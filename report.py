#!/usr/bin/env python3
"""
pharmacy_report_final.py

Generates a 3-page markdown pharmacy site selection report (static images only).
- No pandas. Uses lists/dicts + numpy + matplotlib.
- Produces required charts and static maps locally (no external map API).
- Uses `place name` when lat/lng are missing; provides Google Maps links.
- Output: report_output/<output>.md, charts in report_output/charts/, maps in report_output/maps/
"""
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from typing import List
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point

# Set Arabic-friendly font globally for matplotlib
# plt.rcParams['font.family'] = 'DejaVu Sans'  # supports Arabic

# -----------------------------
# Charts (required only)
# -----------------------------


import arabic_reshaper
from bidi.algorithm import get_display
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
import math
from urllib.parse import quote_plus

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
from Config import Config
# -----------------------------
# Config
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
# Utilities
# -----------------------------
def ensure_dirs(outdir: str):
    for sub in ['charts', 'maps', 'data']:
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)


def load_scores(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def to_num(x: Any) -> float:
    try:
        if isinstance(x, str) and x.strip().upper() in ("N/A", "NA", ""):
            return float('nan')
        return float(x)
    except Exception:
        return float('nan')


def pick_display_name(record: dict) -> Optional[str]:
    for k in ('place name', 'place_name', 'place', 'name'):
        v = record.get(k)
        if v:
            return str(v)
    return None


# -----------------------------
# Processing
# -----------------------------
def process_sites(scores: dict) -> Tuple[List[dict], List[str]]:
    warnings: List[str] = []
    sites: List[dict] = []
    for key, rec in scores.items():
        place = pick_display_name(rec)
        lat = rec.get('lat')
        lng = rec.get('lng')

        site = {
            'id': key,
            'display_name': place or key,
            'raw_place': place,
            'lat': None,
            'lng': None,
            'scores': {},
            'details': {}
        }

        try:
            site['lat'] = float(lat) if lat is not None else None
        except Exception:
            site['lat'] = None
        try:
            site['lng'] = float(lng) if lng is not None else None
        except Exception:
            site['lng'] = None

        total = 0.0
        s = rec.get('scores', {}) or {}
        for crit in CRITERIA:
            crit_obj = s.get(crit, {}) or {}
            raw_overall = to_num(crit_obj.get('overall_score', float('nan')))
            if not math.isnan(raw_overall):
                if raw_overall < 0:
                    warnings.append(f"{key}: {crit} overall_score negative ({raw_overall})")
                if raw_overall > CRITERION_WEIGHTS[crit] + 1e-6:
                    warnings.append(f"{key}: {crit} overall_score ({raw_overall}) exceeds criterion weight ({CRITERION_WEIGHTS[crit]})")
            weighted = raw_overall if not math.isnan(raw_overall) else float('nan')
            site['scores'][f'{crit}_raw_overall'] = raw_overall
            site['scores'][f'{crit}_score'] = weighted if not math.isnan(weighted) else 0.0
            if not math.isnan(weighted):
                total += weighted

            details = {}
            for dk, dv in (crit_obj.get('details') or {}).items():
                val = to_num(dv)
                safe_key = dk.strip()
                details[f'{crit}__{safe_key}'] = val
                if not math.isnan(val):
                    if val < 0 or val > 100:
                        warnings.append(f"{key}: {crit} detail '{dk}' out of 0-100 range ({val})")
                    details[f'{crit}__{safe_key}_weighted'] = (val / 100.0) * CRITERION_WEIGHTS[crit]
                else:
                    details[f'{crit}__{safe_key}_weighted'] = float('nan')
            if not details:
                details[f'{crit}__MISSING'] = float('nan')
                details[f'{crit}__MISSING_weighted'] = float('nan')

            site['details'].update(details)

        site['total_score'] = total
        site['total_pct'] = (total / MAX_TOTAL) * 100.0 if MAX_TOTAL > 0 else float('nan')

        if site['lat'] is None or site['lng'] is None:
            if not site['raw_place']:
                warnings.append(f"{key}: missing lat/lng and no place name provided")

        sites.append(site)

    if not sites:
        warnings.append('No sites parsed from scores file.')

    return sites, warnings



# You still need a font that supports Arabic
from matplotlib import rcParams
rcParams['font.family'] = 'Arial'  # Make sure this font is installed
rcParams['axes.unicode_minus'] = False

def plot_top_stacked(sites: list, top_n: int, outpath: str):
    top = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]
    if not top:
        return
    
    # Reshape Arabic labels for proper rendering
    labels = [get_display(arabic_reshaper.reshape(s['display_name'])) for s in top]

    comps = [f"{c}_score" for c in CRITERIA]
    data = np.array([[s['scores'].get(c, 0) for s in top] for c in comps])

    fig, ax = plt.subplots(figsize=(max(12, top_n * 1.2), 8), dpi=200)
    bottoms = np.zeros(len(labels))
    cmap = cm.get_cmap('tab20')

    for i in range(data.shape[0]):
        ax.bar(labels, data[i], bottom=bottoms, label=CRITERIA[i].capitalize(), color=cmap(i))
        bottoms += data[i]

    ax.set_title(f"Top {top_n} Locations — Component scores (stacked)", fontsize=14)
    ax.set_ylabel('Weighted points', fontsize=12)
    ax.legend(loc='upper right', fontsize='small')

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)

    plt.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.9)
    fig.savefig(outpath)
    plt.close(fig)


