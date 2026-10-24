# GlycoTwin Machine Learning Methodology (Phase 2)

## 1. Overview & Research Tasks

GlycoTwin implements and evaluates two distinct predictive classification tasks using the continuous glucose monitoring (CGM), insulin infusion, and biometric features established in Phase 1:

### Task A: Future Hypoglycemia Risk (Secondary Task)
- **Clinical Target**: Predict whether interstitial glucose falls below **70 mg/dL** at any point during the upcoming **30 minutes**:
  $$y_t = \mathbb{I}\left(\min_{k=1..6} G_{t+k} < 70\text{ mg/dL}\right)$$
- **Eligible Cohort**: All valid observations ($N = 308,942$).
- **Prevalence**: 8.95% positive ($N = 27,661$).
- **Note**: This includes windows where current glucose $G_t$ is already below 70 mg/dL, representing future 30-minute hypoglycemia status.

### Task B: Impending Hypoglycemia Onset (Primary Research Task)
- **Clinical Target**: Predict whether glucose drops below **70 mg/dL** during the upcoming **30 minutes**, conditional on the participant currently being normoglycemic or hyperglycemic ($G_t \ge 70\text{ mg/dL}$):
  $$\text{onset}_t = \mathbb{I}\left(G_t \ge 70\text{ mg/dL} \land \min_{k=1..6} G_{t+k} < 70\text{ mg/dL}\right)$$
- **Eligible Cohort**: Filtered to non-hypoglycemic baseline windows ($N = 288,628$).
- **Prevalence**: 3.03% positive ($N = 8,742$).
- **Significance**: This is the primary clinical alert task; it predicts impending onset transitions where patient corrective action (e.g., 15g fast-acting carbohydrates) is therapeutics-relevant.

---

## 2. Leak-Free Feature Matrix & Exclusions

Models are provided strictly with 28 backward-looking features computed at or before prediction time $t$:
- **Current State**: `glucose_current`
- **Lags**: `glucose_lag_5m`, `glucose_lag_10m`, `glucose_lag_15m`, `glucose_lag_30m`, `glucose_lag_60m`
- **Trends & RoC**: `glucose_change_5m`, `glucose_change_15m`, `glucose_change_30m`, `glucose_slope_15m`, `glucose_slope_30m`
- **Rolling Statistics**: `glucose_mean_15m`, `glucose_mean_30m`, `glucose_mean_60m`, `glucose_std_30m`, `glucose_std_60m`, `glucose_min_30m`, `glucose_max_30m`
- **Circadian Rhythms**: `hour_sin`, `hour_cos`, `weekday_sin`, `weekday_cos`
- **Contextual Wearables & CSII**: `recent_calories`, `recent_steps`, `recent_heart_rate`, `recent_basal_rate`, `recent_bolus_volume`, `recent_carb_input`

### Quarantined Fields (Strictly Excluded from Feature Matrix)
`participant_id`, `time`, `source_file`, `target_hypo_30m`, `is_hypo_onset_30m`, `future_min_glucose_30m`, `target_eligible`, `is_modelling_eligible`.

---

## 3. Evaluated Model Architectures

### 1. Baseline A: Rule-Based Trajectory Heuristic (`RuleBasedHypoBaseline`)
- **Philosophy**: Non-parametric deterministic physiological reference.
- **Formulation**: Projects glucose 15 minutes ahead using recent 15-minute slope:
  $$G_{\text{proj}} = G_t + 15.0 \cdot \text{slope}_{15\text{m}}$$
- Maps projected glucose to a continuous sigmoid risk score:
  $$P(\text{risk}) = \frac{1}{1 + \exp\left(\frac{G_{\text{proj}} - 75.0}{10.0}\right)}$$

### 2. Baseline B / Model A: Regularized Logistic Regression
- **Architecture**: Scikit-learn Pipeline with `StandardScaler()` and `LogisticRegression`.
- **Hyperparameters**:
  - Regularization: $L_2$ penalty, $C = 1.0$.
  - Solver: `lbfgs`, max iterations: 1,000.
  - Class Weighting: `balanced` (inversely proportional to class frequencies on training split).
  - Reproducibility: `random_state = 42`.

### 3. Model B: Extreme Gradient Boosting (`XGBClassifier`)
- **Architecture**: Regularized shallow decision tree ensemble.
- **Hyperparameters**:
  - Number of Estimators: 100
  - Maximum Tree Depth: 4 (controls overfitting and interaction complexity)
  - Learning Rate: 0.05
  - Subsample: 0.8 (row subsampling per tree)
  - Colsample by Tree: 0.8 (feature subsampling per tree)
  - Objective / Metric: Binary logloss
  - Imbalance Handling: `scale_pos_weight = N_neg / N_pos` computed strictly on training folds.
