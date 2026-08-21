# Week 9 Capstone Update — Lameck Mugo

## ML component added
This week, the capstone's predictive-maintenance component was implemented as a binary classification workflow for identifying pipeline pumps at risk of failure within a 7-day intervention window. The implementation is aligned with the capstone proposal's operational objective of moving from fixed-interval maintenance toward condition-based maintenance.

## Which ML algorithm did you choose and why?
I selected **XGBoost** as the primary candidate for operational threshold analysis after comparing it with a **Random Forest** using 5-fold stratified cross-validation. Both models are tree-based ensemble methods capable of modelling non-linear relationships among telemetry variables.

XGBoost was particularly useful for this use case because pump failure risk may depend on interactions between vibration, bearing temperature, motor current, pressure deviation, load, pump age, and maintenance state. The final decision was based on the operational metric trade-off rather than accuracy alone.

The capstone's target is at least 80% recall while keeping false alarms below 5%. The final XGBoost operating threshold was therefore selected after threshold analysis rather than automatically using the default probability cutoff of 0.50.

## How did you handle class imbalance?
The target class was intentionally imbalanced because near-failure events are less common than normal operating observations.

Two approaches were used:

- **Random Forest:** `class_weight="balanced"` was applied.
- **XGBoost:** **SMOTE** was applied inside an imbalanced-learn pipeline.

Placing SMOTE inside the cross-validation pipeline is important because oversampling before cross-validation could leak synthetic information from the training process into validation folds and produce overly optimistic results.

Evaluation focused on Precision, Recall, F1-score, ROC-AUC, the Confusion Matrix, and the False Positive Rate. Accuracy was not used as the primary decision metric.

## What insight from Feature Importance analysis surprised you?
The most notable insight was that **vibration was the strongest global SHAP driver**, while **bearing temperature ranked highest in the model's built-in feature-importance measure**. Motor current was also consistently among the leading operational signals.

This difference was useful because it showed that explainability methods can provide complementary views of the same model. Feature importance indicates how useful a variable was to the model's tree splits, while mean absolute SHAP values show how strongly a feature changed individual predictions on average.

Operationally, this suggests that the maintenance team should not monitor a single sensor in isolation. The model is more informative when vibration, thermal stress, and electrical load are interpreted together.

## Current limitations
The primary dataset remains physics-informed synthetic SCADA data because real KPC internal pump and maintenance logs are not publicly available. Therefore, the Week 9 results demonstrate a rigorous ML workflow but do not constitute validated production performance. The next validation step should compare the feature-engineering logic against the AI4I 2020 dataset and, where appropriate, benchmark related degradation modelling against NASA C-MAPSS.

## Week 9 status
- [x] Defined operational classification target
- [x] Checked class imbalance
- [x] Applied class weighting / SMOTE
- [x] Compared Random Forest and XGBoost
- [x] Used 5-fold stratified cross-validation
- [x] Evaluated Precision, Recall, F1, ROC-AUC and confusion matrices
- [x] Added optional K-Means operational segmentation
- [x] Added global feature importance
- [x] Added SHAP global and local explanations
- [x] Documented operational limitations and trust considerations
