# GlycoTwin Feature Engineering Specification (Phase 1)

## 1. Overview & Core Principles

The GlycoTwin feature-engineering pipeline converts raw continuous glucose monitoring (CGM) measurements and synchronized wearable/pump telemetry into a causal, leak-free, tabular feature matrix for predictive modeling.

### Core Principles
1. **Strict Temporal Causality**: Every feature evaluated at prediction time $t$ uses exclusively observations recorded at or before timestamp $t$ ($s \le t$).
2. **Right-Aligned Rolling Windows**: All rolling statistical windows are right-aligned (never centered). A 30-minute rolling statistic over a 5-minute nominal grid strictly uses observations $\{t-5\Delta, t-4\Delta, t-3\Delta, t-2\Delta, t-\Delta, t\}$.
3. **No Cross-Participant Bleed**: Calculations are isolated strictly within participant boundaries.
4. **Metadata Isolation**: Participant identifiers (`participant_id`) and timestamps (`time`) are maintained strictly as metadata for grouping, calibration, and audit provenance—never as predictive inputs.

---

## 2. Implemented Feature Groups (27 Features)

The pipeline produces 27 numeric feature columns across six physiological and behavioral domains:

### Group A: Current Glycemic State (1 Feature)
| Feature Name | Definition | Lookback Window | Physical Units |
| :--- | :--- | :--- | :--- |
| `glucose_current` | Instantaneous CGM reading at prediction time $t$: $G_t$ | 0 min (instantaneous) | mg/dL |

### Group B: Glucose Lags (5 Features)
Captures recent historical trajectory at 5m, 10m, 15m, 30m, and 60m horizons:
| Feature Name | Formulation | Lookback Window | Physical Units |
| :--- | :--- | :--- | :--- |
| `glucose_lag_5m` | $G_{t-1}$ (1 step back) | 5 minutes | mg/dL |
| `glucose_lag_10m` | $G_{t-2}$ (2 steps back) | 10 minutes | mg/dL |
| `glucose_lag_15m` | $G_{t-3}$ (3 steps back) | 15 minutes | mg/dL |
| `glucose_lag_30m` | $G_{t-6}$ (6 steps back) | 30 minutes | mg/dL |
| `glucose_lag_60m` | $G_{t-12}$ (12 steps back) | 60 minutes | mg/dL |

### Group C: Glucose Trends & Derivatives (5 Features)
Measures direction, velocity, and rate of change (RoC) to detect rapid downward trajectories towards hypoglycemia:
| Feature Name | Formulation | Lookback Window | Physical Units |
| :--- | :--- | :--- | :--- |
| `glucose_change_5m` | $\Delta G_{5} = G_t - G_{t-1}$ | 5 minutes | mg/dL |
| `glucose_change_15m` | $\Delta G_{15} = G_t - G_{t-3}$ | 15 minutes | mg/dL |
| `glucose_change_30m` | $\Delta G_{30} = G_t - G_{t-6}$ | 30 minutes | mg/dL |
| `glucose_slope_15m` | $\text{RoC}_{15} = (G_t - G_{t-3}) / 15.0$ | 15 minutes | mg/dL / min |
| `glucose_slope_30m` | $\text{RoC}_{30} = (G_t - G_{t-6}) / 30.0$ | 30 minutes | mg/dL / min |

### Group D: Rolling Glucose Statistics & Variability (7 Features)
Quantifies short- and medium-term glucose variability and extreme excursions:
| Feature Name | Formulation | Lookback Window | Physical Units |
| :--- | :--- | :--- | :--- |
| `glucose_mean_15m` | $\frac{1}{3} \sum_{k=0}^2 G_{t-k}$ | 15 minutes (3 steps) | mg/dL |
| `glucose_mean_30m` | $\frac{1}{6} \sum_{k=0}^5 G_{t-k}$ | 30 minutes (6 steps) | mg/dL |
| `glucose_mean_60m` | $\frac{1}{12} \sum_{k=0}^{11} G_{t-k}$ | 60 minutes (12 steps) | mg/dL |
| `glucose_std_30m` | Rolling sample standard deviation $\sigma(G_{t-5..t})$ | 30 minutes (6 steps) | mg/dL |
| `glucose_std_60m` | Rolling sample standard deviation $\sigma(G_{t-11..t})$ | 60 minutes (12 steps) | mg/dL |
| `glucose_min_30m` | Rolling minimum $\min(G_{t-5..t})$ | 30 minutes (6 steps) | mg/dL |
| `glucose_max_30m` | Rolling maximum $\max(G_{t-5..t})$ | 30 minutes (6 steps) | mg/dL |

### Group E: Diurnal & Circadian Cycles (4 Features)
Captures biological insulin sensitivity variations across circadian day/night and weekly rhythms using continuous sinusoidal harmonics:
| Feature Name | Formulation | Range |
| :--- | :--- | :--- |
| `hour_sin` | $\sin(2\pi \cdot (\text{hour} + \text{minute}/60) / 24)$ | $[-1.0, 1.0]$ |
| `hour_cos` | $\cos(2\pi \cdot (\text{hour} + \text{minute}/60) / 24)$ | $[-1.0, 1.0]$ |
| `weekday_sin` | $\sin(2\pi \cdot \text{weekday} / 7)$ | $[-1.0, 1.0]$ |
| `weekday_cos` | $\cos(2\pi \cdot \text{weekday} / 7)$ | $[-1.0, 1.0]$ |

### Group F: Contextual Wearables & Insulin Infusion (6 Features)
Integrates synchronized Fitbit biometrics and Medtronic 640G CSII telemetry:
| Feature Name | Formulation | Lookback Window | Physical Meaning |
| :--- | :--- | :--- | :--- |
| `recent_calories` | Rolling sum of calories burned | 30 minutes (6 steps) | Active energy expenditure (kcal) |
| `recent_steps` | Rolling sum of steps | 30 minutes (6 steps) | Physical movement count |
| `recent_heart_rate` | Rolling mean heart rate | 30 minutes (6 steps) | Mean cardiovascular exertion (bpm) |
| `recent_basal_rate` | Active basal delivery at time $t$ | Instantaneous ($t$) | Continuous subcutaneous insulin (U/5-min) |
| `recent_bolus_volume`| Rolling sum of bolus deliveries | 60 minutes (12 steps) | Active bolus insulin units delivered |
| `recent_carb_input` | Rolling sum of carbohydrate logs | 60 minutes (12 steps) | Digested carbohydrate intake (grams) |

---

## 3. Warmup Policy & Missing History Handling

1. **Warmup Window**: Because the 60-minute rolling features require 12 previous 5-minute intervals, the first 12 steps of every participant recording cannot compute un-biased rolling statistics.
2. **Explicit Eligibility Filtering**: Rather than imputing or back-filling missing historical values with future data, rows during the warmup phase are explicitly marked with `is_modelling_eligible = False`.
3. **No Leakage Imputation**: When building models in Phase 2, training and inference will strictly use observations where `is_modelling_eligible == True`.
