# Pharmacy Expansion Analysis: Riyadh Market Entry

## Executive Summary

**Top recommendation:** `24.735048294067383,46.664703369140625` (lat: 24.735048, lng: 46.664703)

**Score:** 50.28 / 100.0 (50.3%)

**Key justifications:**
- **Traffic** — score 18.8 (weight 25.0)
- **Demographics** — score 18.2 (weight 30.0)
- **Complementary** — score 5.0 (weight 10.0)
- **Healthcare** — score 4.5 (weight 20.0)
- **Competitive** — score 3.7 (weight 15.0)

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

---

## Methodology & Visualizations

**Methodology summary:**
- Input: scoring JSON where each criterion overall_score is expected to be scaled to its weight.
- Aggregation: total score = sum of criterion overall scores.
- Ranking: by total score.

**Visualizations produced:**
- Interactive candidates map: maps/candidates_map.html
- Demographic heatmap (residential density): maps/demographics_heatmap.html
- Charts: charts/ (stacked comparison, traffic, candidate breakdowns)

**Why this candidate is best**
The top candidate `24.735048294067383,46.664703369140625` combines high scores in traffic, demographics, complementary. Strong traffic and demographic scores indicate both footfall and market fit.

**Limitations & next steps**
- Missing or "N/A" detail values were treated as neutral (not contributing).
- For Phase 2: add dynamic weight controls, isochrone-based catchments, and automated competitor ingestion.
