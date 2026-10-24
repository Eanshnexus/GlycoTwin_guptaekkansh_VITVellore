"""
Phase 0 Data Audit Script for HUPA-UCM Diabetes Dataset.
Audits all 25 participant files:
- Record counts and temporal spans
- Sampling intervals and regularity
- Column completeness and missingness
- Glucose distributions and clinical ranges (hypoglycemia, normoglycemia, hyperglycemia)
- Prediction horizon target feasibility (30-min vs 60-min, overall vs onset)
"""
import os
import glob
import json
import pandas as pd
import numpy as np

def run_audit(data_dir: str):
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    records = []
    total_rows = 0
    
    for f in files:
        pid = os.path.basename(f).replace(".csv", "")
        df = pd.read_csv(f, sep=";")
        
        # Parse time
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)
        n = len(df)
        total_rows += n
        
        # Time continuity
        diffs = df["time"].diff().dt.total_seconds() / 60.0
        gaps_gt_5m = (diffs > 5.0).sum()
        pct_exact_5m = ((diffs == 5.0).sum() / (n - 1) * 100) if n > 1 else 100.0
        
        t_start = df["time"].min()
        t_end = df["time"].max()
        span_days = (t_end - t_start).total_seconds() / 86400.0
        
        # Missingness
        nulls = df.isna().sum().to_dict()
        
        # Glucose statistics
        g = df["glucose"].values
        g_min = float(np.min(g))
        g_max = float(np.max(g))
        g_mean = float(np.mean(g))
        g_std = float(np.std(g))
        
        # Clinical Ranges
        # Hypoglycemia: < 70 mg/dL (Level 1)
        # Severe Hypoglycemia: < 54 mg/dL (Level 2)
        # Target Range: 70 - 180 mg/dL
        # Hyperglycemia: > 180 mg/dL
        hypo_l1 = int((g < 70).sum())
        hypo_l2 = int((g < 54).sum())
        in_range = int(((g >= 70) & (g <= 180)).sum())
        hyper = int((g > 180).sum())
        
        # Target evaluation: Next 30 minutes (6 steps forward)
        # Horizon: i+1 to i+6
        # Event 1: Unconditional future hypo (< 70 mg/dL)
        # Event 2: Impending hypo onset (Current glucose >= 70 mg/dL, and future min < 70 mg/dL)
        future_30m_min = np.array([np.min(g[i+1:min(i+7, n)]) if i+1 < n else np.nan for i in range(n)])
        valid_mask_30m = np.arange(n) <= (n - 7)
        
        future_30m_valid = future_30m_min[valid_mask_30m]
        curr_g_valid = g[valid_mask_30m]
        
        hypo_30m_all = (future_30m_valid < 70).sum()
        hypo_30m_all_pct = (hypo_30m_all / len(future_30m_valid) * 100) if len(future_30m_valid) > 0 else 0.0
        
        onset_mask = curr_g_valid >= 70
        onset_denom = onset_mask.sum()
        onset_30m_count = ((future_30m_valid < 70) & onset_mask).sum()
        onset_30m_pct = (onset_30m_count / onset_denom * 100) if onset_denom > 0 else 0.0
        
        # Contextual modalities
        cal_nz = int((df["calories"] > 0).sum()) if "calories" in df else 0
        hr_nz = int((df["heart_rate"] > 0).sum()) if "heart_rate" in df else 0
        step_nz = int((df["steps"] > 0).sum()) if "steps" in df else 0
        basal_nz = int((df["basal_rate"] > 0).sum()) if "basal_rate" in df else 0
        bolus_nz = int((df["bolus_volume_delivered"] > 0).sum()) if "bolus_volume_delivered" in df else 0
        carb_nz = int((df["carb_input"] > 0).sum()) if "carb_input" in df else 0
        
        records.append({
            "participant_id": pid,
            "rows": n,
            "start_time": str(t_start),
            "end_time": str(t_end),
            "span_days": round(span_days, 2),
            "pct_5min_intervals": round(pct_exact_5m, 2),
            "gaps_gt_5min": int(gaps_gt_5m),
            "glucose_min": round(g_min, 1),
            "glucose_max": round(g_max, 1),
            "glucose_mean": round(g_mean, 1),
            "glucose_std": round(g_std, 1),
            "time_in_range_pct": round(in_range / n * 100, 2),
            "time_hypo_pct": round(hypo_l1 / n * 100, 2),
            "time_hypo_severe_pct": round(hypo_l2 / n * 100, 2),
            "time_hyper_pct": round(hyper / n * 100, 2),
            "future_30m_hypo_all_count": int(hypo_30m_all),
            "future_30m_hypo_all_pct": round(hypo_30m_all_pct, 2),
            "future_30m_hypo_onset_count": int(onset_30m_count),
            "future_30m_hypo_onset_pct": round(onset_30m_pct, 2),
            "bolus_events": bolus_nz,
            "carb_events": carb_nz,
            "heart_rate_non_zero_pct": round(hr_nz / n * 100, 2),
            "steps_non_zero_pct": round(step_nz / n * 100, 2),
            "null_counts": nulls
        })
        
    summary_df = pd.DataFrame(records)
    return summary_df

if __name__ == "__main__":
    prep_dir = r"c:\Users\gupta\Desktop\GlycoTwin\HUPA-UCM Diabetes Dataset\HUPA-UCM Diabetes Dataset\Preprocessed"
    df = run_audit(prep_dir)
    print("=== HUPA-UCM DATASET AUDIT SUMMARY ===")
    print(f"Total Participants: {len(df)}")
    print(f"Total Rows: {df['rows'].sum()}")
    print(f"Mean Span (Days): {df['span_days'].mean():.1f} (min: {df['span_days'].min():.1f}, max: {df['span_days'].max():.1f})")
    print(f"Mean Glucose: {df['glucose_mean'].mean():.1f} mg/dL")
    print(f"Mean Time in Range (70-180 mg/dL): {df['time_in_range_pct'].mean():.1f}%")
    print(f"Mean Time in Hypoglycemia (<70 mg/dL): {df['time_hypo_pct'].mean():.1f}%")
    print(f"Mean Future 30m Hypoglycemia Risk (All): {df['future_30m_hypo_all_pct'].mean():.2f}%")
    print(f"Mean Future 30m Hypoglycemia Onset: {df['future_30m_hypo_onset_pct'].mean():.2f}%")
    print(f"Total 30m Hypoglycemia Onset Events: {df['future_30m_hypo_onset_count'].sum()}")
    
    # Save audit report to JSON
    out_dir = r"c:\Users\gupta\Desktop\GlycoTwin\artifacts\evaluation"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "phase0_data_audit.json")
    with open(out_file, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)
    print(f"Saved audit output to {out_file}")
