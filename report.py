#!/usr/bin/env python3
"""
Pharmacy Site Selection - Static Markdown Report Generator
Single-file script. Drop-in: paste & run.

Features changed per request:
- No pandas or Dataframes anywhere (pure Python lists/dicts)
- Colorful, styled, eye-catching markdown (uses small inline HTML/CSS)
- Wherever lat/lng is missing or not useful, we prefer `place name` from scores JSON
- Before each site analysis we include a Google Maps link (by lat,lng if present; otherwise by place name)
- Always produce PNG "snapshots" for maps so images render in the markdown even without headless browsers.
- Audit files are saved as JSON (no CSVs / no DataFrame outputs)

Usage:
    python3 pharmacy_report_generator.py --scores results.json --outdir report_output --top-n 10 --current-loc "24.7,46.6" --embed-snapshots

Dependencies:
    - matplotlib (for charts + simple map snapshots)
    - folium (optional: saves interactive html maps)

This script attempts to be "paste & run". It writes a 3-page markdown report with embedded images.

"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
import math
import statistics

import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster, HeatMap

# -----------------------------
# Config (weights)
# -----------------------------
CRITERIA = ["traffic", "demographics", "competitive", "healthcare", "complementary"]
CRITERION_WEIGHTS: Dict[str, float] = {
    "traffic": 25.0,
    "demographics": 30.0,
    "competitive": 15.0,
    "healthcare": 20.0,
    "complementary": 10.0
}
MAX_TOTAL = sum(CRITERION_WEIGHTS.values())

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# -----------------------------
# Utility helpers (no pandas)
# -----------------------------

def ensure_dirs(outdir: str):
    for sub in ['charts', 'maps', 'data']:
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)


def load_scores(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def to_float_safe(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if s == '' or s.lower() in ('n/a', 'na', 'null'):
            return None
        return float(s)
    except Exception:
        return None


def normalize_detail_values(details: dict) -> dict:
    out = {}
    for k, v in (details or {}).items():
        key = k.strip()
        out[key] = to_float_safe(v)
    return out

# -----------------------------
# Build internal data structure (list of site dicts) + validations
# -----------------------------

def build_sites_and_audit(scores: dict) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    sites: List[Dict[str, Any]] = []

    for key, val in scores.items():
        lat = to_float_safe(val.get('lat'))
        lng = to_float_safe(val.get('lng'))
        place_name = val.get('place name') or val.get('place_name') or key
        s = val.get('scores', {}) or {}
        site = {'id': key, 'place_name': place_name, 'lat': lat, 'lng': lng, 'scores_raw': {}, 'details': {}, 'total_score': 0.0, 'total_pct': 0.0}

        total_weighted = 0.0
        for crit in CRITERIA:
            crit_obj = s.get(crit, {}) or {}
            raw_overall = to_float_safe(crit_obj.get('overall_score'))
            if raw_overall is None:
                raw_overall_val = None
            else:
                raw_overall_val = float(raw_overall)
                if raw_overall_val < 0:
                    warnings.append(f"{key}: {crit} overall_score negative ({raw_overall_val})")
                if raw_overall_val > CRITERION_WEIGHTS[crit] + 1e-6:
                    warnings.append(f"{key}: {crit} overall_score ({raw_overall_val}) exceeds criterion weight ({CRITERION_WEIGHTS[crit]})")

            weighted = raw_overall_val if raw_overall_val is not None else 0.0
            site['scores_raw'][crit] = raw_overall_val
            site[f'{crit}_score'] = weighted
            total_weighted += weighted

            details = normalize_detail_values(crit_obj.get('details', {}))
            site['details'][crit] = details
            if details:
                for dk, dv in details.items():
                    if dv is None:
                        continue
                    if dv < 0 or dv > 100:
                        warnings.append(f"{key}: {crit} detail '{dk}' out of 0-100 range ({dv})")

        site['total_score'] = total_weighted
        site['total_pct'] = (total_weighted / MAX_TOTAL) * 100.0 if MAX_TOTAL > 0 else 0.0

        if site['lat'] is None or site['lng'] is None:
            warnings.append(f"{key}: missing or invalid lat/lng; using place name where practical")

        sites.append(site)

    return sites, warnings

# -----------------------------
# Charting functions (matplotlib) - operate on sites list
# -----------------------------

def plot_top_n_stacked(sites: List[Dict[str, Any]], top_n: int, outpath: str):
    top = sorted(sites, key=lambda r: r['total_score'], reverse=True)[:top_n]
    labels = [f"{i+1}. {s['place_name']}" for i, s in enumerate(top)]
    comps = [c + '_score' for c in CRITERIA]
    data = []
    for c in CRITERIA:
        data.append([s.get(f'{c}_score', 0.0) or 0.0 for s in top])

    fig, ax = plt.subplots(figsize=(max(8, top_n * 0.6), 6))
    bottoms = [0.0] * len(top)
    for i in range(len(data)):
        ax.bar(labels, data[i], bottom=bottoms, label=CRITERIA[i].capitalize())
        bottoms = [bottoms[j] + data[i][j] for j in range(len(bottoms))]
    ax.set_title(f"Top {top_n} Locations - Component Scores")
    ax.set_ylabel("Weighted score (points)")
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


def plot_traffic_flow(sites: List[Dict[str, Any]], outpath: str):
    top = sorted(sites, key=lambda r: r['total_score'], reverse=True)[:10]
    # try to find any detail column referring to 'Daily' or 'Vehicle' or 'speed'
    veh_values = []
    speed_values = []
    ids = [s['place_name'] for s in top]
    for s in top:
        # search details across criteria
        found_veh = None
        found_speed = None
        for crit in CRITERIA:
            for dk, dv in s['details'].get(crit, {}).items():
                k = dk.lower()
                if ('daily' in k and 'vehicle' in k) or ('vehicle' in k and 'count' in k) or ('daily vehicle' in k):
                    found_veh = dv
                if 'average' in k and ('speed' in k or 'viechle' in k or 'vehicle' in k):
                    found_speed = dv
        veh_values.append(found_veh if found_veh is not None else 0.0)
        speed_values.append(found_speed if found_speed is not None else None)

    fig, ax = plt.subplots(figsize=(10, 4))
    if any(v for v in veh_values):
        ax.bar(ids, [v or 0.0 for v in veh_values])
        ax.set_ylabel('Daily Vehicle Count')
        ax.set_title('Traffic - Daily Vehicle Count (top 10)')
    elif any(v for v in speed_values if v is not None):
        ax.bar(ids, [v or 0.0 for v in speed_values])
        ax.set_ylabel('Average Vehicle Speed')
        ax.set_title('Traffic - Average Vehicle Speed (top 10)')
    else:
        ax.bar(ids, [s.get('traffic_score', 0.0) or 0.0 for s in top])
        ax.set_ylabel('Traffic Score (points)')
        ax.set_title('Traffic - Traffic Score (top 10)')
    ax.set_xticklabels(ids, rotation=45, ha='right', fontsize=8)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


def plot_scoring_breakdown(site: Dict[str, Any], outpath: str):
    comps = [site.get(f'{c}_score', 0.0) or 0.0 for c in CRITERIA]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([c.capitalize() for c in CRITERIA], comps)
    ax.set_ylabel('Weighted score (points)')
    ax.set_title(f"Scoring breakdown: {site.get('place_name')}")
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

# -----------------------------
# Map snapshot helpers: create simple PNG scatter maps so markdown will show images even without headless browsers
# -----------------------------

def create_simple_map_png(sites: List[Dict[str, Any]], out_png: str, title: str = 'Candidates Map'):
    # center by mean of present coords
    xs = [s['lng'] for s in sites if s['lng'] is not None]
    ys = [s['lat'] for s in sites if s['lat'] is not None]
    if not xs or not ys:
        # fallback: simple plot of index
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No coordinates available for map snapshot', ha='center', va='center')
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out_png, dpi=150)
        plt.close(fig)
        return

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    marginx = (maxx - minx) * 0.15 if (maxx - minx) > 0 else 0.01
    marginy = (maxy - miny) * 0.15 if (maxy - miny) > 0 else 0.01

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(title)
    for s in sites:
        if s['lat'] is None or s['lng'] is None:
            continue
        size = 50 * (max(0.1, s.get('total_pct', 0.0) / 100.0)) + 20
        ax.scatter(s['lng'], s['lat'], s=size)
        label = s.get('place_name') or s['id']
        ax.text(s['lng'], s['lat'], '\n' + label, fontsize=6)

    ax.set_xlim(minx - marginx, maxx + marginx)
    ax.set_ylim(miny - marginy, maxy + marginy)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

# -----------------------------
# Folium interactive maps still produced (HTML); saved in maps/ but snapshots will be PNGs created above
# -----------------------------

def create_interactive_map_html(sites: List[Dict[str, Any]], top_n: int, out_html: str):
    valid = [s for s in sites if s['lat'] is not None and s['lng'] is not None]
    if valid:
        center = [statistics.mean([s['lat'] for s in valid]), statistics.mean([s['lng'] for s in valid])]
    else:
        center = [24.7136, 46.6753]

    m = folium.Map(location=center, zoom_start=12, control_scale=True)
    mc = MarkerCluster()
    for s in sites:
        try:
            popup_html = f"<b>{s.get('place_name') or s['id']}</b><br><i>Total: {float(s.get('total_score',0.0)):.2f} ({float(s.get('total_pct',0.0)):.1f}%)</i><br>"
            crits = [(c, float(s.get(f'{c}_score', 0.0) or 0.0)) for c in CRITERIA]
            crits = sorted(crits, key=lambda x: x[1], reverse=True)[:3]
            popup_html += "<b>Top contributions:</b><br>"
            for c, v in crits:
                popup_html += f"{c.capitalize()}: {v:.2f}<br>"
            popup_html += "<b>Top details:</b><br>"
            for c in CRITERIA:
                details = s['details'].get(c, {}) or {}
                best_detail = None
                best_val = -1
                for dk, dv in details.items():
                    if dv is None:
                        continue
                    # weighted approximate
                    weighted = (dv / 100.0) * CRITERION_WEIGHTS[c]
                    if weighted > best_val:
                        best_val = weighted
                        best_detail = dk
                if best_detail:
                    popup_html += f"{c.capitalize()}: {best_detail} ({best_val:.2f} pts)<br>"

            if s['lat'] is not None and s['lng'] is not None:
                marker = folium.CircleMarker(location=(float(s['lat']), float(s['lng'])), radius=4 + (float(s.get('total_pct',0.0))/10 if s.get('total_pct') else 0), popup=popup_html)
                mc.add_child(marker)
        except Exception:
            continue
    m.add_child(mc)

    top = sorted(sites, key=lambda r: r['total_score'], reverse=True)[:top_n]
    for s in top:
        if s['lat'] is not None and s['lng'] is not None:
            folium.Marker(location=(float(s['lat']), float(s['lng'])), popup=f"<b>TOP</b><br>{s.get('place_name') or s['id']}<br>Score: {float(s['total_score']):.2f}", icon=folium.Icon(color='red', icon='star')).add_to(m)

    m.save(out_html)

# -----------------------------
# Audit files (JSON-based)
# -----------------------------

def write_audit_jsons(sites: List[Dict[str, Any]], outdir: str) -> Dict[str, str]:
    out = {}
    full = os.path.join(outdir, 'data', 'candidates_processed.json')
    with open(full, 'w', encoding='utf-8') as fh:
        json.dump(sites, fh, ensure_ascii=False, indent=2)
    out['candidates_processed'] = full

    # flattened details json
    rows = []
    for s in sites:
        base = {'id': s['id'], 'place_name': s.get('place_name'), 'lat': s.get('lat'), 'lng': s.get('lng'), 'total_score': s.get('total_score'), 'total_pct': s.get('total_pct')}
        for c in CRITERIA:
            details = s['details'].get(c, {}) or {}
            if details:
                for dk, dv in details.items():
                    rows.append({**base, 'criterion': c, 'detail_name': dk, 'detail_raw': dv, 'detail_weighted': (dv / 100.0) * CRITERION_WEIGHTS[c] if dv is not None else None})
            else:
                rows.append({**base, 'criterion': c, 'detail_name': None, 'detail_raw': None, 'detail_weighted': None})
    details_path = os.path.join(outdir, 'data', 'candidates_details_flattened.json')
    with open(details_path, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    out['details_flattened'] = details_path
    return out

# -----------------------------
# Markdown generation - colorful and includes google maps links and image snapshots
# -----------------------------

def google_maps_link_for_site(s: Dict[str, Any]) -> str:
    if s['lat'] is not None and s['lng'] is not None:
        return f"https://www.google.com/maps/search/?api=1&query={s['lat']},{s['lng']}"
    else:
        q = s.get('place_name') or s['id']
        from urllib.parse import quote_plus
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def embed_image_or_placeholder(filepath: Optional[str]) -> str:
    if filepath and os.path.exists(filepath):
        return f"![{os.path.basename(filepath)}]({filepath})"
    else:
        return "*No image available*"


def generate_markdown_and_manifest(
    sites: List[Dict[str, Any]],
    outdir: str,
    out_md: str,
    top_n: int,
    map_html: str,
    map_png: Optional[str],
    heat_html: str,
    heat_png: Optional[str],
    charts: Dict[str,str],
    competition_html: Optional[str],
    competition_png: Optional[str],
    current_loc: Optional[Tuple[float,float]],
    warnings: List[str],
    manifest_path: str
):
    top = sorted(sites, key=lambda r: r['total_score'], reverse=True)[:top_n]
    best = top[0] if top else None

    audit_paths = write_audit_jsons(sites, outdir)

    md_path = os.path.join(outdir, out_md)
    with open(md_path, 'w', encoding='utf-8') as md:
        # Add some simple CSS for visual appeal (many markdown renderers accept inline HTML/CSS)
        md.write('<style>\n')
        md.write('  .card{background:#f9f9ff;border-radius:12px;padding:12px;margin:8px 0;box-shadow:0 2px 6px rgba(0,0,0,0.08)}\n')
        md.write('  .pill{display:inline-block;background:#efefff;color:#222;padding:6px 10px;border-radius:999px;font-weight:600;margin-right:6px}\n')
        md.write('  h1{color:#2b5dff}\n')
        md.write('  .muted{color:#666;font-size:0.95em}\n')
        md.write('</style>\n\n')

        md.write('# Pharmacy Expansion Analysis: Riyadh Market Entry \n\n')
        md.write(f"<div class=\"card\"><h2 style=\"margin:0\">Executive Summary</h2>\n")
        md.write(f"<p class=\"muted\">Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)</p>\n")
        if best:
            display_name = best.get('place_name') or best['id']
            md.write(f"<p style=\"font-size:1.1em\"><span class=\"pill\">Top recommendation</span> <strong>{display_name}</strong></p>\n")
            md.write(f"<p><strong>Score:</strong> {best['total_score']:.2f} / {MAX_TOTAL} ({best['total_pct']:.1f}%)</p>\n")

            # key contributions
            md.write('<p><strong>Key criterion contributions:</strong></p>\n')
            crit_scores = {c: best.get(f'{c}_score', 0.0) for c in CRITERIA}
            sorted_crit = sorted(crit_scores.items(), key=lambda x: x[1], reverse=True)
            md.write('<ul>\n')
            for c, sc in sorted_crit:
                md.write(f"<li><strong>{c.capitalize()}</strong> — {sc:.2f} pts (weight {CRITERION_WEIGHTS[c]})</li>\n")
            md.write('</ul>\n')

        md.write('</div>\n\n')

        # Comparison to current location
        if current_loc is not None and sites:
            # find nearest candidate to current loc (euclidean approx)
            def dist2(a,b):
                return (a[0]-b[0])**2 + (a[1]-b[1])**2
            candidates_with_coords = [s for s in sites if s['lat'] is not None and s['lng'] is not None]
            if candidates_with_coords:
                idx = min(range(len(candidates_with_coords)), key=lambda i: dist2((candidates_with_coords[i]['lat'], candidates_with_coords[i]['lng']), current_loc))
                curr = candidates_with_coords[idx]
                md.write('## Comparison to Current Location\n\n')
                md.write(f"Nearest candidate to your current location: **{curr.get('place_name') or curr['id']}** (lat: {curr.get('lat')}, lng: {curr.get('lng')})\n\n")
                md.write('**Improvement by criterion (vs current location)**\n\n')
                md.write('| Criterion | Current (pts) | Top candidate (pts) | Absolute delta | % delta |\n')
                md.write('|---|---:|---:|---:|---:|\n')
                for c in CRITERIA:
                    t = best.get(f'{c}_score', 0.0) if best else 0.0
                    v = curr.get(f'{c}_score', 0.0)
                    abs_delta = t - v
                    if abs(v) < 1e-9:
                        pct_str = 'N/A (baseline 0)'
                    else:
                        pct_delta = (abs_delta / v) * 100.0
                        pct_str = f"{pct_delta:.1f}%"
                    md.write(f"| {c.capitalize()} | {v:.2f} | {t:.2f} | {abs_delta:+.2f} | {pct_str} |\n")
                md.write('\n')

        md.write('---\n\n')

        # Page 2 Detailed Site Analysis
        md.write('## Detailed Site Analysis\n\n')
        md.write(f"Top {top_n} candidates summary:\n\n")
        md.write('| Rank | id | Location | Total Score | Total % |\n')
        md.write('|---:|---|---|---:|---:|\n')
        for i, r in enumerate(top):
            loc_display = ''
            if r['lat'] is None or r['lng'] is None:
                loc_display = f"{r.get('place_name') or r['id']}"
            else:
                loc_display = f"{r['lat']:.6f}, {r['lng']:.6f}"
            md.write(f"| {i+1} | `{r['id']}` | {loc_display} | {r['total_score']:.2f} | {r['total_pct']:.1f}% |\n")
        md.write('\n')

        # Per-site detail breakdown (top candidates) with Google Maps links and maps snapshots
        md.write('### Per-site detail breakdown (top candidates)\n\n')
        for i, r in enumerate(top):
            md.write(f"#### {i+1}. `{r['id']}` — <strong>{r.get('place_name') or r['id']}</strong>\n\n")
            gmap = google_maps_link_for_site(r)
            md.write(f"**Google Maps link:** {gmap}  \n\n")

            # If lat/lng missing show place name
            if r['lat'] is None or r['lng'] is None:
                md.write(f"**Location:** {r.get('place_name') or 'N/A'}\n\n")
            else:
                md.write(f"**Coordinates:** {r['lat']:.6f}, {r['lng']:.6f}\n\n")

            md.write('| Evaluation Criterion | Sub-factor | Raw Score (0–100) | Weighted Points |\n')
            md.write('|---|---|---:|---:|\n')
            for c in CRITERIA:
                details = r['details'].get(c, {}) or {}
                if details:
                    num_sub = len(details)
                    # we'll display each detail and compute weighted = (raw/100)*(criterion weight)
                    criterion_total_points = 0.0
                    for dk, dv in details.items():
                        raw = dv
                        weighted = (raw / 100.0) * CRITERION_WEIGHTS[c] if raw is not None else None
                        if weighted is not None:
                            criterion_total_points += weighted
                        md.write(f"| {c.capitalize()} | {dk} | {'' if raw is None else f'{raw:.1f}'} | {'' if weighted is None else f'{weighted:.2f}'} |\n")
                    md.write(f"| **{c.capitalize()} (Total)** |  |  | **{criterion_total_points:.2f}** |\n")
                else:
                    overall_used = r.get(f'{c}_score', 0.0)
                    md.write(f"| {c.capitalize()} | No sub-factor data |  | **{overall_used:.2f}** |\n")
            md.write('\n')

            # include a snapshot of the best breakdown per site
            per_chart = charts.get('per_site_{}_breakdown'.format(i+1))
            if per_chart and os.path.exists(per_chart):
                md.write(embed_image_or_placeholder(per_chart) + '\n\n')
            md.write('\n')

        md.write('### Best candidate scoring breakdown\n\n')
        if charts.get('best_breakdown'):
            md.write(embed_image_or_placeholder(charts['best_breakdown']) + '\n\n')
        md.write('\n')
        md.write('### Top candidates component comparison\n\n')
        if charts.get('top_stacked'):
            md.write(embed_image_or_placeholder(charts['top_stacked']) + '\n\n')
        md.write('### Traffic flow visualization\n\n')
        if charts.get('traffic'):
            md.write(embed_image_or_placeholder(charts['traffic']) + '\n\n')
        md.write('---\n\n')

        # Page 3 Methodology & Visualizations
        md.write('## Methodology & Visualizations\n\n')
        md.write('### Visualizations produced\n\n')

        md.write('#### Interactive map: Top-ranked locations with scoring overlays\n\n')
        if map_png and os.path.exists(map_png):
            md.write(embed_image_or_placeholder(map_png) + '  \n')
            md.write(f"**Interactive (HTML):** {map_html}  \n\n")
        else:
            md.write(f"**Interactive (HTML):** {map_html}  \n\n")

        md.write('#### Demographic heatmap: Population density and target demographics\n\n')
        if heat_png and os.path.exists(heat_png):
            md.write(embed_image_or_placeholder(heat_png) + '  \n')
            md.write(f"**Interactive (HTML):** {heat_html}  \n\n")
        else:
            md.write(f"**Interactive (HTML):** {heat_html}  \n\n")

        md.write('#### Competition analysis map: Existing pharmacies with coverage areas\n\n')
        if competition_html:
            if competition_png and os.path.exists(competition_png):
                md.write(embed_image_or_placeholder(competition_png) + '  \n')
                md.write(f"**Interactive (HTML):** {competition_html}  \n\n")
            else:
                md.write(f"**Interactive (HTML):** {competition_html}  \n\n")
        else:
            md.write('*(no competition file provided / no loc_data found)*\n\n')

        md.write('### Methodology summary:\n')
        md.write('- Input: scoring JSON where each criterion overall_score is expected to be in the criterion weight units.\n')
        md.write('- Details: each detail metric expected 0-100. Weighted contribution computed as (detail/100)*criterion_weight for auditability.\n')
        md.write('- Validation: flags detail values outside 0-100 and criterion overalls > criterion weight. See run_manifest.json for warnings.\n')
        md.write('- Aggregation: total_score = sum of criterion overall_score (if provided).\n')
        md.write('- Ranking: by total_score (descending).\n\n')

        md.write('### Limitations & next steps\n')
        md.write('- Missing or "N/A" detail values were treated as neutral (no contribution).\n')
        md.write('- Phase 2: interactive weight controls, isochrone catchments, automated competitor ingestion, sensitivity analysis.\n\n')

        if warnings:
            md.write('---\n\n')
            md.write('## Data quality warnings (auto-generated)\n\n')
            for w in warnings:
                md.write(f"- {w}\n")
            md.write('\n')

        md.write('---\n\n')
        md.write('## Audit files\n\n')
        md.write(f"- Candidates processed JSON: {audit_paths['candidates_processed']}\n")
        md.write(f"- Flattened details JSON: {audit_paths['details_flattened']}\n")

    manifest = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'report_md': md_path,
        'charts': charts,
        'map_html': map_html,
        'map_png': map_png,
        'heat_html': heat_html,
        'heat_png': heat_png,
        'competition_html': competition_html,
        'competition_png': competition_png,
        'audit_files': audit_paths,
        'warnings': warnings
    }
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)
    logging.info(f"Run manifest saved to {manifest_path}")
    logging.info(f"Markdown report saved to {md_path}")

# -----------------------------
# CLI main
# -----------------------------

def main():
    p = argparse.ArgumentParser(description='Generate PM-ready pharmacy site selection report (no DataFrame)')
    p.add_argument('--scores', default='results.json')
    p.add_argument('--outdir', default='report_output')
    p.add_argument('--output', default='report.md')
    p.add_argument('--top-n', type=int, default=10)
    p.add_argument('--competition', default=None)
    p.add_argument('--current-loc', default=None)
    p.add_argument('--embed-snapshots', action='store_true', help='Produce PNG snapshots for maps and include them in report')
    args = p.parse_args()

    scores_path = args.scores
    outdir = args.outdir
    out_md = args.output
    top_n = args.top_n
    competition = args.competition
    current_loc = None
    if args.current_loc:
        try:
            lat_s, lng_s = args.current_loc.split(',')
            current_loc = (float(lat_s.strip()), float(lng_s.strip()))
        except Exception:
            logging.warning("Cannot parse --current-loc; ignoring")
            current_loc = None

    os.makedirs(outdir, exist_ok=True)
    ensure_dirs(outdir)

    if not os.path.exists(scores_path):
        logging.error(f"scores file not found: {scores_path}")
        sys.exit(1)

    scores = load_scores(scores_path)
    sites, warnings = build_sites_and_audit(scores)

    # Save processed JSON and produce charts
    charts = {
        'top_stacked': os.path.join(outdir, 'charts', 'top_stacked.png'),
        'traffic': os.path.join(outdir, 'charts', 'traffic_flow.png'),
        'best_breakdown': os.path.join(outdir, 'charts', 'best_breakdown.png')
    }

    plot_top_n_stacked(sites, top_n, charts['top_stacked'])
    logging.info(f"Saved stacked chart: {charts['top_stacked']}")
    plot_traffic_flow(sites, charts['traffic'])
    logging.info(f"Saved traffic chart: {charts['traffic']}")
    try:
        best_site = sorted(sites, key=lambda r: r['total_score'], reverse=True)[0]
        plot_scoring_breakdown(best_site, charts['best_breakdown'])
        logging.info(f"Saved best breakdown chart: {charts['best_breakdown']}")
    except Exception as e:
        logging.warning("Unable to create best breakdown chart: " + str(e))

    # Create simple PNG snapshots for map & heat
    map_html = os.path.join(outdir, 'maps', 'candidates_map.html')
    create_interactive_map_html(sites, top_n, map_html)
    map_png = os.path.join(outdir, 'maps', 'candidates_map.png')
    create_simple_map_png(sites, map_png, title='Candidates Map')

    # Demographics heatmap: attempt to use any demographics detail as weight
    weight_present = False
    for s in sites:
        for dk, dv in s['details'].get('demographics', {}).items():
            if dv is not None:
                weight_present = True
                break
        if weight_present:
            break

    heat_html = os.path.join(outdir, 'maps', 'demographics_heatmap.html')
    heat_png = os.path.join(outdir, 'maps', 'demographics_heatmap.png')
    if weight_present:
        # save simple map with marker size proportional to first numeric demographic detail found
        for s in sites:
            s['_dem_weight'] = 0.0
            for dk, dv in s['details'].get('demographics', {}).items():
                if dv is not None:
                    s['_dem_weight'] = float(dv)
                    break
        # create folium heat html if coords exist
        try:
            valid = [s for s in sites if s['lat'] is not None and s['lng'] is not None and s.get('_dem_weight', 0.0) > 0]
            if valid:
                # folium heat
                center = [statistics.mean([s['lat'] for s in valid]), statistics.mean([s['lng'] for s in valid])]
                m = folium.Map(location=center, zoom_start=12)
                heat_data = [[s['lat'], s['lng'], s['_dem_weight']] for s in valid]
                HeatMap(heat_data, radius=15, max_zoom=13).add_to(m)
                m.save(heat_html)
            else:
                create_interactive_map_html(sites, top_n, heat_html)
        except Exception:
            create_interactive_map_html(sites, top_n, heat_html)
        # png snapshot
        create_simple_map_png(sites, heat_png, title='Demographics (proxy)')
    else:
        create_interactive_map_html(sites, top_n, heat_html)
        create_simple_map_png(sites, heat_png, title='Demographics (fallback)')

    # Competition map (try to use provided competition JSON or loc_data directory)
    competition_html = None
    competition_png = None
    if competition and os.path.exists(competition):
        competition_html = os.path.join(outdir, 'maps', 'competition_map.html')
        try:
            with open(competition, 'r', encoding='utf-8') as fh:
                comp = json.load(fh)
            # if comp is GeoJSON-like, write to html via folium
            try:
                valid = [s for s in sites if s['lat'] is not None and s['lng'] is not None]
                center = [statistics.mean([s['lat'] for s in valid]), statistics.mean([s['lng'] for s in valid])] if valid else [24.7136,46.6753]
                m = folium.Map(location=center, zoom_start=12)
                folium.GeoJson(comp, name='competition').add_to(m)
                m.save(competition_html)
                competition_png = os.path.join(outdir, 'maps', 'competition_map.png')
                create_simple_map_png(sites, competition_png, title='Competition (overlay)')
            except Exception:
                # fallback: just create interactive map with comp markers if comp is list of {lat,lng}
                create_interactive_map_html(sites, top_n, competition_html)
                competition_png = os.path.join(outdir, 'maps', 'competition_map.png')
                create_simple_map_png(sites, competition_png, title='Competition (fallback)')
        except Exception as e:
            logging.warning('Could not create competition overlay map: ' + str(e))
    else:
        # try to find loc_data directory
        def find_loc_data():
            cwd = os.getcwd()
            candidates = [os.path.join(cwd, 'data', 'loc_data'), os.path.join(cwd, 'loc_data'), os.path.join(cwd, 'report_output','data','loc_data'), os.path.join(cwd,'data')]
            for c in candidates:
                if os.path.isdir(c) and any(fname.lower().endswith('.json') for fname in os.listdir(c)):
                    return c
            for root, dirs, files in os.walk(cwd):
                if 'loc_data' in dirs:
                    loc = os.path.join(root, 'loc_data')
                    if any(fname.lower().endswith('.json') for fname in os.listdir(loc)):
                        return loc
            return None
        loc = find_loc_data()
        if loc:
            try:
                competition_html = os.path.join(outdir, 'maps', 'competition_map.html')
                # create a simple map with circles for files
                pts = []
                for fname in os.listdir(loc):
                    if not fname.lower().endswith('.json'):
                        continue
                    try:
                        with open(os.path.join(loc,fname),'r',encoding='utf-8') as fh:
                            j = json.load(fh)
                        lat = to_float_safe(j.get('lat'))
                        lng = to_float_safe(j.get('lng'))
                        nm = j.get('name') or j.get('site_name') or fname
                        if lat is not None and lng is not None:
                            pts.append({'lat':lat,'lng':lng,'popup':nm})
                    except Exception:
                        continue
                if not pts:
                    raise RuntimeError('no usable loc_data')
                center = [statistics.mean([p['lat'] for p in pts]), statistics.mean([p['lng'] for p in pts])]
                m = folium.Map(location=center, zoom_start=12)
                for p in pts:
                    folium.Circle(location=(p['lat'],p['lng']), radius=500, color='blue', fill=True, fill_opacity=0.1).add_to(m)
                    folium.Marker(location=(p['lat'],p['lng']), popup=str(p['popup']), icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
                m.save(competition_html)
                competition_png = os.path.join(outdir, 'maps', 'competition_map.png')
                create_simple_map_png(sites, competition_png, title='Competition (loc_data)')
            except Exception as e:
                logging.warning('Could not create competition map from loc_data: ' + str(e))
        else:
            logging.info('No competition provided and no loc_data found; skipping competition map')

    # If embed_snapshots flag not provided, still we already created PNGs so they will be embedded.
    manifest_path = os.path.join(outdir, 'run_manifest.json')
    generate_markdown_and_manifest(sites, outdir, out_md, top_n, map_html, map_png, heat_html, heat_png, charts, competition_html, competition_png, current_loc, warnings, manifest_path)
    logging.info('Report generation complete.')

if __name__ == '__main__':
    main()
