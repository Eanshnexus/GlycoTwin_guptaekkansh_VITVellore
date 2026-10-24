# GlycoTwin Project Specification & Engineering Architecture

## 1. Project Objective & Research Hypothesis

### Research Objective
Develop a personalized glucose digital twin application that represents anonymized research participants using historical glucose and contextual measurements, predicts future glucose-risk events using strictly retrospective information, and compares a general population model against an individually adapted model.

### Primary Research Hypothesis
> *"Does adapting a population-trained glucose prediction model to an individual's historical data improve prediction of future glucose-risk events compared with using the population model alone?"*

This question is treated strictly as an empirical hypothesis; improvements will never be assumed or fabricated.

---

## 2. Research Integrity & Safety Rules

1. **Non-Clinical Research Prototype**: GlycoTwin is strictly a retrospective research prototype. It does not provide medical advice and has not been clinically validated.
2. **Explicit Retrospective Grounding**: Retrospective observations must be clearly distinguished from live monitoring. Predictions will explicitly display their observation timestamp and prediction horizon.
3. **No Fabricated Data or Claims**: Synthetic demonstration fixtures will be clearly marked as synthetic. Real participant metrics will come strictly from verified API endpoints and saved evaluation files.
4. **Prevention of Future Data Leakage**:
   - At prediction time $t$, features may only be computed using information where timestamp $s \le t$.
   - Future measurements ($s > t$) are quarantined exclusively for calculating ground-truth evaluation labels.
   - Random row-shuffling across time is strictly prohibited.

---

## 3. Verified Prediction Target

- **Task**: Predict whether interstitial glucose falls below the clinical hypoglycemia threshold within the next 30 minutes.
- **Horizon**: $\Delta t = 30\text{ minutes}$ (6 forward 5-minute intervals).
- **Label Formulation**:
  $$Y_t = \mathbb{I}\left(\min_{k \in \{1, 2, 3, 4, 5, 6\}} G_{t+k} < 70\text{ mg/dL}\right)$$
- **Observed Cohort Prevalence**:
  - Unconditional 30-min Hypo Risk: 9.76% across all eligible windows.
  - Impending Hypo Onset ($G_t \ge 70\text{ mg/dL}$): 3.06% across normoglycemic windows.

---

## 4. Input Feature Availability & Engineering Plan (Phase 1)

Features will be computed using rolling causal lookback windows:

| Feature Category | Candidate Variables | Lookback Window |
| :--- | :--- | :--- |
| **Instantaneous CGM** | Current glucose $G_t$ | Instantaneous ($t$) |
| **Rate of Change (RoC)** | $\Delta G_{15} = (G_t - G_{t-3})/15$, $\Delta G_{30} = (G_t - G_{t-6})/30$, $\Delta G_{60} = (G_t - G_{t-12})/60$ | 15, 30, 60 minutes |
| **Glucose Variability** | Rolling standard deviation $\sigma(G_{t-12..t})$, rolling range $(\max - \min)$ | 60 minutes (12 steps) |
| **Circadian Rhythm** | $\sin(2\pi \cdot \text{hour}/24)$, $\cos(2\pi \cdot \text{hour}/24)$, day of week | Instantaneous ($t$) |
| **Recent Insulin** | Cumulative bolus $\sum \text{bolus}_{t-12..t}$, active basal rate | 60 minutes |
| **Recent Nutrition** | Cumulative carbohydrate input $\sum \text{carbs}_{t-12..t}$ | 60 minutes |
| **Physical Activity** | Rolling steps $\sum \text{steps}_{t-6..t}$, rolling mean heart rate | 30 minutes |

---

## 5. Machine Learning Design & Evaluation Framework (Phase 2)

### A. Population Model vs. Personalised Model Comparison
1. **Population Model**:
   - Trained across $N-k$ training participants using cross-validation.
   - Evaluated on held-out test participants (Zero-Shot Cross-Participant Generalization).
2. **Personalised Model**:
   - For a held-out participant, an initial chronological segment (e.g. first 50% of the timeline) is used to fine-tune/calibrate the model weights.
   - The adapted model is evaluated on the remaining held-out segment (last 50% of the timeline).
   - The population model is evaluated on the exact same held-out segment for direct, head-to-head, leak-free comparison.

### B. Evaluation Metrics
- **ROC-AUC** & **Precision-Recall AUC (PR-AUC / Average Precision)**
- **Sensitivity / Recall** at calibrated thresholds (e.g. 80% recall threshold for hypoglycemia alerts)
- **Precision**, **Specificity**, **F1-Score**, and **Confusion Matrix**
- **Brier Score** for probabilistic calibration assessment

---

## 6. Monorepo Architecture

```
GlycoTwin/
├── data/
│   ├── raw/                 # Ignored raw data directory
│   ├── processed/           # Ignored preprocessed data directory
│   └── sample/              # Minimal synthetic fixtures for unit tests
├── ml/
│   ├── audit.py             # Phase 0 cohort auditor
│   ├── inspect_data.py      # Non-destructive inventory and schema tool
│   ├── pipeline.py          # Phase 1 feature engineer and loader
│   ├── models.py            # Phase 2 population and personalized models
│   └── evaluate.py          # Phase 2 evaluation metrics and curve generator
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entrypoint
│   │   ├── routers/         # Health, patients, observations, predictions, evaluation
│   │   └── schemas/         # Pydantic validation models
│   └── tests/               # API endpoint unit tests
├── frontend/
│   ├── src/
│   │   ├── components/      # UI cards, navigation, metric pills
│   │   ├── views/           # Clinical Overview, Twin, Prediction, Lab, Evaluation
│   │   └── services/        # API client and TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
├── artifacts/
│   ├── models/              # Serialized joblib models
│   └── evaluation/          # Audit summaries, ROC/PR curves, evaluation JSONs
├── docs/
│   ├── data_inventory.md
│   ├── data_dictionary.md
│   ├── data_quality_report.md
│   └── project_specification.md
├── tests/
│   └── test_phase0_audit.py
├── .gitignore
├── README.md
└── LICENSE
```

---

## 7. Reusable Audit Command

To rerun the Phase 0 data audit at any time:

```powershell
python ml/inspect_data.py
```

The script will locate the directories, verify file counts, compute sampling consistency and target prevalences, and update `artifacts/evaluation/phase0_audit_summary.json` without modifying any source files.
