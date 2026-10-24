"""
GlycoTwin: Phase 1 Data Pipeline Execution Script.
Coordinates the end-to-end execution of:
1. Data discovery and loading (ml/data_loader.py)
2. Quality and physiological validation (ml/validate_data.py)
3. Conservative cleaning and sorting (ml/preprocess.py)
4. Causal feature engineering (ml/build_features.py)
5. Horizon label construction (ml/create_labels.py)
6. Saving modelling dataset (Parquet + CSV) and artifact summaries.

Usage:
    python -m ml.run_pipeline [--dataset-dir PATH] [--output-dir PATH] [--artifacts-dir PATH]
"""
import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from ml.config import PipelineConfig, DEFAULT_CONFIG
from ml.data_loader import load_all_participants
from ml.validate_data import validate_cohort
from ml.preprocess import preprocess_cohort
from ml.build_features import compute_participant_features, build_feature_manifest, FEATURE_COLUMNS, METADATA_COLUMNS
from ml.create_labels import create_future_hypo_labels

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GlycoTwin Phase 1 Data & Feature Pipeline")
    parser.add_argument("--dataset-dir", type=str, default=None, help="Path to HUPA-UCM dataset root")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for processed data")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts/evaluation", help="Directory for evaluation artifacts")
    parser.add_argument("--save-csv", action="store_true", default=True, help="Also export CSV copy alongside Parquet")
    parser.add_argument("--participant-limit", type=int, default=None, help="Optional limit for rapid testing")
    return parser.parse_args()

