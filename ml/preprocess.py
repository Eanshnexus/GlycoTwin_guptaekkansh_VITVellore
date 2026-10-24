"""
GlycoTwin: Preprocessing Module.
Applies conservative, documented cleaning to participant records:
- Chronological sorting
- Duplicate timestamp resolution (documented deduplication policy)
- Event semantics preservation (no forward-filling of discrete pulses like bolus or carbs)
- Logging of all exclusions and data adjustments
"""
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

def preprocess_single_participant(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans and standardizes a single participant's observations.
    
    Cleaning Policies:
    1. Chronological Sorting: Ensures records are monotonically ordered by timestamp.
    2. Duplicate Timestamps: If duplicate timestamps occur, the earliest record is kept
       and subsequent duplicates are logged and excluded.
    3. Missing Glucose Values: Rows with missing glucose are excluded because glucose is
       the primary physiological signal. (In HUPA-UCM preprocessed files, NaN count is 0).
    4. Discrete Events (Bolus & Carbohydrates): Left as discrete interval quantities.
       Zero means no bolus or carb input occurred during that 5-minute interval.
       Never forward-filled or interpolated.
    5. Continuous Sensors (Heart Rate, Calories, Basal Rate): Left as recorded.
       Zeros in calories represent resting basal expenditure or device off;
       zeros in basal_rate represent pump suspension or zero basal delivery.
       
    Returns:
        - Cleaned DataFrame
        - Preprocessing audit metadata dictionary
    """
    pid = df["participant_id"].iloc[0] if "participant_id" in df else "UNKNOWN"
    initial_rows = len(df)
    exclusions = {
        "duplicate_timestamps_excluded": 0,
        "missing_glucose_excluded": 0,
        "invalid_glucose_excluded": 0
    }

    # 1. Sort chronologically
    df_clean = df.sort_values("time").copy()

    # 2. Check and handle duplicate timestamps
    dup_mask = df_clean["time"].duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    if dup_count > 0:
        exclusions["duplicate_timestamps_excluded"] = dup_count
        df_clean = df_clean[~dup_mask].copy()

    # 3. Check for missing or invalid glucose
    nan_glucose_mask = df_clean["glucose"].isna()
    nan_g_count = int(nan_glucose_mask.sum())
    if nan_g_count > 0:
        exclusions["missing_glucose_excluded"] = nan_g_count
        df_clean = df_clean[~nan_glucose_mask].copy()

    invalid_g_mask = (df_clean["glucose"] <= 0) | (df_clean["glucose"] > 1000)
    inv_g_count = int(invalid_g_mask.sum())
    if inv_g_count > 0:
        exclusions["invalid_glucose_excluded"] = inv_g_count
        df_clean = df_clean[~invalid_g_mask].copy()

    df_clean = df_clean.reset_index(drop=True)
    final_rows = len(df_clean)

    meta = {
        "participant_id": pid,
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "total_excluded": initial_rows - final_rows,
        "exclusions_detail": exclusions
    }
    return df_clean, meta

def preprocess_cohort(cohort: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Applies preprocessing to all participants in the cohort.
    Maintains participant boundaries.
    """
    clean_cohort: Dict[str, pd.DataFrame] = {}
    cohort_meta: List[Dict[str, Any]] = []
    total_in = 0
    total_out = 0
    total_excluded = 0

    for pid, df in cohort.items():
        clean_df, meta = preprocess_single_participant(df)
        clean_cohort[pid] = clean_df
        cohort_meta.append(meta)
        total_in += meta["initial_rows"]
        total_out += meta["final_rows"]
        total_excluded += meta["total_excluded"]

    summary = {
        "total_participants": len(cohort),
        "total_input_rows": total_in,
        "total_output_rows": total_out,
        "total_excluded_rows": total_excluded,
        "participant_details": cohort_meta
    }
    return clean_cohort, summary
