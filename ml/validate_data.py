"""
GlycoTwin: Data Validation Module.
Validates participant data for chronological order, duplicate timestamps,
sampling interval distribution, glucose physiological boundaries,
missing values, and anomalies.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

def validate_participant_data(
    df: pd.DataFrame,
    expected_interval_minutes: int = 5,
    min_physiological_glucose: float = 20.0,
    max_physiological_glucose: float = 600.0,
    sensor_low_saturation: float = 40.0,
    sensor_high_saturation: float = 400.0
) -> Dict[str, Any]:
    """
    Performs comprehensive validation on a single participant's DataFrame.
    
    Returns a dictionary detailing:
        - participant_id
        - row_count
        - duplicate_rows
        - duplicate_timestamps
        - is_chronological
        - sampling_intervals: median, exact_expected_pct, gaps_gt_interval
        - missing_values_by_column
        - physiological_checks: invalid_glucose_count, extreme_high_count, extreme_low_count
        - validation_passed: boolean
        - warnings: list of detected anomalies or unusual physiological flags
        - errors: list of fatal issues (e.g. non-chronological, duplicates)
    """
    pid = df["participant_id"].iloc[0] if "participant_id" in df else "UNKNOWN"
    n_rows = len(df)
    errors: List[str] = []
    warnings: List[str] = []

    if n_rows == 0:
        errors.append("DataFrame contains 0 rows.")
        return {
            "participant_id": pid,
            "row_count": 0,
            "validation_passed": False,
            "errors": errors,
            "warnings": warnings
        }

    # 1. Duplicates
    dup_rows = int(df.duplicated(subset=["time", "glucose"]).sum())
    dup_times = int(df["time"].duplicated().sum())
    if dup_times > 0:
        errors.append(f"Found {dup_times} duplicate timestamps within participant '{pid}'.")

    # 2. Chronological Ordering
    time_series = pd.to_datetime(df["time"])
    is_sorted = time_series.is_monotonic_increasing
    if not is_sorted:
        warnings.append(f"Timestamps for participant '{pid}' are not strictly sorted chronologically; sorting required.")

    # 3. Sampling intervals
    sorted_times = time_series.sort_values().reset_index(drop=True)
    diffs_min = sorted_times.diff().dt.total_seconds() / 60.0
    valid_diffs = diffs_min.dropna()

    median_interval = float(valid_diffs.median()) if len(valid_diffs) > 0 else 0.0
    exact_matches = int((valid_diffs == expected_interval_minutes).sum())
    pct_exact = float((exact_matches / len(valid_diffs) * 100.0)) if len(valid_diffs) > 0 else 100.0
    gaps_gt_interval = int((valid_diffs > expected_interval_minutes).sum())
    max_gap_minutes = float(valid_diffs.max()) if len(valid_diffs) > 0 else 0.0

    if gaps_gt_interval > 0:
        warnings.append(
            f"Detected {gaps_gt_interval} intervals > {expected_interval_minutes}m (Max gap: {max_gap_minutes:.1f}m)."
        )

    # 4. Missingness
    null_counts = {col: int(df[col].isna().sum()) for col in df.columns}
    has_nulls = any(v > 0 for v in null_counts.values())
    if has_nulls:
        warnings.append(f"Missing values detected: { {k: v for k, v in null_counts.items() if v > 0} }")

    # 5. Glucose boundaries and physiological checks
    glucose = df["glucose"].values
    # Hard invalid readings (physiologically impossible or negative)
    invalid_glucose = (glucose <= 0) | (glucose > 1000.0) | np.isnan(glucose)
    invalid_count = int(invalid_glucose.sum())
    if invalid_count > 0:
        errors.append(f"Found {invalid_count} physically invalid glucose values (<=0 or >1000 mg/dL).")

    # Extreme but genuine clinical values
    extreme_low_count = int((glucose < sensor_low_saturation).sum())
    extreme_high_count = int((glucose > sensor_high_saturation).sum())
    hypo_l2_count = int((glucose < 54.0).sum())
    hypo_l1_count = int(((glucose >= 54.0) & (glucose < 70.0)).sum())

    if extreme_low_count > 0:
        warnings.append(f"{extreme_low_count} readings at or below sensor lower limit ({sensor_low_saturation} mg/dL).")
    if extreme_high_count > 0:
        warnings.append(f"{extreme_high_count} readings at or above sensor upper limit ({sensor_high_saturation} mg/dL).")

    validation_passed = len(errors) == 0

    return {
        "participant_id": pid,
        "row_count": n_rows,
        "validation_passed": validation_passed,
        "duplicate_rows": dup_rows,
        "duplicate_timestamps": dup_times,
        "is_chronological": is_sorted,
        "median_interval_minutes": median_interval,
        "pct_exact_interval": round(pct_exact, 2),
        "gaps_gt_interval": gaps_gt_interval,
        "max_gap_minutes": round(max_gap_minutes, 1),
        "null_counts": null_counts,
        "glucose_min": float(np.nanmin(glucose)) if len(glucose) > 0 else 0.0,
        "glucose_max": float(np.nanmax(glucose)) if len(glucose) > 0 else 0.0,
        "glucose_mean": float(np.nanmean(glucose)) if len(glucose) > 0 else 0.0,
        "hypo_l1_count": hypo_l1_count,
        "hypo_l2_count": hypo_l2_count,
        "errors": errors,
        "warnings": warnings
    }

def validate_cohort(cohort: Dict[str, pd.DataFrame], expected_interval_minutes: int = 5) -> Dict[str, Any]:
    """
    Validates an entire cohort of participants.
    Produces an aggregated machine-readable summary.
    """
    participant_reports = []
    total_rows = 0
    total_errors = 0
    total_warnings = 0

    for pid, df in cohort.items():
        rep = validate_participant_data(df, expected_interval_minutes=expected_interval_minutes)
        participant_reports.append(rep)
        total_rows += rep["row_count"]
        total_errors += len(rep["errors"])
        total_warnings += len(rep["warnings"])

    cohort_passed = total_errors == 0

    return {
        "cohort_size": len(cohort),
        "total_observations": total_rows,
        "cohort_validation_passed": cohort_passed,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "participant_validations": participant_reports
    }
