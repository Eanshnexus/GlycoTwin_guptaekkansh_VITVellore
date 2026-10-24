"""
GlycoTwin: Label Creation Module.
Constructs forward-looking supervised target labels for hypoglycemia risk prediction:
    y_t = I( min(G[t+1], G[t+2], ..., G[t+H]) < threshold )

Safety & Leakage-Prevention Guarantees:
1. Current observation G[t] is strictly excluded from future label.
2. Participant boundaries are never crossed.
3. Incomplete future horizons (e.g. file end or intervals with sampling gaps > expected)
   are flagged with NaN / eligible_target=False, NEVER defaulted to 0 (negative).
4. Configurable threshold (default 70.0 mg/dL) and horizon (default 30 min / 6 steps).
"""
from typing import Optional, Tuple
import numpy as np
import pandas as pd

def create_future_hypo_labels(
    df: pd.DataFrame,
    threshold: float = 70.0,
    horizon_minutes: int = 30,
    expected_interval_minutes: int = 5
) -> pd.DataFrame:
    """
    Computes binary future hypoglycemia label and horizon eligibility for a single participant.
    
    Inputs:
        - df: Preprocessed DataFrame for ONE participant, sorted chronologically.
        - threshold: Glucose boundary below which a positive event is triggered (default 70 mg/dL).
        - horizon_minutes: Forward prediction horizon in minutes (default 30).
        - expected_interval_minutes: Nominal step size (default 5).
        
    Returns DataFrame with:
        - target_hypo_30m: 1 (positive event in (t, t+30m]), 0 (no event), NaN (horizon invalid/incomplete)
        - target_eligible: Boolean flag indicating whether the full 30-minute forward horizon is valid
        - future_min_glucose_30m: Minimum glucose observed in (t, t+30m] (or NaN if incomplete)
        - is_hypo_onset_30m: 1 if target_hypo_30m == 1 and G[t] >= 70 mg/dL (impending onset), else 0
    """
    n = len(df)
    k_steps = horizon_minutes // expected_interval_minutes
    
    res = pd.DataFrame(index=df.index)
    res["target_hypo_30m"] = np.nan
    res["target_eligible"] = False
    res["future_min_glucose_30m"] = np.nan
    res["is_hypo_onset_30m"] = np.nan

    if n <= k_steps:
        # Not enough observations to even form one full forward horizon
        return res

    g = df["glucose"].values
    times = df["time"].values

    targets = np.full(n, np.nan)
    eligibles = np.zeros(n, dtype=bool)
    future_mins = np.full(n, np.nan)
    onsets = np.full(n, np.nan)

    # For each index i, future window is i+1 through i+k_steps inclusive
    for i in range(n - k_steps):
        # Verify temporal continuity: the timestamp at i+k_steps must be exactly k_steps * expected_interval_minutes ahead
        t_start = pd.Timestamp(times[i])
        t_end = pd.Timestamp(times[i + k_steps])
        actual_delta_min = (t_end - t_start).total_seconds() / 60.0
        expected_delta_min = k_steps * expected_interval_minutes

        # Allow small tolerance of 30 seconds for clock jitter
        if abs(actual_delta_min - expected_delta_min) <= 0.5:
            # Full contiguous forward window is present
            future_vals = g[i + 1 : i + k_steps + 1]
            min_future_g = float(np.min(future_vals))
            
            is_hypo = 1 if min_future_g < threshold else 0
            curr_g = g[i]
            is_onset = 1 if (is_hypo == 1 and curr_g >= threshold) else 0

            targets[i] = is_hypo
            eligibles[i] = True
            future_mins[i] = min_future_g
            onsets[i] = is_onset
        else:
            # Incomplete or discontinuous window due to gap > expected interval
            targets[i] = np.nan
            eligibles[i] = False
            future_mins[i] = np.nan
            onsets[i] = np.nan

    res["target_hypo_30m"] = targets
    res["target_eligible"] = eligibles
    res["future_min_glucose_30m"] = future_mins
    res["is_hypo_onset_30m"] = onsets

    return res
