"""
GlycoTwin: Central Pipeline Configuration.
Defines parameters for dataset paths, feature engineering lookbacks,
target horizons, and output locations.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class PipelineConfig:
    # Directories
    workspace_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    dataset_dir: Optional[Path] = None
    output_dir: Path = field(default_factory=lambda: Path("data/processed"))
    artifacts_dir: Path = field(default_factory=lambda: Path("artifacts/evaluation"))
    sample_dir: Path = field(default_factory=lambda: Path("data/sample"))

    # Clinical / Prediction Parameters
    glucose_hypo_threshold: float = 70.0  # mg/dL
    glucose_severe_hypo_threshold: float = 54.0  # mg/dL
    prediction_horizon_minutes: int = 30  # 30-minute forward lookahead
    expected_sampling_interval_minutes: int = 5  # 5-minute nominal resolution

    # Feature Engineering Parameters
    lookback_window_minutes: int = 60  # Require at least 60m history for rolling stats
    lag_steps: List[int] = field(default_factory=lambda: [1, 2, 3, 6, 12])  # 5m, 10m, 15m, 30m, 60m
    rolling_windows: List[int] = field(default_factory=lambda: [3, 6, 12])  # 15m, 30m, 60m

    # Output file paths
    output_parquet_name: str = "glycotwin_features.parquet"
    output_csv_name: str = "glycotwin_features.csv"
    manifest_json_name: str = "phase1_feature_manifest.json"
    summary_json_name: str = "phase1_pipeline_summary.json"

    def get_dataset_dir(self) -> Path:
        """Finds HUPA-UCM dataset directory dynamically if not explicitly passed."""
        if self.dataset_dir and self.dataset_dir.exists():
            return self.dataset_dir.resolve()
        candidates = [
            self.workspace_root / "HUPA-UCM Diabetes Dataset",
            self.workspace_root / "data" / "raw" / "HUPA-UCM Diabetes Dataset"
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()
        raise FileNotFoundError(f"Could not locate HUPA-UCM dataset in candidates: {candidates}")

    def get_preprocessed_dir(self) -> Path:
        """Locates the preprocessed directory inside the dataset root."""
        base = self.get_dataset_dir()
        prep_candidates = list(base.rglob("Preprocessed"))
        if prep_candidates:
            return prep_candidates[0].resolve()
        raise FileNotFoundError(f"Could not find 'Preprocessed' folder inside {base}")

    @property
    def forward_steps(self) -> int:
        return self.prediction_horizon_minutes // self.expected_sampling_interval_minutes

    @property
    def min_history_steps(self) -> int:
        return self.lookback_window_minutes // self.expected_sampling_interval_minutes

DEFAULT_CONFIG = PipelineConfig()
