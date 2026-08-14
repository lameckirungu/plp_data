# Week 7 — Safety Command Center Dashboard & Crisis Communication

---

## Data Source

Built against **`safety_incidents_kenya.csv`** — 445 real logged HSE incidents across
seven Kenyan depot sites (Mombasa, Nairobi, Kisumu, Wajir, Mandera, Nyeri, Kakamega),
January–June 2026. `safety_incidents.csv` (a generic version with placeholder US
coordinates) is included for reference but not used by the app.

## Setup

```bash
pip install streamlit plotly pandas numpy
streamlit run app_safety_dashboard.py
```

No data generation step needed — the app loads `data/safety_incidents_kenya.csv` directly.

## Files

| File | Part | Description |
|------|------|-------------|
| `app_safety_dashboard.py` | A | The Streamlit dashboard — tested end-to-end with Playwright, zero runtime errors, zero unresolved network dependencies |
| `data/safety_incidents_kenya.csv` | A | The real provided dataset the app loads |
| `data/safety_incidents.csv` | — | Generic reference version (not used by the app) |
| `Week7_Safety_Alert_Lameck.pdf` | B.1 | 1-page urgent safety alert, built from the dashboard's real finding: Mombasa Depot Chemical Exposure incidents show a 66.7% potential-SIF rate |
| `Week7_Roleplay_Lameck.mp4` | B.2 | 
| `capstone_week7_update.md` | C | Capstone progress check |

## Dashboard Features (Part A checklist)

- `@st.cache_data` on data load
- Sidebar filters: Site, Date Range, Incident Type (plus a bonus Department filter)
- 4 KPI metrics with conditional red coloring (Total Incidents, Avg Severity, Critical/Potential-SIF Count, Lost Time Rate)
-  Time-series chart (weekly incident trend)
-  Categorical chart (incidents by type, horizontal bar)
-  Heatmap of incidents by shift × day of week — chosen over a tile-based map because tile/boundary maps depend on a live external connection at render time and fail silently without one (see design note below). Real depot coordinates are still surfaced via a supporting table, satisfying "location data exists."
-  All charts reactive to sidebar filters (single `filtered` dataframe feeds everything)
- `st.warning` alert when potential-SIF incidents exceed an adjustable threshold
-  CSV export of filtered data
-  Inline comments explaining every design decision

## Design Note: Why a Heatmap Instead of a Map

Both Plotly map options were tested — `scatter_map` (tile-based) and
`scatter_geo` (topojson-based) — and both depend on a live request to an external server
at render time. In a restricted or offline network environment, that request fails and the
map renders as a blank canvas with no error message. The heatmap draws entirely from data
already in memory and is guaranteed to render identically in any environment.

## Key Finding Driving Part B

**Mombasa Depot: 12 Chemical Exposure incidents (Jan–Jun 2026), more than double the
average of the other six depots — and 8 of those 12 (66.7%) were flagged with potential
for Serious Injury or Fatality**, a far higher share than the rest of the network. This
finding drives both the safety alert PDF and the role-play script.


