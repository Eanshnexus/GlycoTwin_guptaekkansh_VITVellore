"""
GlycoTwin: Feature Engineering Module.
Constructs causal, strictly backward-looking features using measurements
available at or before prediction time t.

Feature Groups:
1. Current State: glucose_current
2. Glucose Lags: 5m, 10m, 15m, 30m, 60m
3. Glucose Trends: changes and slopes over 5m, 15m, 30m
4. Rolling Glucose Stats: mean, std, min, max over 15m, 30m, 60m
5. Circadian / Temporal: hour_sin, hour_cos, weekday_sin, weekday_cos
6. Contextual Wearables & CSII: rolling calories, steps, heart rate, active basal,
   cumulative bolus, cumulative carbohydrates over 30m/60m causal windows.
"""
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd

# Explicit list of model feature names (excludes metadata like participant_id, time, labels)
FEATURE_COLUMNS: List[str] = [
    # Current state
    "glucose_current",
    # Lags
    "glucose_lag_5m",
    "glucose_lag_10m",
    "glucose_lag_15m",
    "glucose_lag_30m",
    "glucose_lag_60m",
    # Trends
    "glucose_change_5m",
    "glucose_change_15m",
    "glucose_change_30m",
    "glucose_slope_15m",
    "glucose_slope_30m",
    # Rolling stats
    "glucose_mean_15m",
    "glucose_mean_30m",
    "glucose_mean_60m",
    "glucose_std_30m",
    "glucose_std_60m",
    "glucose_min_30m",
    "glucose_max_30m",
    # Time features
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    # Contextual features
    "recent_calories",
    "recent_steps",
    "recent_heart_rate",
    "recent_basal_rate",
    "recent_bolus_volume",
    "recent_carb_input"
]

METADATA_COLUMNS: List[str] = [
    "participant_id",
    "time",
    "source_file"
]