def plot_traffic(sites: List[dict], outpath: str):
    top = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:10]
    if not top:
        return
    
    x = [get_display(arabic_reshaper.reshape(s['display_name'])) for s in top]
    veh_vals = []
    speed_vals = []
    for s in top:
        found_veh = float('nan')
        found_speed = float('nan')
        for k, v in s['details'].items():
            kl = k.lower()
            if 'daily' in kl and ('vehicle' in kl or 'vehicles' in kl or 'viechle' in kl or 'veh' in kl):
                found_veh = v
            if 'average' in kl and ('speed' in kl or 'vehicle' in kl or 'viechle' in kl):
                found_speed = v
        veh_vals.append(0.0 if math.isnan(found_veh) else float(found_veh))
        speed_vals.append(0.0 if math.isnan(found_speed) else float(found_speed))

    # Increase the figure size and DPI
    fig, ax = plt.subplots(figsize=(15, 8), dpi=200)

    if any(v > 0 for v in veh_vals):
        ax.bar(x, veh_vals)
        ax.set_ylabel('Daily Vehicle Count')
        ax.set_title('Traffic — Daily vehicle count (top 10)')
    elif any(v > 0 for v in speed_vals):
        ax.bar(x, speed_vals)
        ax.set_ylabel('Average vehicle speed')
        ax.set_title('Traffic — Average speed (top 10) km')
    else:
        ax.bar(x, [s.get('scores', {}).get('traffic_score', 0) for s in top])
        ax.set_ylabel('Traffic score (points)')
        ax.set_title('Traffic — Traffic score (top 10)')

    ax.set_xticklabels(x, rotation=45, ha='right', fontsize=10)
    
    # Manually adjust the subplots to create more space for the labels
    plt.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.9)
    
    fig.savefig(outpath)
    plt.close(fig)


def plot_breakdown(site: dict, outpath: str):
    vals = [site.get('scores', {}).get(f'{c}_score', 0.0) for c in CRITERIA]
    fig, ax = plt.subplots(figsize=(15, 8), dpi=150)
    ax.bar([c.capitalize() for c in CRITERIA], vals)
    ax.set_ylabel('Weighted points')
    ax.set_title(f"Scoring breakdown — best site")
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)

# -----------------------------
# Static maps (matplotlib + contextily)
# -----------------------------
def create_static_map_png(sites: List[dict], outpath: str, top_n: int = 10, extent: tuple = None):
    fig_size = (10, 7.5)
    dpi = 150
    pad = 0.1

    coords = [(s['lat'], s['lng']) for s in sites if s['lat'] is not None and s['lng'] is not None]
    fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)

    if not coords:
        ax.text(0.5, 0.5, 'No coordinates available to render map', ha='center', va='center')
        ax.axis('off')
        ax.set_title("Top recommended candidates", pad=3)
        fig.savefig(outpath, pad_inches=pad)
        plt.close(fig)
        return

    gdf = gpd.GeoDataFrame(sites, geometry=[Point(s['lng'], s['lat']) for s in sites if s['lat'] is not None])
    gdf = gdf.set_crs(epsg=4326).to_crs(epsg=3857)

    gdf.plot(ax=ax, color='blue', alpha=0.6, markersize=50, label='Candidates')
    top_sites = sorted([s for s in sites if s['lat'] and s['lng']], key=lambda x: x.get('total_score',0), reverse=True)[:top_n]
    for i, t in enumerate(top_sites, start=1):
        x, y = gpd.GeoSeries([Point(t['lng'], t['lat'])], crs=4326).to_crs(epsg=3857).geometry[0].coords[0]
        ax.scatter(x, y, s=120, color='red', marker='*')
        ax.text(x, y, f" {i}", fontsize=12, weight='bold', color='black')

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_axis_off()
    ax.set_title("Top recommended candidates", pad=3)

    if extent is None:
        extent = ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1]
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    fig.savefig(outpath, pad_inches=pad)
    plt.close(fig)
    return extent


