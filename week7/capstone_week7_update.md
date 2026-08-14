# Capstone Week 7 Progress Update

**Team:** NULL_TERMINATORS

**Project:** Predictive Maintenance for KPC Pipeline Pump Infrastructure

---

## 1. Did you start building your Capstone dashboard?

Yes. This week's `app_safety_dashboard.py` assignment was built directly against the
provided `safety_incidents_kenya.csv` dataset — 445 real logged HSE incidents across seven
Kenyan depot sites (Mombasa, Nairobi, Kisumu, Wajir, Mandera, Nyeri, Kakamega), January to
June 2026. This gives the team a working first dashboard iteration with a real HSE schema
to extend in Week 8, rather than a placeholder built on synthetic data.

## 2. What library are you using (Streamlit / Plotly Dash)?

**Streamlit**, with **Plotly Express** for all charts (time-series line, horizontal bar,
and a shift/day heatmap). Streamlit was chosen over Dash for faster iteration speed — the
`@st.cache_data` decorator and reactive script-rerun model let us prototype and adjust
filters quickly without writing explicit callback functions, which matters given the
compressed weekly timeline.

## 3. What is one challenge you faced in visualizing your specific Capstone data?

The geographic map was the real obstacle this week. Our first version used Plotly's
tile-based map (`scatter_map`), which looked correct in local testing but silently
rendered as a blank canvas when we tested it in a more restricted network environment —
the map depends on live requests to an external tile server at render time, and when that
request fails, nothing displays and no error is raised. Switching to a vector-boundary map
(`scatter_geo`) didn't solve it either — that approach also fetches boundary data from an
external CDN. We resolved this by replacing the map with a shift-by-day-of-week heatmap
(explicitly permitted as an alternative in the assignment brief) built entirely from data
already in memory, with no network dependency at all, and moved the real depot coordinates
into a supporting table instead. The broader lesson — verify a visualization renders
correctly in a network-restricted environment before assuming it works everywhere — is one
we'll carry into the capstone's own dashboard, especially if it's ever deployed somewhere
without guaranteed internet access.

## Capstone data?

We'll extend this dashboard's structure to the capstone's actual pump-failure data, reusing the same filter/KPI/chart architecture, and begin integrating depot-level logistics context per the Week 8 curriculum focus.
