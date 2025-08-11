# Pharmacy Expansion Analysis: Riyadh Market Entry

_Report generated: 2025-08-11 12:16:26Z_

### **Deliverables**

**1. Automated Report Generation**

- **3-page markdown report** with:
  - Page 1: Executive summary and top recommendations
  - Page 2: Detailed site analysis with scoring breakdown
  - Page 3: Maps, charts, and methodology overview

- Embedded visualizations (maps, charts, tables)
- Professional formatting with consistent styling

---

## Executive Summary

**Top recommendation:** `24.735048294067383,46.664703369140625` (lat: 24.735048, lng: 46.664703)

**Score:** 50.28 / 100.0 (50.3%)

**Key justifications:**
- **Traffic** — weighted contribution 18.75 (weight 25.0)
- **Demographics** — weighted contribution 18.24 (weight 30.0)
- **Complementary** — weighted contribution 5.05 (weight 10.0)
- **Healthcare** — weighted contribution 4.55 (weight 20.0)
- **Competitive** — weighted contribution 3.69 (weight 15.0)

---

## Detailed Site Analysis

Top 10 candidates summary:

| Rank | id | lat | lng | Total Score | Total % |
|---:|---|---:|---:|---:|---:|
| 1 | `24.735048294067383,46.664703369140625` | 24.735048 | 46.664703 | 50.28 | 50.3% |
| 2 | `24.7136,46.6753` | 24.713600 | 46.675300 | 49.33 | 49.3% |
| 3 | `24.70555877685547,46.78419876098633` | 24.705559 | 46.784199 | 48.70 | 48.7% |
| 4 | `24.765399932861328,46.803592681884766` | 24.765400 | 46.803593 | 47.72 | 47.7% |
| 5 | `24.861194610595703,46.62861633300781` | 24.861195 | 46.628616 | 43.99 | 44.0% |
| 6 | `24.751220703125,46.57400131225586` | 24.751221 | 46.574001 | 43.81 | 43.8% |
| 7 | `24.836605072021484,46.65959167480469` | 24.836605 | 46.659592 | 43.07 | 43.1% |
| 8 | `24.73484992980957,46.792118072509766` | 24.734850 | 46.792118 | 42.09 | 42.1% |
| 9 | `24.613752365112305,46.602638244628906` | 24.613752 | 46.602638 | 42.06 | 42.1% |
| 10 | `24.52115821838379,46.52830505371094` | 24.521158 | 46.528305 | 40.76 | 40.8% |

### Best candidate scoring breakdown

![Best breakdown](charts/best_breakdown.png)

### Top candidates component comparison

![Top stacked](charts/top_stacked.png)

### Traffic flow visualization

![Traffic flow](charts/traffic_flow.png)

---

## Methodology & Visualizations

### **Visualizations Required**

#### Interactive map: Top-ranked locations with scoring overlays

**File produced:** [candidates_map.html](report_output\maps\candidates_map.html)

---

#### Scoring comparison chart: Top 10 locations ranked by criteria

![top_stacked.png](report_output\charts\top_stacked.png)  
**File produced:** `charts/top_stacked.png`

---

#### Demographic heatmap: Population density and target demographics

**File produced:** [demographics_heatmap.html](report_output\maps\demographics_heatmap.html)

---

#### Competition analysis map: Existing pharmacies with coverage areas

**File produced:** *(no competition file provided)*

---

#### Traffic flow visualization: Vehicle count data representation

![traffic_flow.png](report_output\charts\traffic_flow.png)  
**File produced:** `charts/traffic_flow.png`

---

### Methodology summary:
- Input: scoring JSON where each criterion overall_score is expected to be in the criterion weight units.
- Details: each detail metric is expected 0-100. We calculate detail weighted contribution as (detail/100) * criterion_weight for auditability.
- Aggregation: total_score = sum of criterion overall_score (weighted contributions).
- Ranking: by total_score (descending).

### Why this candidate is best
The top candidate `24.735048294067383,46.664703369140625` combines highest weighted contributions in traffic, demographics, complementary.

### Limitations & next steps
- Missing or "N/A" detail values were treated as neutral (not contributing).
- Phase 2 planned features: dynamic weight controls (UI), isochrone-based catchments, competitor auto-ingest, interactive sensitivity analysis.

