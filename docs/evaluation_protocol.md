# GlycoTwin Model Evaluation Protocol

## 1. Participant-Aware Cross-Validation Protocol

### Why Random Row Splitting is Scientifically Invalid
CGM records collected every 5 minutes exhibit strong autocorrelation across successive timesteps. Random row splitting places observation $t$ in the training set and observation $t+1$ (recorded 5 minutes later) in the test set, creating catastrophic evaluation leakage and fabricating artificially inflated metrics.

### Implemented Protocol: GroupKFold
To assess genuine clinical generalization to unseen individuals:
- The 25 participants are partitioned into **5 disjoint folds** using `GroupKFold(n_splits=5)`.
- In each fold, models are trained on approximately 20 participants (~250k rows) and evaluated on 4–5 completely held-out participants (~30k–150k rows).
- All preprocessing (e.g., standard scaling, class weights) is fitted **strictly on the training participants**.
- Zero records from held-out participants enter the training phase for that fold.

---

## 2. Threshold Selection & Calibration Protocol

1. **No Test-Set Threshold Peeking**: Classification thresholds are determined strictly using training fold predictions.
2. **Strategy**: The default threshold strategy selects the threshold maximizing $F_1$ score on the training out-of-bag predictions:
   $$t^* = \arg\max_{t} F_1(y_{\text{train}}, \hat{p}_{\text{train}} \ge t)$$
3. **Operational Application**: The threshold $t^*$ selected from training data is subsequently applied to the held-out validation participants to produce hard binary classifications ($\hat{y} \in \{0, 1\}$).

---

## 3. Evaluation Metrics

Because hypoglycemia risk is class-imbalanced (Task A: 8.95%, Task B: 3.03%), accuracy is uninformative. The evaluation reports:

| Metric | Clinical & Statistical Significance |
| :--- | :--- |
| **ROC-AUC** | Measure of global ranking ability across all possible discrimination thresholds. |
| **Average Precision (PR-AUC)** | Primary metric for imbalanced alert systems; evaluates the precision-recall trade-off without false-positive dilution. |
| **Sensitivity (Recall)** | Clinical capture rate: fraction of true hypoglycemia episodes successfully alerted before onset. |
| **Specificity** | Fraction of safe normoglycemic windows correctly identified as non-events (avoids alarm fatigue). |
| **Precision (PPV)** | Reliability of triggered alerts: fraction of triggered predictions that represent true events. |
| **F1-Score** | Harmonic mean of precision and recall at the operational threshold. |
| **Brier Score** | Mean squared difference between predicted probabilities and binary outcomes; measures calibration accuracy. |

---

## 4. Pooled vs. Participant-Balanced (Macro) Summaries

Because three participants (`HUPA0026P`, `HUPA0027P`, `HUPA0028P`) have long observation spans (90 to 574 days) compared to the remaining 22 participants (8 to 15 days), evaluations report both:
1. **Pooled Metrics**: Aggregates all out-of-fold predictions across all participants into a single confusion matrix and ROC/PR curve.
2. **Macro-Averaged Metrics**: Computes metrics independently for each participant and reports the mean and standard deviation across participants, weighting each individual patient equally.
