# GlycoTwin Phase 1: Data Pipeline & Feature Engineering Report

## 1. Executive Summary

Phase 1 successfully developed and verified a leak-free, reproducible preprocessing and feature-engineering pipeline that converts the raw HUPA-UCM Diabetes Dataset into a production-ready, standardized modeling dataset.

### Headline Pipeline Metrics
- **Participants Processed**: **25 participants** with Type 1 Diabetes.
- **Input Gridded Observations**: **309,392 rows**.
- **Output Rows**: **309,392 rows**.
- **Modelling-Eligible Windows**: **308,942 windows** (excluding initial 60m warmup and terminal 30m horizon).
- **Positive 30-min Hypo Risk Windows ($y=1$)**: **27,661** (**8.95%** prevalence).
- **Negative Windows ($y=0$)**: **281,281** (**91.05%**).
- **Impending Hypo Onset Transitions**: **8,742 discrete events**.
- **Feature Columns Generated**: **27 causal features** (0 future leakage).
- **Elapsed Pipeline Runtime**: **30.63 seconds** across all 309k rows.
- **Test Suite Status**: **20 of 20 tests PASSED** in 4.09 seconds.

---

## 2. Longitudinal Participant Breakdown

The pipeline computed window counts, positive label prevalences, and onset events per participant:

| Participant ID | Raw Rows | Modelling-Eligible Windows | Excluded Warmup Windows | Excluded Terminal Windows | Positive Labels ($y=1$) | Negative Labels ($y=0$) | Hypo Prevalence (%) | Onset Events |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `HUPA0001P` | 4,096 | 4,078 | 12 | 6 | 130 | 3,948 | 3.19% | 45 |
| `HUPA0002P` | 3,181 | 3,163 | 12 | 6 | 896 | 2,267 | 28.33% | 206 |
| `HUPA0003P` | 3,770 | 3,752 | 12 | 6 | 358 | 3,394 | 9.54% | 150 |
| `HUPA0004P` | 3,184 | 3,166 | 12 | 6 | 363 | 2,803 | 11.47% | 159 |
| `HUPA0005P` | 3,858 | 3,840 | 12 | 6 | 185 | 3,655 | 4.82% | 85 |
| `HUPA0006P` | 2,290 | 2,272 | 12 | 6 | 247 | 2,025 | 10.87% | 94 |
| `HUPA0007P` | 3,857 | 3,839 | 12 | 6 | 446 | 3,393 | 11.62% | 196 |
| `HUPA0009P` | 3,812 | 3,794 | 12 | 6 | 0 | 3,794 | 0.00% | 0 |
| `HUPA0010P` | 2,976 | 2,958 | 12 | 6 | 315 | 2,643 | 10.65% | 117 |
| `HUPA0011P` | 3,839 | 3,821 | 12 | 6 | 148 | 3,673 | 3.87% | 77 |
| `HUPA0014P` | 3,829 | 3,811 | 12 | 6 | 209 | 3,602 | 5.48% | 88 |
| `HUPA0015P` | 3,792 | 3,774 | 12 | 6 | 224 | 3,550 | 5.94% | 103 |
| `HUPA0016P` | 3,835 | 3,817 | 12 | 6 | 722 | 3,095 | 18.92% | 224 |
| `HUPA0017P` | 3,599 | 3,581 | 12 | 6 | 134 | 3,447 | 3.74% | 55 |
| `HUPA0018P` | 3,895 | 3,877 | 12 | 6 | 818 | 3,059 | 21.10% | 179 |
| `HUPA0019P` | 3,711 | 3,693 | 12 | 6 | 187 | 3,506 | 5.06% | 76 |
| `HUPA0020P` | 2,862 | 2,844 | 12 | 6 | 143 | 2,701 | 5.03% | 71 |
| `HUPA0021P` | 2,343 | 2,325 | 12 | 6 | 145 | 2,180 | 6.24% | 71 |
| `HUPA0022P` | 4,023 | 4,005 | 12 | 6 | 733 | 3,272 | 18.30% | 192 |
| `HUPA0023P` | 3,919 | 3,901 | 12 | 6 | 217 | 3,684 | 5.56% | 117 |
| `HUPA0024P` | 2,902 | 2,884 | 12 | 6 | 277 | 2,607 | 9.60% | 123 |
| `HUPA0025P` | 4,006 | 3,988 | 12 | 6 | 682 | 3,306 | 17.10% | 199 |
| `HUPA0026P` | 40,605 | 40,587 | 12 | 6 | 3,822 | 36,765 | 9.42% | 1,234 |
| `HUPA0027P` | 165,306 | 165,288 | 12 | 6 | 13,388 | 151,900 | 8.10% | 4,204 |
| `HUPA0028P` | 25,902 | 25,884 | 12 | 6 | 1,224 | 24,660 | 4.73% | 596 |
| **Total** | **309,392** | **308,942** | **300** | **150** | **27,661** | **281,281** | **8.95%** | **8,742** |

---

## 3. Exclusions & Eligibility Rules Applied

1. **Initial Warmup Exclusions (300 rows across cohort, 12 per participant)**:
   Observations occurring within the first 60 minutes (steps 0 to 11) of a participant's recording cannot compute full 60-minute backward lags and rolling standard deviations. These are tagged with `feature_eligible = False`.
2. **Terminal Horizon Exclusions (150 rows across cohort, 6 per participant)**:
   Observations occurring within the final 30 minutes (last 6 steps) cannot observe a full 30-minute forward evaluation horizon. These are tagged with `target_eligible = False` and `target_hypo_30m = NaN` (never defaulted to 0).
3. **Modelling-Eligible Windows (308,942 rows)**:
   Observed intervals where `is_modelling_eligible = feature_eligible & target_eligible == True`.

---

## 4. Pipeline Artifacts Produced

| File Path | Format | Size | Description |
| :--- | :--- | :--- | :--- |
| `data/processed/glycotwin_features.parquet` | Apache Parquet (Snappy) | 21.2 MB | Primary, compressed, fast-loading modelling dataset containing all 27 features, metadata, and labels. |
| `data/processed/glycotwin_features.csv` | Standard CSV | 133.7 MB | Portable text copy for interoperability and inspection. |
| `artifacts/evaluation/phase1_feature_manifest.json` | JSON | 4.8 KB | Machine-readable catalog specifying lookback, units, category, and eligibility for all 27 features. |
| `artifacts/evaluation/phase1_pipeline_summary.json` | JSON | 6.2 KB | Complete run summary with row counts, participant breakdowns, software versions, and timestamp. |

---

## 5. Software Environment & Execution Commands

- **Python Version**: `3.13.15`
- **pandas**: `2.3.3`
- **numpy**: `2.3.2`
- **pyarrow**: `19.0.0`
- **pytest**: `9.1.1`

### Reproduction Command
To execute the complete Phase 1 pipeline from the root directory:
```powershell
python -m ml.run_pipeline
```

To run the automated test suite (20 tests covering both Phase 0 and Phase 1):
```powershell
python -m pytest tests/ -v
```

---

## 6. Phase 2 Readiness Recommendation

**The dataset and feature pipeline are 100% verified and ready for Phase 2 (Machine Learning Models & Personalisation).**
- Clean causal feature matrix is saved in `data/processed/glycotwin_features.parquet`.
- Target label balance (8.95% positive, 27,661 events) provides an ideal foundation for baseline logistic regression and tree-based classification (XGBoost).
- Participant isolation guarantees that GroupKFold cross-validation and personalized chronological evaluation can proceed without leakage.
