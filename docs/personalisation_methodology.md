# GlycoTwin Personalisation Methodology & Experimental Design

## 1. Central Research Hypothesis

The primary research question of the GlycoTwin project is:
> *"Does adapting a population-trained glucose prediction model to an individual's historical data improve prediction of future glucose-risk events compared with using the population model alone?"*

This inquiry is treated as an empirical hypothesis; improvements are never assumed or fabricated.

---

## 2. Experimental Protocol

To perform a leak-free, mathematically sound comparison, the experiment enforces a **chronological forward split within each evaluation participant**:

```
Participant Timeline:
[======================= Total Observations =======================]
[--- 30% Calibration Segment ---] [------- 70% Evaluation Segment -------]
       (Adapter Fitting)                (Head-to-Head Comparison)
```

### Step 1: Population Model Training (Strict LOPO)
For each evaluation participant $p \in \{1, \dots, 25\}$:
- The population model is trained on all other cohort participants ($N \setminus \{p\}$).
- Participant $p$'s data is completely quarantined from the population model.

### Step 2: Personalisation on Calibration Segment
- The initial 30% chronological segment of participant $p$'s recording is designated as the **Personal Calibration Window**.
- A lightweight, regularized adaptation layer (Platt log-odds scaling) is fitted to map population log-odds to the individual's baseline empirical risk:
  $$P_{\text{pers}}(y=1 | x) = \sigma(w \cdot z_{\text{pop}}(x) + b)$$
  Where $z_{\text{pop}}(x) = \text{logit}(P_{\text{pop}}(y=1 | x))$.

### Step 3: Explicit Fallback Policy for Sparse Events
If participant $p$'s calibration segment contains **fewer than 2 positive hypoglycemia events** (e.g. `HUPA0009P`, who has 0 events), fitting a personal adapter is ill-conditioned.
- **Protocol**: The system triggers an explicit status: `fallback_insufficient_events`.
- In fallback mode, the unadapted population model is used directly as the primary predictor.
- This participant is retained in the evaluation table and clearly marked.

### Step 4: Fair Head-to-Head Evaluation
Both the unadapted population model and the adapted personalised model are evaluated on the **exact same remaining 70% future holdout segment**:
- No future evaluation labels are ever seen during population training or personal adaptation.
- Both models produce predictions for the identical set of timestamps.
- Paired differences ($\Delta\text{PR-AUC} = \text{PR-AUC}_{\text{pers}} - \text{PR-AUC}_{\text{pop}}$, $\Delta\text{Brier} = \text{Brier}_{\text{pers}} - \text{Brier}_{\text{pop}}$) are computed participant-by-participant.
