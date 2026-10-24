# GlycoTwin Phase 0: Data Quality Audit Report

## 1. Executive Summary

This data-quality audit examines the **HUPA-UCM Diabetes Dataset** to verify its integrity, sampling consistency, missingness, and event prevalence prior to machine learning development.

### Key Metrics
- **Total Validated Participants**: 25 individuals diagnosed with Type 1 Diabetes (`HUPA0001P` – `HUPA0028P`).
- **Total Gridded Records**: **309,392 rows**.
- **Sampling Frequency**: **100.0% exact 5-minute spacing** (300 seconds between successive measurements).
- **Temporal Gaps > 5 Minutes**: **0 gaps** across all 25 files.
- **Missing Values (NaNs)**: **0.00%** across all 8 columns in all 25 files.
- **Duplicate Rows**: **0 duplicate rows** across the dataset.
- **Duplicate Timestamps**: **0 duplicate timestamps** within any participant.

---

## 2. File Schema & Data Types

| Column Name | Inferred Dtype | Storage Dtype | Null Count (%) | Zero Count (%) | Plausible Value Range |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time` | ISO-8601 String | `datetime64[ns]` | 0 (0.00%) | 0 (0.00%) | 2018-06-13 to 2020-01-25 |
| `glucose` | Continuous Float | `float64` | 0 (0.00%) | 0 (0.00%) | 40.0 to 400.0 mg/dL |
| `calories` | Continuous Float | `float64` | 0 (0.00%) | 7,200 (2.33%) | 0.0 to 35.0 kcal / 5-min |
| `heart_rate` | Continuous Float | `float64` | 0 (0.00%) | 0 (0.00%) | 45.0 to 185.0 bpm |
| `steps` | Discrete Float | `float64` | 0 (0.00%) | 219,350 (70.90%) | 0 to 800 steps / 5-min |
| `basal_rate` | Continuous Float | `float64` | 0 (0.00%) | 115,451 (37.32%) | 0.0 to 0.40 U / 5-min |
| `bolus_volume_delivered` | Discrete Float | `float64` | 0 (0.00%) | 305,797 (98.84%) | 0.0 to 15.0 U |
| `carb_input` | Discrete Float | `float64` | 0 (0.00%) | 306,746 (99.14%) | 0.0 to 150.0 grams |

---

## 3. Safe Sample Records

Below is a safe sample extract showing the first 3 rows of `HUPA0001P.csv` to confirm the structure without exposing sensitive participant data:

```
time;glucose;calories;heart_rate;steps;basal_rate;bolus_volume_delivered;carb_input
2018-06-13T18:40:00;332.0;6.359500050544739;82.32283464566929;34.0;0.0916666666666666;0.0;0.0
2018-06-13T18:45:00;326.0;7.72799998521805;83.74015748031496;0.0;0.0916666666666666;0.0;0.0
2018-06-13T18:50:00;330.0;4.749500036239624;80.5251798561151;0.0;0.0916666666666666;0.0;0.0
```

---

## 4. Participant-Level Quality & Coverage

| Participant ID | Total Rows | Duration (Days) | Mean Glucose (mg/dL) | Hypo (<70) % | In-Range (70-180) % | Hyper (>180) % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `HUPA0001P` | 4,096 | 14.2 | 181.4 | 1.44% | 51.56% | 47.00% |
| `HUPA0002P` | 3,181 | 11.0 | 113.5 | 23.92% | 63.85% | 12.23% |
| `HUPA0003P` | 3,770 | 13.1 | 143.3 | 7.03% | 68.97% | 24.01% |
| `HUPA0004P` | 3,184 | 11.1 | 180.4 | 9.74% | 46.17% | 44.10% |
| `HUPA0005P` | 3,858 | 13.4 | 147.7 | 3.01% | 76.54% | 20.45% |
| `HUPA0006P` | 2,290 | 7.9 | 165.2 | 8.65% | 58.56% | 32.79% |
| `HUPA0007P` | 3,857 | 13.4 | 173.2 | 8.87% | 53.75% | 37.39% |
| `HUPA0009P` | 3,812 | 13.2 | 193.7 | 0.00% | 46.69% | 53.31% |
| `HUPA0010P` | 2,976 | 10.3 | 135.9 | 8.33% | 71.91% | 19.76% |
| `HUPA0011P` | 3,839 | 13.3 | 159.1 | 2.71% | 65.51% | 31.78% |
| `HUPA0014P` | 3,829 | 13.3 | 188.1 | 4.02% | 48.05% | 47.92% |
| `HUPA0015P` | 3,792 | 13.2 | 163.5 | 4.17% | 63.13% | 32.70% |
| `HUPA0016P` | 3,835 | 13.3 | 150.2 | 15.12% | 59.84% | 25.03% |
| `HUPA0017P` | 3,599 | 12.5 | 200.8 | 2.39% | 46.10% | 51.51% |
| `HUPA0018P` | 3,895 | 13.5 | 143.7 | 17.61% | 60.10% | 22.28% |
| `HUPA0019P` | 3,711 | 12.9 | 162.9 | 2.67% | 67.88% | 29.45% |
| `HUPA0020P` | 2,862 | 9.9 | 194.3 | 3.56% | 45.49% | 50.94% |
| `HUPA0021P` | 2,343 | 8.1 | 137.3 | 4.74% | 76.10% | 19.16% |
| `HUPA0022P` | 4,023 | 14.0 | 112.6 | 15.39% | 73.13% | 11.48% |
| `HUPA0023P` | 3,919 | 13.6 | 133.1 | 4.34% | 79.54% | 16.13% |
| `HUPA0024P` | 2,902 | 10.1 | 166.9 | 7.79% | 56.65% | 35.56% |
| `HUPA0025P` | 4,006 | 13.9 | 113.8 | 13.43% | 77.06% | 9.51% |
| `HUPA0026P` | 40,605 | 141.0 | 163.0 | 7.68% | 58.07% | 34.25% |
| `HUPA0027P` | 165,306 | 574.2 | 130.8 | 6.44% | 72.82% | 20.74% |
| `HUPA0028P` | 25,902 | 90.1 | 128.4 | 3.12% | 76.24% | 20.64% |

---

## 5. Candidate Prediction Target & Overlapping Windows Analysis

### Horizon Definition
- Current time step: $t$
- Forward window: 30 minutes ($t+5\text{ min}$ to $t+30\text{ min}$, corresponding to $k \in \{1, 2, 3, 4, 5, 6\}$)
- Label formulation: $Y_t = \mathbb{I}\left(\min_{k=1..6} G_{t+k} < 70\text{ mg/dL}\right)$

### Overlapping Windows & Serial Correlation
Because predictions are made at every 5-minute time step, successive prediction windows overlap by $5 \times 5 = 25$ minutes:
- Windows $t$ and $t+1$ share 5 forward evaluation steps.
- **Implication**: Observations are serially correlated. Naive random row-splitting would cause severe data leakage between train and test splits.
- **Evaluation Requirement**: Must use **participant-level grouping (GroupKFold)** or strictly chronological forward splitting where the test set is sequestered to a later unbroken time window.

### Prevalence Statistics
- **Total Eligible Windows**: **309,242** (excluding the final 6 windows per participant file).
- **Positive 30-min Hypo Risk Windows**: **27,729** (average participant prevalence: **9.76%**).
- **Discrete Hypoglycemia Onset Events** (drop below 70 mg/dL starting from normoglycemia $G_t \ge 70$): **8,761 events** (prevalence among normoglycemic windows: **3.06%**).

---

## 6. Audit Conclusion & Feasibility Verdict

The dataset exhibits exceptional data quality:
1. Complete 5-minute temporal regularity with zero missing intervals.
2. Clean multimodal alignment across CGM, insulin delivery, and activity sensors.
3. Sufficient volume (309k rows, 27k positive windows, 8.7k onset events) to robustly evaluate population and personalised models.
