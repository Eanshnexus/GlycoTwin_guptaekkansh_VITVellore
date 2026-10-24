# GlycoTwin Data Dictionary: HUPA-UCM Diabetes Dataset

## 1. Provenance & Dataset Classification

- **Dataset**: HUPA-UCM Diabetes Dataset
- **Authors**: Hidalgo et al., *"HUPA-UCM Diabetes Dataset"*, Data in Brief 55 (August 2024): 110559. [DOI: 10.1016/j.dib.2024.110559](https://doi.org/10.1016/j.dib.2024.110559)
- **Licence**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Format**: Semicolon-delimited (`;`) CSV files resampled to regular 5-minute intervals.

---

## 2. Categorization of Data Fields

In accordance with strict clinical data engineering standards, fields are categorized into:
- **Verified Fields**: Directly observed, unit-verified, and validated across all 25 participant records.
- **Inferred Fields**: Derived algorithmically from primary measurements (e.g. rollings, deltas, clinical risk indicators).
- **Unavailable Fields**: Mentioned in general clinical trial literature or raw directories but absent from preprocessed 5-minute grids.
- **Fields with Uncertain Meanings**: Fields where sensor hardware conventions or reporting definitions require explicit documentation.

---

## 3. Verified Fields (Present in 5-Minute Preprocessed Files)

All 25 preprocessed files contain these 8 verified fields with **0.00% missing values (NaNs)**.

| Field Name | Type | Physical Units | Source Device | Missingness | Physical Range & Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time` | ISO-8601 String | Datetime (`YYYY-MM-DDTHH:MM:SS`) | Synchronized Master Clock | 0.00% | Exact timestamp of the 5-minute observation. Spaced at exact 300-second increments with 0 gaps > 5 min. |
| `glucose` | Float | mg/dL | Abbott FreeStyle Libre 2 | 0.00% | Interstitial continuous glucose reading. Range: 40.0 to 400.0 mg/dL. Mean: 155.3 mg/dL. |
| `calories` | Float | kcal / 5 min | Fitbit Wearable Tracker | 0.00% | Estimated calories burned during the 5-minute window. 2.33% zeros during sleep or device removal. |
| `heart_rate`| Float | beats per minute (bpm) | Fitbit Optical PPG | 0.00% | Mean heart rate during the 5-minute window. Range: 45.0 to 185.0 bpm. Mean: 79.4 bpm. |
| `steps` | Float | step count / 5 min | Fitbit Accelerometer | 0.00% | Total steps taken during the 5-minute interval. 70.90% zeros (typical of sedentary, resting, or sleep periods). |
| `basal_rate`| Float | Units / 5 min | Medtronic MiniMed 640G | 0.00% | Basal insulin infused during the interval. 37.32% zeros during pump suspension or non-pump intervals. |
| `bolus_volume_delivered` | Float | Units of rapid-acting insulin | Medtronic MiniMed 640G | 0.00% | Rapid insulin bolus for meals or correction. Discrete pulses (3,595 recorded events). 98.84% zeros. |
| `carb_input`| Float | Grams (g) | Medtronic Bolus Wizard | 0.00% | Patient-entered carbohydrate mass for meal calculation. Discrete events (2,646 recorded meals). 99.14% zeros. |

---

## 4. Inferred Fields (Derived Features & Target Labels)

These fields are constructed in Phase 1 for feature engineering and supervised prediction.

| Field Name | Type | Formula / Derivation | Lookback / Horizon | Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `target_hypo_30m` | Binary (0 / 1) | $\mathbb{I}\left(\min_{k=1..6} G_{t+k} < 70\right)$ | Next 30 minutes (forward 6 steps) | Primary target: Will interstitial glucose fall below 70 mg/dL in the next 30 minutes? |
| `target_hypo_onset_30m` | Binary (0 / 1) | $G_t \ge 70 \land \mathbb{I}\left(\min_{k=1..6} G_{t+k} < 70\right)$ | Next 30 minutes (forward 6 steps) | Impending hypoglycemia event given non-hypoglycemic current status. |
| `glucose_roc_15m` | Float | $(G_t - G_{t-3}) / 15.0$ | Lookback: 15 minutes (past 3 steps) | Rate of change of glucose (mg/dL/min). Indicates steep drops. |
| `glucose_roc_30m` | Float | $(G_t - G_{t-6}) / 30.0$ | Lookback: 30 minutes (past 6 steps) | Medium-term trend of glucose trajectory. |
| `glucose_std_60m` | Float | $\sigma(G_{t-12..t})$ | Lookback: 60 minutes (past 12 steps) | Short-term glucose variability. |
| `time_of_day_sin` | Float | $\sin(2\pi \cdot \text{hour} / 24)$ | Instantaneous | Circadian cyclical time-of-day representation. |
| `time_of_day_cos` | Float | $\cos(2\pi \cdot \text{hour} / 24)$ | Instantaneous | Circadian cyclical time-of-day representation. |
| `recent_bolus_sum_60m` | Float | $\sum_{k=0}^{12} \text{bolus}_{t-k}$ | Lookback: 60 minutes | Cumulative active insulin bolus delivered in the past hour. |
| `recent_carb_sum_60m` | Float | $\sum_{k=0}^{12} \text{carbs}_{t-k}$ | Lookback: 60 minutes | Cumulative carbohydrate intake logged in the past hour. |

---

## 5. Unavailable Fields (Not in 5-Minute Preprocessed Grid)

The following modalities were mentioned in Mendeley dataset descriptions or raw directory subtrees, but are **unavailable** in the 5-minute preprocessed files:

1. **Sleep Stages and Sleep Quality**:
   - *Status*: **Unavailable in preprocessed data**.
   - *Findings*: Daily sleep files (`*_sleep_*_night_summary.csv`) exist in `Raw_Data/{PID}/fitbit/`, but they are discrete daily sleep-session summaries (e.g. `Minutes Light`, `Minutes Deep`, `Efficiency`) that are asynchronous, missing for multiple participants, and not gridded into 5-minute intervals.
   - *Decision*: Excluded from the real-time 5-minute feature vector to preserve data pipeline integrity and avoid synthetic fabrication.
2. **Skin Temperature / Galvanic Skin Response (GSR)**:
   - *Status*: **Unavailable**. Not recorded by Fitbit Charge or FreeStyle Libre.
3. **Meal Composition Beyond Carbohydrates (Fat, Protein, Glycemic Index)**:
   - *Status*: **Unavailable**. Medtronic Bolus Wizard only records total grams of carbohydrate.

---

## 6. Fields with Uncertain Meanings & Clinical Conventions

1. **`basal_rate` Exact Time Denomination**:
   - In insulin pump logs, basal rates are typically programmed as **Units per hour (U/h)** or converted during resampling to **Units per 5-minute interval (U / 5-min)**.
   - Inspection shows values such as `0.09166` (which equals $1.1\text{ U/h} \div 12$). The preprocessed files represent **units delivered per 5-minute interval**.
2. **`glucose` Reading Calibration Delay**:
   - The FreeStyle Libre 2 measures interstitial fluid glucose, which exhibits a physiological lag of 5–10 minutes behind venous/capillary blood glucose. This is acknowledged as a natural property of CGM technology.
3. **Missing Sensor Intervals**:
   - Rather than containing NaNs or missing timestamps, the preprocessed files present a continuous 5-minute sequence where occasional sensor dropouts were linearly interpolated by the original authors (Hidalgo et al.). This ensures regular step continuity without synthetic modeling assumptions.
