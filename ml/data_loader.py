"""
GlycoTwin: Data Loader Module.
Discovers and loads participant records from HUPA-UCM dataset files.
Enforces schema types, timestamp parsing, provenance tracking,
and participant boundary preservation.
"""
import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "time",
    "glucose",
    "calories",
    "heart_rate",
    "steps",
    "basal_rate",
    "bolus_volume_delivered",
    "carb_input"
]

NUMERICAL_COLUMNS = [
    "glucose",
    "calories",
    "heart_rate",
    "steps",
    "basal_rate",
    "bolus_volume_delivered",
    "carb_input"
]

class DataLoaderError(Exception):
    """Custom exception raised when file discovery or loading encounters a fatal error."""
    pass

def discover_participant_files(preprocessed_dir: Path, participant_pattern: str = "*.csv") -> List[Path]:
    """
    Discovers all candidate participant CSV files in the preprocessed directory.
    Does not hardcode specific IDs. Sorts files for deterministic loading.
    """
    if not preprocessed_dir.exists():
        raise DataLoaderError(f"Preprocessed directory does not exist: {preprocessed_dir}")

    files = sorted(list(preprocessed_dir.glob(participant_pattern)))
    if not files:
        raise DataLoaderError(f"No participant CSV files found matching '{participant_pattern}' in: {preprocessed_dir}")
    return files

def load_single_participant(file_path: Path) -> pd.DataFrame:
    """
    Loads and validates a single participant's continuous measurement CSV file.
    Non-destructive: Does not alter the original file.
    
    Returns DataFrame with:
        - participant_id: extracted from filename stem
        - parsed datetime 'time' column
        - validated numerical types for all required modalities
        - source_file: provenance metadata
    """
    if not file_path.exists():
        raise DataLoaderError(f"Participant file does not exist: {file_path}")

    pid = file_path.stem
    if not pid:
        raise DataLoaderError(f"Could not extract participant identifier from filename: {file_path}")

    try:
        # HUPA-UCM preprocessed files use semicolon delimiter
        df = pd.read_csv(file_path, sep=";")
    except Exception as e:
        raise DataLoaderError(f"Failed to read CSV file '{file_path}': {str(e)}") from e

    # Check required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataLoaderError(
            f"File '{file_path}' for participant '{pid}' is missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    # Parse timestamps
    try:
        df["time"] = pd.to_datetime(df["time"])
    except Exception as e:
        raise DataLoaderError(f"Failed to parse 'time' column as ISO-8601 timestamps in '{file_path}': {str(e)}") from e

    # Check for NaT timestamps
    if df["time"].isna().any():
        nat_count = int(df["time"].isna().sum())
        raise DataLoaderError(f"File '{file_path}' contains {nat_count} invalid (NaT) timestamps.")

    # Cast numerical columns
    for col in NUMERICAL_COLUMNS:
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
        except Exception as e:
            raise DataLoaderError(f"Non-numeric values found in column '{col}' of '{file_path}': {str(e)}") from e

    # Add metadata columns
    df["participant_id"] = pid
    df["source_file"] = file_path.name

    return df

def load_all_participants(preprocessed_dir: Path, participant_pattern: str = "*.csv") -> Dict[str, pd.DataFrame]:
    """
    Discovers and loads all participant files into a dictionary keyed by participant_id.
    Preserves participant boundaries without merging records.
    """
    files = discover_participant_files(preprocessed_dir, participant_pattern)
    cohort_data: Dict[str, pd.DataFrame] = {}

    for f in files:
        df = load_single_participant(f)
        pid = df["participant_id"].iloc[0]
        if pid in cohort_data:
            raise DataLoaderError(f"Duplicate participant ID '{pid}' detected across files: '{f}' and previous file.")
        cohort_data[pid] = df

    return cohort_data
