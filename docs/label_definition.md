# GlycoTwin Label Definition & Prediction Target Specification

## 1. Mathematical Formulation

The prediction task addresses the research question:
*"Will interstitial glucose drop below the clinical hypoglycemia threshold at any point during the upcoming 30 minutes?"*

For an observation made at timestamp $t$:
$$y_t = \mathbb{I}\left(\min_{k \in \{1, 2, 3, 4, 5, 6\}} G_{t+k} < 70\text{ mg/dL}\right)$$

Where:
- $G_{t}$ is the interstitial continuous glucose reading at prediction time $t$.
- $k \in \{1, \dots, 6\}$ represents the six consecutive 5-minute forward steps: $\{t+5\text{m}, t+10\text{m}, t+15\text{m}, t+20\text{m}, t+25\text{m}, t+30\text{m}\}$.
- $y_t = 1$ indicates a positive hypoglycemia risk event within the 30-minute window.
- $y_t = 0$ indicates that glucose remains $\ge 70\text{ mg/dL}$ across the entire 30-minute window.

---

## 2. Core Safety & Leakage-Prevention Constraints

### Exclusion of the Current Observation $G_t$
Under no circumstances is the current glucose reading $G_t$ permitted to contribute to the future outcome label $y_t$. The label solely inspects future intervals starting strictly at $t+1$ ($t+5\text{ min}$).

### Non-Defaulting Policy for Incomplete Horizons
For observations near the end of a participant's recording, or preceding an unexpected data collection interruption:
- **Rule**: If the forward horizon does not contain a full, contiguous 30-minute sequence, $y_t$ is assigned `NaN` and `target_eligible` is set to `False`.
- **Prohibition**: An incomplete forward horizon must **NEVER** be assumed to be negative ($y_t = 0$). Doing so would artificially depress the true event rate and inject false negatives into the evaluation set.

### Participant Boundary Isolation
The forward window is strictly confined to the recording of participant $P_i$. Under no circumstances can a forward horizon evaluate observations belonging to another participant $P_{i+1}$.

---

## 3. Impending Hypoglycemia Onset Sub-Label

In addition to the primary unconditional hypoglycemia risk label, the pipeline computes an onset-specific indicator:
$$\text{onset}_t = \mathbb{I}\left(G_t \ge 70\text{ mg/dL} \land \min_{k=1..6} G_{t+k} < 70\text{ mg/dL}\right)$$

### Clinical Relevance
While the unconditional label detects whether the patient will experience hypoglycemia in the next 30 minutes regardless of their current state, the onset label isolates the transition from normoglycemia/hyperglycemia into hypoglycemia—the exact scenario where a predictive alert provides actionable therapeutic utility.

---

## 4. Cohort Event Prevalence

Across the 308,942 modelling-eligible windows in the HUPA-UCM dataset:
- **Unconditional 30-minute Hypo Risk ($y_t = 1$)**: **27,661 positive windows** (**8.95%** prevalence).
- **Negative Windows ($y_t = 0$)**: **281,281 windows** (**91.05%**).
- **Impending Hypo Onset Events**: **8,742 discrete transitions**.
- **Excluded Incomplete Horizons**: Exactly 150 windows (6 terminal steps $\times$ 25 participants).

---

## 5. Serial Correlation & Window Overlap

Because the pipeline evaluates rolling prediction windows at every 5-minute timestep, successive windows $\{t, t+1, \dots\}$ overlap in their future evaluation horizons.
- Consecutive windows share 5 of their 6 forward intervals.
- **Evaluation Mandate**: Random row splitting would cause massive autocorrelation leakage across train and test sets.
- **Enforcement**: Phase 2 model evaluation strictly utilizes **GroupKFold (Leave-Participants-Out)** for cross-participant generalization and **chronological forward holdout splits** for personalized adaptation testing.
