# GlycoTwin

### Personalised Glucose Digital Twin for Predictive Diabetes Management

**A machine-learning-powered digital twin research prototype for forecasting future glucose-risk events and investigating personalised prediction models.**

**Happiest Health Digital Twin Challenge 2026 — Prototype & Code Submission**

[GitHub Repository](https://github.com/Eanshnexus/GlycoTwin_guptaekkansh_VITVellore) · [Architecture Diagram](docs/submission/GlycoTwin_Architecture.pdf) · [Project Presentation](docs/submission/GlycoTwin_Presentation.pdf) · [Demo Video](#demo-video)

---

## 1. Team Details

Registered Team Name         guptaekkansh
Team Leader                  Ekkansh Gupta 
College                      VIT Vellore
Project Title                GlycoTwin —Personalised Glucose Digital Twin for Predictive Diabetes Management 

## 2. Problem Statement

Continuous glucose monitoring provides valuable information about glucose fluctuations, but displaying historical readings alone does not establish whether future adverse glucose events can be predicted reliably for an individual.

Glucose dynamics are associated with several contextual factors, including recent glucose trends, insulin administration, carbohydrate intake, physical activity, and heart-rate measurements. A general prediction model may also perform differently across individuals because their observed patterns and event frequencies vary.

GlycoTwin investigates whether historical glucose patterns and contextual time-series measurements can support future hypoglycaemia-risk prediction, and whether adapting a population-trained model to an individual's historical observations improves predictive performance.

The project emphasises reproducible evaluation, participant-aware validation, temporal leakage prevention, and transparent reporting of model limitations.

## 3. Healthcare Use Case

GlycoTwin is a research prototype focused on people with Type 1 diabetes.

It provides an interactive environment for:

* Exploring historical continuous glucose monitoring (CGM) measurements.
* Examining available insulin, carbohydrate, activity, and heart-rate data.
* Predicting future glucose-risk events using machine-learning models.
* Comparing population-level models with personalised models.
* Reviewing historical predictions alongside observed outcomes.
* Investigating model performance and prediction errors.

The intended research application is to study how an individual's historical glucose patterns can inform future-event prediction.

**GlycoTwin is not a clinically validated medical device. Its predictions are experimental and must not be used for diagnosis, treatment, or real-time diabetes-management decisions.**

---

## 4. Project Overview

GlycoTwin is a modular research application combining a Python machine-learning pipeline, a FastAPI backend, and a React-based interactive dashboard.

Its central research question is:

> Does adapting a population-trained glucose prediction model to an individual's historical data improve the prediction of future glucose-risk events compared with using the population model alone?

The project evaluates this question experimentally rather than assuming that personalisation improves performance.

### Prediction Tasks

#### Task B — Primary Benchmark: Impending Hypoglycaemia Onset

Predict whether glucose will fall below 70 mg/dL within the next 30 minutes, conditional on the current glucose being at least 70 mg/dL.

For five-minute sampling intervals:

$$
y_t =
\mathbb{I}
\left(
\min_{k=1,\ldots,6} G_{t+k}<70
\right),
\quad \text{when } G_t \geq 70
$$

#### Task A — Secondary Benchmark: Future Hypoglycaemia Risk

Predict whether glucose will fall below 70 mg/dL at any point within the next 30 minutes, across all eligible prediction timestamps.

$$
y_t =
\mathbb{I}
\left(
\min_{k=1,\ldots,6} G_{t+k}<70
\right)
$$

The current glucose reading is excluded from the future outcome window. Incomplete future horizons are not automatically labelled negative.

These tasks are evaluated separately because predicting a future low-glucose reading is different from predicting an impending transition into hypoglycaemia.

---

## 5. Dataset and Provenance

### Primary Dataset

**HUPA-UCM Diabetes Dataset**

* Dataset page: [Mendeley Data — HUPA-UCM Diabetes Dataset](https://data.mendeley.com/datasets/3hbcscwz44/1)
* Publication: Hidalgo et al., *HUPA-UCM Diabetes Dataset*, Data in Brief 55 (2024), 110559.
* Publication DOI: [10.1016/j.dib.2024.110559](https://doi.org/10.1016/j.dib.2024.110559)
* Dataset DOI: [10.17632/3hbcscwz44.1](https://doi.org/10.17632/3hbcscwz44.1)
* Dataset licence: Creative Commons Attribution 4.0 International (CC BY 4.0), as documented in the project data audit.

### Dataset Summary

| Attribute                  | Description                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------- |
| Participants               | 25 people with Type 1 diabetes                                                              |
| Source observations        | 309,392 records                                                                             |
| Modelling-eligible windows | 308,942                                                                                     |
| Sampling interval          | Five minutes                                                                                |
| Glucose measurement        | Interstitial glucose, mg/dL                                                                 |
| Contextual variables       | Calories, heart rate, steps, basal insulin delivery, bolus insulin, and carbohydrate intake |
| Primary modelling target   | Impending hypoglycaemia onset within 30 minutes                                             |
| Data usage                 | Research and algorithmic evaluation                                                         |

The preprocessing pipeline excludes initial warm-up rows required for historical features and terminal rows without a complete future prediction horizon.

The modelling-eligible count is therefore lower than the original observation count.

### Dataset Access and Data Handling

The original research dataset is not committed wholesale to this repository.

To reproduce the pipeline:

1. Obtain the dataset from the official Mendeley Data page.
2. Extract the dataset locally.
3. Configure the input path using the project's configuration.
4. Run the documented data pipeline.
5. Run the automated tests before conducting new experiments.

Raw and processed research data are excluded from version control where configured by `.gitignore`.

### Static and Dynamic Health Data

The audited machine-learning pipeline uses historical glucose observations and available contextual time-series measurements.

Static demographics, diagnoses, laboratory results, and genetic markers are **not established as predictive inputs in the audited model results**.

If the interface includes a synthetic EHR-style profile for demonstration, those fields must be explicitly labelled synthetic and must not be represented as verified records belonging to the HUPA-UCM participants.

The availability of a static profile in the interface does not imply that its fields enter the trained model.

**Challenge requirement alignment:** The currently audited predictive model is based on the documented temporal features. Any additional static EHR demonstration layer must be described according to its actual implementation. Do not claim that static EHR variables improve predictive performance unless they have been incorporated and evaluated experimentally.

---

## 6. System Architecture

GlycoTwin separates data processing, machine learning, model serving, and the user interface.

```text
                 HUPA-UCM Diabetes Dataset
                           |
                           v
                Data Loading & Validation
                           |
                           v
               Preprocessing & Feature Engineering
                           |
                           v
                 Future-Event Label Construction
                           |
                           v
              Population Model & Personalisation
                           |
                           v
                  Model Evaluation Artifacts
                           |
               +-----------+------------+
               |                        |
               v                        v
        Historical Predictions     Model Inference
               |                        |
               +-----------+------------+
                           |
                           v
                    FastAPI Backend
                           |
                           v
                React + TypeScript Frontend
                           |
                           v
          Patient Digital Twin & Research Dashboard
```

The training and evaluation pipeline is separate from runtime inference. Historical out-of-fold predictions are distinguished from predictions generated by a fitted model.

The architecture diagram and editable source should be included in the submission materials.

* **Architecture diagram PDF:** `docs/submission/GlycoTwin_Architecture.pdf`
* **Editable architecture file:** `docs/submission/GlycoTwin_Architecture.pptx`

**Before publishing:** verify that both files exist and that their links work.

---

## 7. Technical Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* Recharts
* Lucide React

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

### Machine Learning and Data Processing

* pandas
* NumPy
* SciPy, where required
* scikit-learn
* XGBoost
* joblib

### Testing and Development

* pytest
* Git and GitHub
* Node.js and npm

The frontend consumes backend APIs for participant data, historical observations, prediction records, and model evaluation results.

---

## 8. AI/ML Methodology

### Feature Engineering

The audited pipeline uses 28 documented features derived from historical observations and contextual measurements.

Feature groups include:

* Current glucose state.
* Historical glucose lags.
* Short-term glucose changes and trends.
* Rolling glucose statistics.
* Time-of-day and weekday representations.
* Contextual features derived from activity, heart rate, insulin, and carbohydrate records.

Features are computed using information available at or before the prediction timestamp.

Participant identifiers, timestamps, target fields, and target-derived metadata are excluded from the predictive feature matrix.

### Models

The experiments compare three approaches:

1. **Rule-based baseline:** A transparent reference model using a predefined rule.
2. **Logistic regression:** A regularised statistical baseline.
3. **XGBoost:** A tree-based ensemble model capable of learning nonlinear relationships.

### Evaluation Strategy

The population models use participant-aware cross-validation so that the held-out participants are excluded from the corresponding training folds.

The personalisation experiment uses an initial chronological portion of an individual's history for calibration and a later portion for evaluation. A purge gap prevents calibration labels from depending on glucose outcomes in the evaluation period.

The population and personalised models are compared on the same future evaluation observations.

### Evaluation Metrics

* ROC-AUC.
* Average precision.
* Precision.
* Recall / sensitivity.
* F1-score.
* Specificity.
* Brier score.

Pooled results and participant-level macro summaries are reported separately. These metrics describe different aspects of model performance and are not interchangeable.

---

## 9. Model Evaluation Results

The following results are from the Phase 2 audit-run artifacts identified by the Phase 5 integration report as the authoritative held-out prediction source.

**Evaluation method:** Five-fold GroupKFold across 25 participants.

### Task A — Future Hypoglycaemia Risk

| Model               |  Threshold | Pooled ROC-AUC | Pooled Average Precision | Pooled Brier Score | Macro ROC-AUC | Macro Average Precision |
| ------------------- | ---------: | -------------: | -----------------------: | -----------------: | ------------: | ----------------------: |
| Rule-based baseline |     0.5949 |         0.9838 |                   0.8813 |             0.0306 |        0.9863 |                  0.8736 |
| Logistic regression |     0.8578 |         0.9806 |                   0.8860 |             0.0483 |        0.9824 |                  0.8711 |
| **XGBoost**         | **0.8707** |     **0.9882** |               **0.9316** |         **0.0381** |    **0.9891** |              **0.9153** |

### Task B — Impending Hypoglycaemia Onset

| Model               |  Threshold | Pooled ROC-AUC | Pooled Average Precision | Pooled Brier Score | Macro ROC-AUC | Macro Average Precision |
| ------------------- | ---------: | -------------: | -----------------------: | -----------------: | ------------: | ----------------------: |
| Rule-based baseline |     0.5506 |         0.9582 |                   0.4928 |             0.0284 |        0.9646 |                  0.5601 |
| Logistic regression |     0.8743 |         0.9555 |                   0.5186 |             0.0528 |        0.9607 |                  0.5731 |
| **XGBoost**         | **0.9148** |     **0.9667** |               **0.5843** |         **0.0709** |    **0.9711** |              **0.6325** |

**Interpretation:** The reported XGBoost results show strong retrospective discrimination on this dataset. For Task B, the pooled ROC-AUC is 0.9667 and the pooled average precision is 0.5843.

The Brier score measures probability prediction error and should not be interpreted as a discrimination metric. Pooled and macro-average results also measure different summaries of model performance.

The operational thresholds were selected during training cross-validation using an F1-oriented procedure. They must not be interpreted as guaranteeing a particular sensitivity on held-out observations.

These results are specific to the study cohort and evaluation design; they do not establish clinical effectiveness or guarantee performance for individual users.

---

## 10. Personalisation Experiment

The personalisation experiment investigates whether adapting a population-trained model to an individual's historical observations improves predictions on later observations.

The audited experiment uses:

* An initial chronological calibration period.
* A purge gap to prevent forward-label overlap.
* A later evaluation period.
* Comparable evaluation observations for the population and personalised approaches.

### Reported Results

* Participants in the experiment: 25.
* Successfully adapted participants: 24.
* Participants using fallback: 1.
* Fallback participant: `HUPA0009P`, due to insufficient positive onset examples in the calibration period.
* Reported mean participant-level change in Brier score: approximately **-0.0615**, defined as personalised minus population-model Brier score.

A negative Brier-score difference indicates a lower observed probability prediction error for the personalised approach under this experiment's evaluation setup.

The implemented adaptation uses a calibration procedure that adjusts predicted probabilities. A calibration improvement does not necessarily improve the model's ranking of events; ROC-AUC and average precision must therefore be evaluated separately.

These findings are exploratory and based on a small research cohort. They should not be interpreted as proof of clinical benefit or generalisability to other populations.

Refer to the Phase 2 audit and personalisation reports for the full methodology and participant-level results.

---

## 11. User Interface

The interactive GlycoTwin dashboard includes the following views.

### Overview

Displays dataset summaries, glucose trends, and model evaluation highlights.

### Patient Digital Twin

Provides participant selection, historical glucose visualisation, available contextual measurements, and historical navigation.

### Glucose Predictions

Displays the two prediction tasks, historical prediction records, predicted probabilities, and observed future labels where available.

### Personalisation Lab

Compares population and personalised model performance and presents participant-level results and fallback status.

### Model Evaluation

Shows model comparisons, evaluation metrics, and available performance visualisations.

### About & Data

Documents the project objectives, dataset provenance, prediction tasks, and scientific limitations.

The application distinguishes historical out-of-fold evaluation predictions from new model inference.

---

## 12. Installation and Quickstart

### Prerequisites

* Python 3.11 or later, subject to dependency compatibility.
* Node.js 20 or later.
* npm.
* Git.
* A local copy of the HUPA-UCM dataset.

### Step 1 — Clone the repository

```powershell
git clone https://github.com/Eanshnexus/GlycoTwin_guptaekkansh_VITVellore.git
cd GlycoTwin_guptaekkansh_VITVellore
```

### Step 2 — Obtain and configure the dataset

Download the HUPA-UCM Diabetes Dataset from:

https://data.mendeley.com/datasets/3hbcscwz44/1

Extract the data locally and configure the input path using the project's configuration.

Do not commit the raw research dataset to the public repository.

### Step 3 — Install Python dependencies

If the repository contains a verified `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

Otherwise, follow the dependency-management instructions in the repository.

### Step 4 — Run the automated tests

From the project root:

```powershell
python -m pytest tests/ -v
```

The latest Phase 5 report records **75 passing tests**. Run the test suite again in the environment used for reproduction rather than assuming that a previous test result guarantees future success.

### Step 5 — Start the backend

From the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

* API: http://127.0.0.1:8000
* Interactive API documentation: http://127.0.0.1:8000/docs
* Health endpoint: http://127.0.0.1:8000/api/health

### Step 6 — Start the frontend

Open a separate terminal:

```powershell
cd frontend
npm install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open the application:

http://127.0.0.1:5173/

### Step 7 — Build the frontend

From the frontend directory:

```powershell
npm.cmd run build
```

This creates the production bundle in `frontend/dist/` when the build succeeds.

---

## 13. Repository Structure

```text
GlycoTwin/
├── frontend/                 # React + TypeScript user interface
├── backend/                  # FastAPI application
├── ml/                       # Data pipeline and ML experiments
├── data/
│   ├── raw/                  # Locally obtained source data
│   ├── processed/            # Generated modelling dataset
│   └── sample/               # Small test fixtures, if present
├── artifacts/
│   ├── models/               # Model artifacts, subject to repository policy
│   └── evaluation/           # Evaluation reports and prediction artifacts
├── docs/
│   └── submission/           # Submission deliverables
├── tests/                    # Automated tests
├── .gitignore
├── LICENSE
└── README.md
```

This structure is representative. Consult the actual repository for the complete file listing.

Raw research data and unnecessary intermediate data should remain outside public version control.

---

## 14. Challenge Submission Deliverables

| Requirement                               | Location                                      | Status                        |
| ----------------------------------------- | --------------------------------------------- | ----------------------------- |
| Team details                              | This README                                   | **[COMPLETE DETAILS]**        |
| College/incubator information             | This README                                   | **[VERIFY INCUBATOR STATUS]** |
| Project title                             | This README                                   | Included                      |
| Problem statement and healthcare use case | Sections 2–3                                  | Included                      |
| Technical stack and AI/ML details         | Sections 7–10                                 | Included                      |
| Public GitHub repository                  | [GitHub Repository](https://github.com/Eanshnexus/GlycoTwin_guptaekkansh_VITVellore) | Public                        |
| Open-source licence                       | [`LICENSE`](LICENSE) (MIT)                    | MIT Open Source Licence       |
| Architecture diagram PDF                  | `docs/submission/GlycoTwin_Architecture.pdf`  | **[VERIFY FILE EXISTS]**      |
| Presentation PDF                          | `docs/submission/GlycoTwin_Presentation.pdf`  | **[VERIFY FILE EXISTS]**      |
| Editable architecture file                | `docs/submission/GlycoTwin_Architecture.pptx` | **[VERIFY FILE EXISTS]**      |
| Editable presentation                     | `docs/submission/GlycoTwin_Presentation.pptx` | **[VERIFY FILE EXISTS]**      |
| Minimum 20-minute demonstration video     | **[INSERT UNLISTED YOUTUBE LINK]**            | **Pending until uploaded**    |

All repository files and links must be accessible to the evaluation panel without additional permissions.

### Demo Video

**Video link:** [ADD THE ACTUAL UNLISTED YOUTUBE LINK BEFORE FINAL SUBMISSION]

The video must be at least 20 minutes long and should explain:

* The problem and healthcare use case.
* Dataset provenance and data handling.
* System architecture.
* Machine-learning pipeline and prediction tasks.
* Population model evaluation.
* Personalisation experiment.
* Working user interface.
* Limitations and intended use.

Do not mark this item complete until the video has been uploaded and its link has been verified.

---

## 15. Development and Verification Status

| Phase                                             | Status                                         |
| ------------------------------------------------- | ---------------------------------------------- |
| Phase 0 — Data Audit and Schema Verification      | Completed                                      |
| Phase 1 — Data Pipeline and Feature Engineering   | Completed                                      |
| Phase 2 — Machine Learning and Personalisation    | Completed; independently audited with caveats  |
| Phase 3 — FastAPI Backend                         | Implemented and verified in the Phase 5 report |
| Phase 4 — React Digital Twin Interface            | Implemented and production build verified      |
| Phase 5 — Integration and End-to-End Verification | Reported as passed                             |
| Phase 6 — Final Submission Packaging              | In progress                                    |

The latest Phase 5 report records 75 passing tests, a successful frontend production build, and successful verification of the primary application workflow.

These are development verification results, not evidence of clinical validation.

---

## 16. Licensing and Attribution

### Source Code

The project code is distributed under the licence specified in the repository's root [`LICENSE`](LICENSE) file.

**Before submission, verify that the file exists and that its licence matches this statement.**

### Research Dataset

The HUPA-UCM Diabetes Dataset is documented in this project as being distributed under the Creative Commons Attribution 4.0 International licence.

Dataset source:

Hidalgo, J. I., et al. *HUPA-UCM Diabetes Dataset*. Data in Brief 55 (2024), 110559.

* [Publication DOI](https://doi.org/10.1016/j.dib.2024.110559)
* [Dataset page](https://data.mendeley.com/datasets/3hbcscwz44/1)
* [CC BY 4.0 licence](https://creativecommons.org/licenses/by/4.0/)

The dataset licence is separate from the licence covering GlycoTwin's original source code. The project code licence does not relicense third-party research data or external assets.

---

## 17. Limitations and Research Integrity

GlycoTwin is an experimental research prototype.

Its limitations include:

* A cohort of 25 participants with Type 1 diabetes.
* Retrospective research observations.
* Dataset-specific recording patterns and event distributions.
* Potential differences in performance between participants.
* The distinction between probability calibration and ranking-based discrimination.
* Limited evidence for generalisation to other populations.
* The absence of prospective clinical validation.
* No demonstrated guarantee that a prediction prevents or reduces an adverse event.

Any synthetic demonstration data must be labelled clearly and distinguished from genuine source-dataset observations.

The project does not provide medical advice, diagnosis, treatment recommendations, or clinically validated real-time alerts.

It is not an autonomous artificial pancreas and must not be used for automated insulin dosing.

**GlycoTwin must not be used for real-world medical decision-making.**

---

## 18. Acknowledgements

We acknowledge the authors of the HUPA-UCM Diabetes Dataset and the associated research community for making the dataset and related resources available for research.

We also acknowledge the organisers of the Happiest Health Digital Twin Challenge 2026 for the opportunity to explore digital-twin concepts in healthcare.

---

*GlycoTwin — Researching personalised glucose prediction through data-driven digital twins.*
