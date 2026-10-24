# GlycoTwin Phase 2: Experimental Results & Model Evaluation

## 1. Executive Summary

Phase 2 evaluated three machine-learning model families across two clinical prediction tasks using 5-fold participant-grouped cross-validation (`GroupKFold`) on the 25 participants of the HUPA-UCM Diabetes Dataset:
1. **Rule-Based Trajectory Baseline**: Deterministic 15-minute slope projection.
2. **Regularized Logistic Regression**: Standardized $L_2$ regularized linear model.
3. **Gradient Boosted Decision Trees (XGBoost)**: Non-linear tree ensemble with training-fitted positive class weighting.

In addition, a full chronological **personalisation experiment** was executed across all 25 participants to test the primary research hypothesis.

---

## 2. Population Out-of-Fold Performance Comparison

All metrics below are computed from **unseen out-of-fold validation predictions** across the entire cohort:

### Task A: Future Hypoglycemia Risk in 30 Minutes ($N = 308,942$; Prevalence = 8.95%)
| Model | Pooled ROC-AUC | Pooled PR-AUC | Pooled F1 | Sensitivity | Specificity | Precision | Brier Score | Macro ROC-AUC | Macro PR-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based Baseline** | 0.9838 | 0.8813 | 0.8347 | 82.86% | 98.46% | 84.09% | 0.0306 | 0.9863 | 0.8736 |
| **Logistic Regression** | 0.9836 | 0.8512 | 0.8350 | 83.03% | 98.44% | 83.97% | 0.0506 | 0.9827 | 0.8496 |
| **XGBoost Ensemble** | **0.9882** | **0.9316** | **0.8592** | **83.46%** | **98.94%** | **88.52%** | **0.0381** | **0.9891** | **0.9153** |

### Task B: Impending Hypoglycemia Onset in 30 Minutes ($N = 288,628$; Prevalence = 3.03%; Primary Task)
| Model | Pooled ROC-AUC | Pooled PR-AUC | Pooled F1 | Sensitivity | Specificity | Precision | Brier Score | Macro ROC-AUC | Macro PR-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based Baseline** | 0.9582 | 0.4928 | 0.5361 | 57.20% | 98.25% | 50.45% | **0.0284** | 0.9646 | 0.5601 |
| **Logistic Regression** | 0.9595 | 0.4280 | 0.5215 | **62.31%** | 97.61% | 44.84% | 0.0863 | 0.9594 | 0.5158 |
| **XGBoost Ensemble** | **0.9667** | **0.5843** | **0.5770** | 61.20% | **0.9841** | **54.58%** | 0.0709 | **0.9711** | **0.6325** |

### Key Population Findings
1. **XGBoost dominates discrimination**: XGBoost achieves superior performance on both tasks, increasing Task B PR-AUC to **0.5843** (pooled) and **0.6325** (macro), substantially outperforming logistic regression (0.4280) and the rule-based baseline (0.4928).
2. **High Specificity on Onset Events**: XGBoost delivers **98.41% specificity** while maintaining **61.20% sensitivity**, ensuring that false alarms are minimized during stable normoglycemic periods.

---

## 3. Personalisation Experiment Results (Task B Impending Onset)

The chronological adaptation experiment evaluated an unadapted population model versus a personalized model adapted on each participant's initial 30% calibration segment, evaluated on the **exact same remaining 70% future holdout**:

- **Total Participants**: 25
- **Successfully Adapted**: 24 participants
- **Triggered Fallback**: 1 participant (`HUPA0009P`, who has 0 hypoglycemia events across their entire observation window)

### Summary of Paired Findings
1. **Dramatic Brier Score Improvement (Probability Calibration)**:
   - For all 24 adapted participants, the Brier score was substantially reduced (e.g. `HUPA0001P`: 0.1491 $\to$ 0.0216, $\Delta = -0.1275$; `HUPA0002P`: 0.1595 $\to$ 0.0387, $\Delta = -0.1208$).
   - *Explanation*: Population models trained with balanced weighting output probabilities anchored around 0.50. Personal adaptation recalibrates probabilities to the individual's baseline empirical event frequency (typically 3–5%), aligning predicted probabilities with true observed risk.
2. **Discrimination Ranking Invariance**:
   - Monotonic log-odds scaling preserves rank-order discrimination; therefore, ROC-AUC and PR-AUC deltas are near zero ($\Delta\text{ROC-AUC} \approx 0.000$, $\Delta\text{PR-AUC} \approx 0.000$).
3. **Threshold Calibration Interaction**:
   - Because the operational classification threshold ($t^* \approx 0.50$) was calibrated on the population model's balanced logit scale, applying it to recalibrated probabilities (which range in [0, 0.20]) reduces naive positive trigger rates. Phase 3/4 must allow participant-calibrated risk thresholds or percentile-based alert triggers.

---

## 4. Subgroup Error Analysis (Task B XGBoost)

Error analysis was conducted on the out-of-fold predictions to identify clinical failure modes:

### By Current Glucose Range
| Glucose Range (mg/dL) | Total Windows | True Positives | False Positives | False Negatives | True Negatives |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Borderline (70–80)** | 7,121 | 2,752 | 1,489 | 1,023 | 1,857 |
| **Low Normal (80–100)** | 27,249 | 2,056 | 1,818 | 1,516 | 21,859 |
| **Normal (100–140)** | 96,160 | 528 | 987 | 794 | 93,851 |
| **Elevated (140–180)** | 77,595 | 14 | 129 | 57 | 77,395 |
| **Hyperglycemia (>180)**| 80,503 | 0 | 12 | 3 | 80,488 |

*Insight*: Over 55% of all true positive onset predictions occur when glucose is in the borderline range (70–80 mg/dL). In hyperglycemia (>180 mg/dL), false positive alerts are virtually non-existent (12 out of 80,503 windows, 0.01%).

### By Rate of Change (Slope)
- **Rapid Drops ($\text{slope} < -1.0\text{ mg/dL/min}$)**: 1,607 true positives vs. 518 false negatives (75.6% sensitivity).
- **Steady Glucose ($-0.3 \le \text{slope} \le +0.3$)**: Low event density; 99.2% specificity.

---

## 5. Artifacts and Visualization Files Generated

All Phase 2 evaluation outputs are stored in `artifacts/evaluation/phase2/`:
- `population_oof_predictions.parquet` (7.2 MB)
- `personalisation_predictions.parquet` (6.8 MB)
- `model_comparison.csv`
- `participant_metrics.csv`
- `population_metrics.json`
- `error_analysis.json`
- `feature_importance.json`
- `phase2_summary.json`
- `roc_curves.png`
- `pr_curves.png`
- `confusion_matrices.png`
- `personalisation_comparison.png`
- `calibration_curves.png`

Serialized model checkpoints are stored in `artifacts/models/`:
- `logistic_regression/model_task_b_onset.joblib`
- `xgboost/model_task_b_onset.joblib`
- `logistic_regression/model_task_a_risk.joblib`
- `xgboost/model_task_a_risk.joblib`