def run_phase1_pipeline(config: PipelineConfig, save_csv: bool = True, participant_limit: int = None) -> Dict[str, Any]:
    start_time = time.time()
    print("=" * 70)
    print("GLYCOTWIN PHASE 1: DATA PIPELINE & FEATURE ENGINEERING")
    print("=" * 70)

    # 1. Paths and Discovery
    dataset_dir = config.get_dataset_dir()
    prep_dir = config.get_preprocessed_dir()
    output_dir = config.workspace_root / config.output_dir
    artifacts_dir = config.workspace_root / config.artifacts_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset root:       {dataset_dir}")
    print(f"Preprocessed path:  {prep_dir}")
    print(f"Output directory:   {output_dir}")
    print(f"Artifacts directory: {artifacts_dir}")

    # 2. Loading
    print("\n[Step 1/5] Loading participant files...")
    raw_cohort = load_all_participants(prep_dir)
    total_raw_participants = len(raw_cohort)
    total_raw_rows = sum(len(df) for df in raw_cohort.values())
    print(f"Loaded {total_raw_participants} participant files ({total_raw_rows:,} total rows).")

    if participant_limit and participant_limit > 0:
        pids = list(raw_cohort.keys())[:participant_limit]
        raw_cohort = {p: raw_cohort[p] for p in pids}
        print(f"Note: Applied participant limit filter -> processing first {len(raw_cohort)} participants.")

    # 3. Validation
    print("\n[Step 2/5] Validating cohort schema and sampling intervals...")
    val_report = validate_cohort(raw_cohort, expected_interval_minutes=config.expected_sampling_interval_minutes)
    print(f"Validation status:  {'PASSED' if val_report['cohort_validation_passed'] else 'FAILED'}")
    print(f"Total validation errors:   {val_report['total_errors']}")
    print(f"Total validation warnings: {val_report['total_warnings']}")

    # 4. Preprocessing
    print("\n[Step 3/5] Preprocessing and sorting observations...")
    clean_cohort, prep_summary = preprocess_cohort(raw_cohort)
    print(f"Preprocessing completed: {prep_summary['total_output_rows']:,} rows retained ({prep_summary['total_excluded_rows']} excluded).")

    # 5. Feature Engineering & Label Creation
    print("\n[Step 4/5] Computing causal features and 30-min horizon labels...")
    processed_dfs: List[pd.DataFrame] = []
    per_participant_stats: List[Dict[str, Any]] = []

    total_valid_windows = 0
    total_pos_labels = 0
    total_neg_labels = 0
    total_onset_events = 0

    for pid, df in clean_cohort.items():
        # Compute backward-looking features
        feats_df = compute_participant_features(df)
        
        # Compute forward-looking labels
        labels_df = create_future_hypo_labels(
            df,
            threshold=config.glucose_hypo_threshold,
            horizon_minutes=config.prediction_horizon_minutes,
            expected_interval_minutes=config.expected_sampling_interval_minutes
        )

        # Merge features and labels
        combined = pd.concat([feats_df, labels_df], axis=1)

        # Eligibility flags
        # History requirement: all feature columns must be non-null (excludes first 12 steps / 60 min)
        feature_eligible = combined[FEATURE_COLUMNS].notna().all(axis=1)
        target_eligible = combined["target_eligible"] == True
        combined["is_modelling_eligible"] = feature_eligible & target_eligible

        # Statistics
        n_p_rows = len(combined)
        n_eligible = int(combined["is_modelling_eligible"].sum())
        p_targets = combined.loc[combined["is_modelling_eligible"], "target_hypo_30m"]
        p_pos = int((p_targets == 1).sum())
        p_neg = int((p_targets == 0).sum())
        p_onsets = int((combined.loc[combined["is_modelling_eligible"], "is_hypo_onset_30m"] == 1).sum())

        total_valid_windows += n_eligible
        total_pos_labels += p_pos
        total_neg_labels += p_neg
        total_onset_events += p_onsets

        per_participant_stats.append({
            "participant_id": pid,
            "raw_rows": n_p_rows,
            "modelling_eligible_windows": n_eligible,
            "excluded_warmup_windows": int((~feature_eligible & target_eligible).sum()),
            "excluded_terminal_windows": int((feature_eligible & ~target_eligible).sum()),
            "positive_labels": p_pos,
            "negative_labels": p_neg,
            "positive_prevalence_pct": round(p_pos / n_eligible * 100.0, 2) if n_eligible > 0 else 0.0,
            "onset_events": p_onsets
        })

        processed_dfs.append(combined)

    # Combine into single modelling dataset
    modelling_dataset = pd.concat(processed_dfs, ignore_index=True)
    print(f"Modelling dataset assembled: {len(modelling_dataset):,} total rows, {total_valid_windows:,} modelling-eligible windows.")
    print(f"Positive labels (Hypo within 30m): {total_pos_labels:,} ({total_pos_labels/total_valid_windows*100:.2f}%)")
    print(f"Negative labels:                   {total_neg_labels:,} ({total_neg_labels/total_valid_windows*100:.2f}%)")
    print(f"Impending onset events:            {total_onset_events:,}")

    # 6. Save Datasets
    print("\n[Step 5/5] Exporting datasets and artifacts...")
    parquet_path = output_dir / config.output_parquet_name
    modelling_dataset.to_parquet(parquet_path, index=False, engine="pyarrow")
    print(f"Saved Parquet dataset: {parquet_path} ({parquet_path.stat().st_size / (1024*1024):.1f} MB)")

    if save_csv:
        csv_path = output_dir / config.output_csv_name
        modelling_dataset.to_csv(csv_path, index=False)
        print(f"Saved CSV dataset:     {csv_path} ({csv_path.stat().st_size / (1024*1024):.1f} MB)")

    # Save feature manifest
    manifest = build_feature_manifest()
    manifest_path = artifacts_dir / config.manifest_json_name
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved Feature Manifest: {manifest_path}")

    # Save pipeline summary
    elapsed_time = round(time.time() - start_time, 2)
    summary_report = {
        "pipeline_version": "1.0.0",
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": elapsed_time,
        "source_preprocessed_dir": str(prep_dir),
        "total_participants": len(clean_cohort),
        "total_input_observations": total_raw_rows,
        "total_output_rows": len(modelling_dataset),
        "total_modelling_eligible_windows": total_valid_windows,
        "positive_labels_count": total_pos_labels,
        "negative_labels_count": total_neg_labels,
        "positive_prevalence_pct": round(total_pos_labels / total_valid_windows * 100.0, 2),
        "onset_hypo_events_count": total_onset_events,
        "feature_count": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "metadata_columns": METADATA_COLUMNS + ["target_hypo_30m", "target_eligible", "future_min_glucose_30m", "is_hypo_onset_30m", "is_modelling_eligible"],
        "configuration": {
            "glucose_hypo_threshold_mg_dl": config.glucose_hypo_threshold,
            "prediction_horizon_minutes": config.prediction_horizon_minutes,
            "expected_sampling_interval_minutes": config.expected_sampling_interval_minutes,
            "lookback_window_minutes": config.lookback_window_minutes
        },
        "software_versions": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__
        },
        "per_participant_breakdown": per_participant_stats
    }

    summary_path = artifacts_dir / config.summary_json_name
    with open(summary_path, "w") as f:
        json.dump(summary_report, f, indent=2)
    print(f"Saved Pipeline Summary: {summary_path}")

    print("\n" + "=" * 70)
    print(f"PHASE 1 PIPELINE EXECUTION SUCCESSFUL (Elapsed: {elapsed_time}s)")
    print("=" * 70)
    return summary_report

if __name__ == "__main__":
    args = parse_args()
    cfg = PipelineConfig(
        dataset_dir=Path(args.dataset_dir) if args.dataset_dir else None,
        output_dir=Path(args.output_dir),
        artifacts_dir=Path(args.artifacts_dir)
    )
    run_phase1_pipeline(cfg, save_csv=args.save_csv, participant_limit=args.participant_limit)