# ----------------------------------------------------------------------------------------------------
def create_demographic_heatmap_png(sites: List[dict], outpath: str, demographic_key_prefix='demographics__', extent=None):
    fig_size = (10, 7.5)
    dpi = 150
    pad = 0.1

    xs, ys, vals = [], [], []
    # ... your existing code to populate xs, ys, vals ...
    gdf = gpd.GeoDataFrame({'value': vals}, geometry=[Point(lon, lat) for lon, lat in zip(xs, ys)], crs=4326).to_crs(epsg=3857)
    norm = Normalize(vmin=np.nanmin(vals), vmax=np.nanmax(vals))

    fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)
    gdf.plot(ax=ax, column='value', cmap='hot', markersize=80, alpha=0.8, legend=True, norm=norm)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_title("Population density", pad=3)
    ax.set_axis_off()

    if extent is not None:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

    fig.savefig(outpath, pad_inches=pad)
    plt.close(fig)


# -----------------------------
# Markdown generation
# -----------------------------
def relpath_for_md(target: Optional[str], md_path: str) -> Optional[str]:
    if not target:
        return None
    if not os.path.exists(target):
        return None
    md_dir = os.path.dirname(md_path) or os.getcwd()
    try:
        return os.path.relpath(target, start=md_dir)
    except Exception:
        return target


