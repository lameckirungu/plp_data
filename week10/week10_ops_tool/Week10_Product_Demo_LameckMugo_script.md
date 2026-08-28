# Week10 Product Demo — Lameck Mugo

**Final video filename:** `Week10_Product_Demo_LameckMugo.mp4`  
**Target duration:** 3:00  
**Recording:** screen-share the running app at 125–150% browser zoom and keep the mouse
movement deliberate.

## 0:00–0:25 — Hook

“A maintenance team may receive hundreds of vibration, temperature, pressure, and motor
readings, but the real question is simple: which pump needs attention first? Reviewing
those signals manually in a spreadsheet is slow and inconsistent, and a risky combination
can be missed. I built PumpGuard Ops to turn telemetry into a prioritized maintenance
decision queue.”

**On screen:** title, synthetic-data notice, and telemetry-source control.

## 0:25–1:15 — Fleet overview

“The bundled demonstration contains recent readings for 24 synthetic pumps across four
depots. The model scores each pump’s latest observation for failure risk within seven
days. At a glance, I can see the number of Critical and Watch assets and the depot with
the highest average risk. The dashed line is the selected intervention threshold. I can
filter by depot or risk band and immediately focus the maintenance queue.”

**On screen:** scroll through KPIs and charts; select `Critical` and `Watch` in the sidebar.

## 1:15–1:55 — Actionable evidence

“The queue ranks the pumps instead of only showing a chart. Each result includes a
probability, risk band, review timeframe, and the model signals pushing risk upward. I’ll
open one Critical pump. Here I can compare its current vibration and temperature with the
six-reading rolling signals. These contributions explain the model’s reasoning; they do
not claim physical causality, so an engineer remains the decision-maker.”

**On screen:** open Asset detail, select the top-ranked pump, point to the score, action,
drivers, and telemetry graph.

## 1:55–2:20 — Upload and export

“The app is not limited to the bundled example. An analyst can download the CSV template
and upload new telemetry. PumpGuard validates the schema, dates, values, and duplicates
before scoring. After review, the filtered action queue can be downloaded as CSV for the
maintenance-planning workflow.”

**On screen:** show Upload CSV, template button, then return to the demo and show export.

## 2:20–2:42 — Value

“For this 24-pump demonstration, the full prioritization workflow takes under two minutes,
compared with an estimated 30 minutes of manual spreadsheet review. That is an
illustrative estimate, not yet a measured KPC baseline. The deeper value is consistent
triage: engineers spend their time investigating the right assets instead of sorting rows.”

## 2:42–3:00 — Call to action

“An organization should pilot PumpGuard Ops with real maintenance history, measure time
saved and false alarms, then calibrate the threshold with engineers before production.
The tool is local, Dockerized, cloud-ready, and contains no hardcoded secrets. The code,
tests, methodology, and AI prompt log are available in my GitHub repository. Let’s turn
sensor data into earlier, evidence-based maintenance action.”
