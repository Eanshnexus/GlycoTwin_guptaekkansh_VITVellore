"""
GlycoTwin: Baseline Models Module.
Implements:
1. Baseline A: Explicit physiological rule-based trajectory heuristic.
2. Baseline B: Standardized Regularized Logistic Regression in a leak-free Pipeline.
"""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

class RuleBasedHypoBaseline:
    """
    A clinical rule-based reference baseline using only information available at prediction time t:
    - Current interstitial glucose G(t)
    - 15-minute rate of change / slope (mg/dL/min)
    
    Formula:
        Projected glucose at t+15 min: G_proj = G(t) + 15 * slope_15m
        Continuous risk score = 1 / (1 + exp((G_proj - 75) / 10))
    """
    def __init__(self, target_threshold: float = 70.0):
        self.target_threshold = target_threshold

    def fit(self, X: pd.DataFrame, y: np.ndarray = None):
        # Rule-based model requires no training parameters
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        g = X["glucose_current"].values
        slope = X["glucose_slope_15m"].values if "glucose_slope_15m" in X.columns else np.zeros_like(g)
        
        # 15-minute linear forward projection based on past rate of change
        g_proj = g + 15.0 * slope
        # Logistic sigmoid mapped around 75 mg/dL with temperature 10.0
        z = (75.0 - g_proj) / 10.0
        # Clip to prevent numerical overflow
        z = np.clip(z, -20.0, 20.0)
        p1 = 1.0 / (1.0 + np.exp(-z))
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)

def build_logistic_regression_pipeline(
    C: float = 1.0,
    class_weight: str = "balanced",
    random_state: int = 42
) -> Pipeline:
    """
    Builds a leak-free scikit-learn Pipeline with StandardScaler and regularized LogisticRegression.
    """
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            penalty="l2",
            C=C,
            solver="lbfgs",
            max_iter=1000,
            class_weight=class_weight,
            random_state=random_state
        ))
    ])
    return pipeline