def google_maps_link(s: dict) -> str:
    if s.get('lat') is not None and s.get('lng') is not None:
        return f"https://www.google.com/maps/search/?api=1&query={s['lat']},{s['lng']}"
    q = s.get('raw_place') or s.get('display_name') or s['id']
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def generate_markdown(sites: List[dict], outdir: str, out_md: str, top_n: int,
                      charts: Dict[str, str], map_png: Optional[str], heat_png: Optional[str],
                      manifest_path: str , num_of_sites : int):
    top_sites = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]
    best = top_sites[0] if top_sites else None
    md_path = os.path.join(outdir, out_md)

    # compute relative paths
    charts_rel = {k: relpath_for_md(v, md_path) for k, v in charts.items()}
    map_png_rel = relpath_for_md(map_png, md_path)
    heat_png_rel = relpath_for_md(heat_png, md_path)

    with open(md_path, 'w', encoding='utf-8') as md:
        # md.write('<style>\n')
        # md.write('body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial;line-height:1.4;padding:10px}\n')
        # md.write('.hero{background:linear-gradient(90deg,#0f172a,#0ea5e9);color:white;padding:18px;border-radius:10px}\n')
        # md.write('.card{background:white;padding:12px;border-left:6px solid #0ea5e9;margin:12px 0;border-radius:8px;box-shadow:0 6px 18px rgba(2,6,23,0.08)}\n')
        # md.write('table{border-collapse:collapse;width:100%}th,td{border:1px solid #e6eef6;padding:8px}th{background:#f1f8ff}\n')
        # md.write('</style>\n\n')

        md.write('<div class="hero">\n')
        md.write('<h1>🧭 Pharmacy Expansion Analysis — Riyadh</h1>\n')
        md.write('<p class="muted">Automated report — multi-criteria scoring across traffic, demographics, competition, healthcare, and complementary businesses.</p>\n')
        md.write('</div>\n\n')

        md.write('## Executive Summary\n\n')
        if best:
            md.write(f"**Top recommendation:** **{best['display_name']}** — overall score {best['total_score']:.2f} / {MAX_TOTAL} ({best['total_pct']:.1f}%).\n\n")
        md.write(f'This report evaluates candidate pharmacy sites using a multi-criteria scoring approach (traffic, demographics, competition, healthcare proximity, and complementary businesses). {num_of_sites} locations has been analyzed, The goal is to produce an ordered shortlist of locations for further due diligence and site visits.\n\n')

        md.write('---\n\n')
        md.write('## Methodology (summary)\n\n')
        md.write('- **Input:** a JSON `scores` file where each candidate includes `lat`, `lng` (optional), `place name` (preferred), and per-criterion `overall_score` and `details`.\n')
        md.write('- **Scoring:** criterion overall_score is expected in criterion units; details (0–100) are used to compute audit-weighted contributions.\n')
        md.write('- **Aggregation:** `total_score` = sum of criterion overall_score. `total_pct` = total_score / max_total * 100.\n')
        md.write('- **Ranking:** top locations by `total_score` descending.\n\n')

        md.write('---\n\n')
        md.write('## Detailed Site Analysis\n\n')
        md.write(f"Top {top_n} candidates summary:\n\n")
        md.write('| Rank | Site Name | Coordinates | Total Score | Total % |\n')
        md.write('|---:|---|---|---:|---:|\n')
        for i, s in enumerate(top_sites, start=1):
            coords = f"{s['lat']:.6f}, {s['lng']:.6f}" if (s['lat'] is not None and s['lng'] is not None) else (s.get('raw_place') or 'N/A')
            md.write(f"| {i} | `{s['display_name']}` | {coords} | {s['total_score']:.2f} | {s['total_pct']:.1f}% |\n")
        md.write('\n')

        # per-site details
        for i, s in enumerate(top_sites, start=1):
            md.write(f"### {i}. {s['display_name']} (total score {s['total_score']:.2f})\n\n")
            md.write(f"**Open in Google Maps:** <{google_maps_link(s)}>\n\n")
            coords_text = f"lat {s['lat']:.6f}, lng {s['lng']:.6f}" if (s['lat'] is not None and s['lng'] is not None) else f"place: {s.get('raw_place') or 'N/A'}"
            md.write(f"**Location:** {coords_text}\n\n")

            md.write('| Evaluation Criterion | Sub-factor | Raw (0–100) | Weighted pts |\n')
            md.write('|---|---|---:|---:|\n')
            for c in CRITERIA:
                dkeys = [k for k in s['details'].keys() if k.startswith(f"{c}__") and not k.endswith('_weighted')]
                if dkeys and any(not math.isnan(s['details'].get(k, float('nan'))) for k in dkeys):
                    sub_weight = CRITERION_WEIGHTS[c] / max(1, len(dkeys))
                    crit_total = 0.0
                    for dk in dkeys:
                        raw = s['details'].get(dk, float('nan'))
                        weighted = (raw / 100.0) * sub_weight if not math.isnan(raw) else float('nan')
                        crit_total += 0.0 if math.isnan(weighted) else weighted
                        sub_name = dk.replace(f"{c}__", '').replace('_', ' ')
                        md.write(f"| {c.capitalize()} | {sub_name} | {'' if math.isnan(raw) else f'{raw:.1f}'} | {'' if math.isnan(weighted) else f'{weighted:.2f}'} |\n")
                    md.write(f"| **{c.capitalize()} (total)** |  |  | **{crit_total:.2f}** |\n")
                else:
                    overall = s.get('scores', {}).get(f'{c}_score', 0.0)
                    md.write(f"| {c.capitalize()} | No sub-factor data |  | **{overall:.2f}** |\n")
            md.write('\n')

            # include best breakdown for the top site only (if available)
            if i == 1 and charts.get('best_breakdown') and os.path.exists(charts['best_breakdown']):
                rel = relpath_for_md(charts['best_breakdown'], md_path).replace("\\", "/")
                if rel:
                    md.write(f"![Best breakdown]({rel})\n\n")

        md.write('---\n\n')
        md.write('### Charts & Visualizations\n\n')
        if charts.get('top_stacked') and os.path.exists(charts['top_stacked']):
            rel = relpath_for_md(charts['top_stacked'], md_path).replace("\\", "/")
            if rel:
                md.write(f"**Top candidates comparison:** ![{os.path.basename(rel)}]({rel})\n\n")
        if charts.get('traffic') and os.path.exists(charts['traffic']):
            rel = relpath_for_md(charts['traffic'], md_path).replace("\\", "/")
            if rel:
                md.write(f"**Traffic flow:** ![{os.path.basename(rel)}]({rel})\n\n")

        md.write('---\n\n')
        md.write('### Maps\n\n')
        if map_png_rel:
            md.write("**Candidates map:**\n\n")
            md.write(f"![{os.path.basename(map_png_rel)}]({map_png_rel.replace('\\', '/')})\n\n")
        else:
            md.write("**Candidates map:** *not available*\n\n")

        if heat_png_rel:
           md.write("**Demographic heatmap:**\n\n") 
           md.write(f"![{os.path.basename(heat_png_rel)}]({heat_png_rel.replace('\\', '/')})\n\n")
        else:
            md.write("**Demographic heatmap:** *not available or no demographic details found*\n\n")

        md.write('---\n\n')
        md.write('## Limitations & next steps\n\n')
        md.write('- Missing detail values were treated as neutral (non-contributing).\n')
        md.write('- For richer maps (tiles, basemaps), consider adding context tiles or running an HTML map generator.\n\n')

        md.write('---\n\n')
        md.write('## Run manifest & artifacts\n\n')
        md.write(f"- Manifest: `{os.path.basename(manifest_path)}`\n")
        md.write(f"- Processed candidates JSON: `data/candidates_processed.json`\n\n")

    logging.info(f"Saved markdown: {md_path}")


