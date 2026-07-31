# Pod Feedback Summary — Week 5 Peer Review
**Author:** Lameck  
**Pod:** KPC Cohort — Oil & Gas  
**Date:** 2026-07-24

---

## My Presentation Summary
I presented a root cause investigation into a throughput shortfall across KPC's four depots using the Mystery_Ops dataset (2,920 records). My key finding: Nairobi depot averages 721 bbl/shift vs ~982 bbl for peers, driven by a maintenance flag rate approximately 3× the network average. The maintenance_flag variable correlates with throughput at r = -0.853 — the strongest signal in the entire dataset.

---

## Sceptical Questions Received

### Question 1 — from pod member Aisha
> *"How do you know the maintenance flag is causing the low throughput and not the other way around — maybe low throughput triggers the flag?"*

**How I answered it:**  
Good challenge on causality. The data structure helps here: the maintenance_flag column is set at the start of a shift based on scheduled maintenance status, not in response to throughput readings. So the flag precedes the throughput measurement in the operational workflow — the direction of causality is maintenance flag → degraded throughput, not the reverse. Additionally, the 368 bbl penalty is consistent across all depots and all months, ruling out a Nairobi-specific data artefact.

**How I improved my argument:**  
I added a cross-depot validation: the maintenance penalty is nearly identical in Mombasa, Kisumu, and Eldoret (where flag rates are low), confirming the relationship is real and not a Nairobi-specific anomaly.

---

### Question 2 — from pod member Brian
> *"Couldn't the February collapse just be seasonal — lower demand in Q1 leading to reduced operations?"*

**How I answered it:**  
The correlation analysis rules this out directly. The demand_index variable shows r < 0.1 with throughput, meaning external demand is not a meaningful driver. More critically, the other three depots show no decline in February or any subsequent month despite operating in the same seasonal environment — if seasonality were the cause, all four depots would be affected equally.

**How I improved my argument:**  
I added the side-by-side monthly comparison chart (Chart 3) as the opening visual, making the depot isolation visible in the first 10 seconds of the presentation rather than revealed at the end.

---

## What I Would Do Differently
I would open with Chart 6 (the maintenance flag rate bar chart) rather than the time series — it delivers the "Nairobi is the problem" and "maintenance is the cause" messages simultaneously in a single chart, which is more efficient for a time-pressured Director audience.