def compute_participant_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes backward-looking feature vector for a single participant's time series.
    Assumes df is sorted chronologically at 5-minute nominal resolution.
    
    Leakage Prevention:
    - All lags use shift(positive_k) -> observation at t-k.
    - All rolling windows are right-aligned (only includes past intervals up to t).
    - No centred rolling windows or negative shifts are ever used.
    """
    res = pd.DataFrame(index=df.index)
    
    # Preserve metadata
    for meta in METADATA_COLUMNS:
        if meta in df.columns:
            res[meta] = df[meta]

    g = df["glucose"]

    # 1. Current State
    res["glucose_current"] = g

    # 2. Glucose Lags (1 step = 5m, 2 = 10m, 3 = 15m, 6 = 30m, 12 = 60m)
    res["glucose_lag_5m"] = g.shift(1)
    res["glucose_lag_10m"] = g.shift(2)
    res["glucose_lag_15m"] = g.shift(3)
    res["glucose_lag_30m"] = g.shift(6)
    res["glucose_lag_60m"] = g.shift(12)

    # 3. Glucose Trends
    res["glucose_change_5m"] = g - res["glucose_lag_5m"]
    res["glucose_change_15m"] = g - res["glucose_lag_15m"]
    res["glucose_change_30m"] = g - res["glucose_lag_30m"]
    res["glucose_slope_15m"] = res["glucose_change_15m"] / 15.0  # mg/dL per min
    res["glucose_slope_30m"] = res["glucose_change_30m"] / 30.0  # mg/dL per min

    # 4. Rolling Glucose Stats (closed='right' by default, strictly past observations)
    res["glucose_mean_15m"] = g.rolling(window=3, min_periods=3).mean()
    res["glucose_mean_30m"] = g.rolling(window=6, min_periods=6).mean()
    res["glucose_mean_60m"] = g.rolling(window=12, min_periods=12).mean()

    res["glucose_std_30m"] = g.rolling(window=6, min_periods=6).std()
    res["glucose_std_60m"] = g.rolling(window=12, min_periods=12).std()

    res["glucose_min_30m"] = g.rolling(window=6, min_periods=6).min()
    res["glucose_max_30m"] = g.rolling(window=6, min_periods=6).max()

    # 5. Temporal Circadian Features
    hour_val = df["time"].dt.hour + df["time"].dt.minute / 60.0
    res["hour_sin"] = np.sin(2 * np.pi * hour_val / 24.0)
    res["hour_cos"] = np.cos(2 * np.pi * hour_val / 24.0)

    weekday_val = df["time"].dt.weekday
    res["weekday_sin"] = np.sin(2 * np.pi * weekday_val / 7.0)
    res["weekday_cos"] = np.cos(2 * np.pi * weekday_val / 7.0)

    # 6. Contextual Features
    # Calories: rolling 30-min expenditure
    if "calories" in df.columns:
        res["recent_calories"] = df["calories"].rolling(window=6, min_periods=1).sum()
    else:
        res["recent_calories"] = 0.0

    # Steps: rolling 30-min total steps
    if "steps" in df.columns:
        res["recent_steps"] = df["steps"].rolling(window=6, min_periods=1).sum()
    else:
        res["recent_steps"] = 0.0

    # Heart Rate: rolling 30-min mean bpm
    if "heart_rate" in df.columns:
        res["recent_heart_rate"] = df["heart_rate"].rolling(window=6, min_periods=1).mean()
    else:
        res["recent_heart_rate"] = 0.0

    # Basal Rate: instantaneous active delivery at time t
    if "basal_rate" in df.columns:
        res["recent_basal_rate"] = df["basal_rate"]
    else:
        res["recent_basal_rate"] = 0.0

    # Bolus Insulin: cumulative delivered over past 60 min (12 steps)
    if "bolus_volume_delivered" in df.columns:
        res["recent_bolus_volume"] = df["bolus_volume_delivered"].rolling(window=12, min_periods=1).sum()
    else:
        res["recent_bolus_volume"] = 0.0

    # Carbohydrate Input: cumulative consumed over past 60 min (12 steps)
    if "carb_input" in df.columns:
        res["recent_carb_input"] = df["carb_input"].rolling(window=12, min_periods=1).sum()
    else:
        res["recent_carb_input"] = 0.0

    return res

def build_feature_manifest() -> Dict[str, Any]:
    """Generates the machine-readable Phase 1 feature manifest metadata."""
    manifest = {
        "pipeline_version": "1.0.0",
        "total_features": len(FEATURE_COLUMNS),
        "feature_list": FEATURE_COLUMNS,
        "features": {
            "glucose_current": {
                "definition": "Instantaneous CGM reading at prediction time t",
                "lookback_minutes": 0,
                "source_column": "glucose",
                "units": "mg/dL",
                "category": "current_state",
                "allowed_in_initial_model": True
            },
            "glucose_lag_5m": {"definition": "Glucose at t - 5 min", "lookback_minutes": 5, "units": "mg/dL", "category": "lag", "allowed_in_initial_model": True},
            "glucose_lag_10m": {"definition": "Glucose at t - 10 min", "lookback_minutes": 10, "units": "mg/dL", "category": "lag", "allowed_in_initial_model": True},
            "glucose_lag_15m": {"definition": "Glucose at t - 15 min", "lookback_minutes": 15, "units": "mg/dL", "category": "lag", "allowed_in_initial_model": True},
            "glucose_lag_30m": {"definition": "Glucose at t - 30 min", "lookback_minutes": 30, "units": "mg/dL", "category": "lag", "allowed_in_initial_model": True},
            "glucose_lag_60m": {"definition": "Glucose at t - 60 min", "lookback_minutes": 60, "units": "mg/dL", "category": "lag", "allowed_in_initial_model": True},
            "glucose_change_5m": {"definition": "Glucose delta G(t) - G(t-5m)", "lookback_minutes": 5, "units": "mg/dL", "category": "trend", "allowed_in_initial_model": True},
            "glucose_change_15m": {"definition": "Glucose delta G(t) - G(t-15m)", "lookback_minutes": 15, "units": "mg/dL", "category": "trend", "allowed_in_initial_model": True},
            "glucose_change_30m": {"definition": "Glucose delta G(t) - G(t-30m)", "lookback_minutes": 30, "units": "mg/dL", "category": "trend", "allowed_in_initial_model": True},
            "glucose_slope_15m": {"definition": "Glucose rate of change over 15 min", "lookback_minutes": 15, "units": "mg/dL/min", "category": "trend", "allowed_in_initial_model": True},
            "glucose_slope_30m": {"definition": "Glucose rate of change over 30 min", "lookback_minutes": 30, "units": "mg/dL/min", "category": "trend", "allowed_in_initial_model": True},
            "glucose_mean_15m": {"definition": "Rolling mean glucose over past 15 min", "lookback_minutes": 15, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_mean_30m": {"definition": "Rolling mean glucose over past 30 min", "lookback_minutes": 30, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_mean_60m": {"definition": "Rolling mean glucose over past 60 min", "lookback_minutes": 60, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_std_30m": {"definition": "Rolling glucose standard deviation over past 30 min", "lookback_minutes": 30, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_std_60m": {"definition": "Rolling glucose standard deviation over past 60 min", "lookback_minutes": 60, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_min_30m": {"definition": "Rolling minimum glucose over past 30 min", "lookback_minutes": 30, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "glucose_max_30m": {"definition": "Rolling maximum glucose over past 30 min", "lookback_minutes": 30, "units": "mg/dL", "category": "rolling_stats", "allowed_in_initial_model": True},
            "hour_sin": {"definition": "Sine of 24h diurnal cycle", "lookback_minutes": 0, "units": "unitless [-1, 1]", "category": "time", "allowed_in_initial_model": True},
            "hour_cos": {"definition": "Cosine of 24h diurnal cycle", "lookback_minutes": 0, "units": "unitless [-1, 1]", "category": "time", "allowed_in_initial_model": True},
            "weekday_sin": {"definition": "Sine of 7-day weekly cycle", "lookback_minutes": 0, "units": "unitless [-1, 1]", "category": "time", "allowed_in_initial_model": True},
            "weekday_cos": {"definition": "Cosine of 7-day weekly cycle", "lookback_minutes": 0, "units": "unitless [-1, 1]", "category": "time", "allowed_in_initial_model": True},
            "recent_calories": {"definition": "Cumulative calories burned in past 30 min", "lookback_minutes": 30, "units": "kcal", "category": "contextual", "allowed_in_initial_model": True},
            "recent_steps": {"definition": "Cumulative steps taken in past 30 min", "lookback_minutes": 30, "units": "steps", "category": "contextual", "allowed_in_initial_model": True},
            "recent_heart_rate": {"definition": "Mean heart rate over past 30 min", "lookback_minutes": 30, "units": "bpm", "category": "contextual", "allowed_in_initial_model": True},
            "recent_basal_rate": {"definition": "Active basal insulin delivery at time t", "lookback_minutes": 0, "units": "U/5-min", "category": "contextual", "allowed_in_initial_model": True},
            "recent_bolus_volume": {"definition": "Cumulative bolus insulin delivered in past 60 min", "lookback_minutes": 60, "units": "Units", "category": "contextual", "allowed_in_initial_model": True},
            "recent_carb_input": {"definition": "Cumulative carbohydrate mass logged in past 60 min", "lookback_minutes": 60, "units": "Grams", "category": "contextual", "allowed_in_initial_model": True}
        }
    }
    return manifest