# -----------------------------
# CLI main
# -----------------------------
def main():
    p = argparse.ArgumentParser(description='Pharmacy site selection - static report generator')
    p.add_argument('--scores', default=Config.scoring_file_dir)
    p.add_argument('--outdir', default='report_output')
    p.add_argument('--output', default='report.md')
    p.add_argument('--top-n', type=int, default=10)
    args = p.parse_args()

    scores_path = args.scores
    outdir = args.outdir
    out_md = args.output
    top_n = args.top_n

    if not os.path.exists(scores_path):
        logging.error(f"Scores file not found: {scores_path}")
        sys.exit(1)

    os.makedirs(outdir, exist_ok=True)
    ensure_dirs(outdir)

    scores = load_scores(scores_path)
    sites, warnings = process_sites(scores)

    # processed JSON
    proc_path = os.path.join(outdir, 'data', 'candidates_processed.json')
    with open(proc_path, 'w', encoding='utf-8') as pf:
        json.dump(sites, pf, indent=2, ensure_ascii=False)
    logging.info(f"Saved processed JSON: {proc_path}")

    # charts and maps paths
    charts = {
        'top_stacked': os.path.join(outdir, 'charts', 'top_stacked.png'),
        'traffic': os.path.join(outdir, 'charts', 'traffic_flow.png'),
        'best_breakdown': os.path.join(outdir, 'charts', 'best_breakdown.png')
    }
    map_png = os.path.join(outdir, 'maps', 'candidates_map.png')
    heat_png = os.path.join(outdir, 'maps', 'demographics_heatmap.png')
    manifest_path = os.path.join(outdir, 'run_manifest.json')

    # generate charts
    try:
        plot_top_stacked(sites, top_n, charts['top_stacked'])
        logging.info(f"Saved top stacked chart: {charts['top_stacked']}")
    except Exception as e:
        logging.warning(f"plot_top_stacked failed: {e}")
    try:
        plot_traffic(sites, charts['traffic'])
        logging.info(f"Saved traffic chart: {charts['traffic']}")
    except Exception as e:
        logging.warning(f"plot_traffic failed: {e}")
    try:
        best = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[0]
        plot_breakdown(best, charts['best_breakdown'])
        logging.info(f"Saved best breakdown chart: {charts['best_breakdown']}")
    except Exception as e:
        logging.warning(f"plot_breakdown failed: {e}")

    # # maps (static)
    try:
        create_static_map_png(sites, map_png, top_n=top_n)
        logging.info(f"Saved static candidates map: {map_png}")
    except Exception as e:
        logging.warning(f"create_static_map_png failed: {e}")
    try:
        create_demographic_heatmap_png(sites, heat_png)
        logging.info(f"Saved demographic heatmap: {heat_png}")
    except Exception as e:
        logging.warning(f"create_demographic_heatmap_png failed: {e}")

    # manifest
    manifest = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'report_md': os.path.join(outdir, out_md),
        'charts': charts,
        'maps': {'map_png': map_png, 'heat_png': heat_png},
        'warnings': warnings,
        'sites_count': len(sites)
    }
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    # markdown
    num_of_sites = len(sites)
    generate_markdown(sites, outdir, out_md, top_n, charts, map_png, heat_png, manifest_path , num_of_sites)
    logging.info("Report generation complete.")

if __name__ == '__main__':
    print("starting report creation .........")
    main()
