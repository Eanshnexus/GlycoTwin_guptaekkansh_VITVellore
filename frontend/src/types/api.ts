/**
 * GlycoTwin TypeScript API Definitions.
 * Aligns 1:1 with Phase 3 FastAPI Pydantic schemas.
 */

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unready';
  app_name: string;
  app_version: string;
  dataset_accessible: boolean;
  models_loaded: Record<string, boolean>;
  total_participants: number;
  total_observations: number;
  timestamp: string;
  details: {
    dataset_path: string;
    environment: string;
    audit_compliance: string;
  };
}

export interface MetadataResponse {
  project_name: string;
  dataset_name: string;
  dataset_provenance: string;
  total_participants: number;
  total_observations: number;
  prediction_horizon_minutes: number;
  hypoglycemia_threshold_mgdl: number;
  available_tasks: Record<string, string>;
  available_models: string[];
  feature_count: number;
  feature_names: string[];
  operational_thresholds: Record<string, Record<string, number>>;
  inference_support: {
    retrospective_cross_validation_evaluation: boolean;
    real_time_model_inference: boolean;
  };
  disclaimer: string;
}

export interface GlucoseStats {
  mean: number;
  std: number;
  min: number;
  max: number;
  tir_percentage: number; // Time In Range (70 - 180 mg/dL)
  tbr_percentage: number; // Time Below Range (< 70 mg/dL)
  tar_percentage: number; // Time Above Range (> 180 mg/dL)
}

export interface PatientListItem {
  participant_id: string;
  observation_count: number;
  start_time: string;
  end_time: string;
  duration_days: number;
  available_modalities: string[];
  has_historical_predictions: boolean;
}

export interface PatientListResponse {
  patients: PatientListItem[];
  pagination: PaginationMeta;
}

export interface PatientDetail {
  participant_id: string;
  observation_count: number;
  start_time: string;
  end_time: string;
  duration_days: number;
  glucose_stats: GlucoseStats;
  available_modalities: string[];
  has_historical_predictions: boolean;
  risk_predictions_count: number;
  onset_predictions_count: number;
}

export interface ObservationItem {
  time: string;
  glucose: number;
  calories: number | null;
  steps: number | null;
  heart_rate: number | null;
  basal_rate: number | null;
  bolus_volume: number | null;
  carb_input: number | null;
}

export interface ObservationResponse {
  participant_id: string;
  observations: ObservationItem[];
  pagination: PaginationMeta;
}

export interface HistoricalPredictionItem {
  participant_id: string;
  time: string;
  task: string;
  model: string;
  predicted_probability: number;
  predicted_class: number;
  operational_threshold: number;
  true_target: number | null;
  cv_fold: number | null;
  horizon_minutes: number;
  evaluation_type: string;
}

export interface HistoricalPredictionResponse {
  participant_id: string;
  task: string;
  predictions: HistoricalPredictionItem[];
  pagination: PaginationMeta;
}

export interface InferenceRequest {
  task: 'risk' | 'onset' | 'task_a_future_hypo' | 'task_b_impending_onset';
  model: 'rule_based' | 'logistic_regression' | 'xgboost';
  features: Record<string, number>;
  prediction_time?: string;
  participant_id?: string;
}

export interface InferenceResponse {
  task: string;
  model: string;
  prediction_time: string;
  horizon_minutes: number;
  glucose_current: number;
  predicted_probability: number;
  predicted_class: number;
  operational_threshold: number;
  feature_schema_version: string;
  inference_status: string;
  limitation_notice: string;
}

export interface MetricScoreSet {
  roc_auc: number | null;
  average_precision: number | null;
  f1_score: number | null;
  sensitivity: number | null;
  specificity: number | null;
  precision: number | null;
  brier_score: number | null;
}

export interface ModelEvaluationSummary {
  model: string;
  task: string;
  evaluation_method: string;
  sample_count: number;
  positive_count: number;
  negative_count: number;
  operational_threshold: number;
  pooled_metrics: MetricScoreSet;
  macro_metrics: Record<string, number | null>;
  notes: string;
}

export interface EvaluationResponse {
  task: string;
  target_column: string;
  models: ModelEvaluationSummary[];
  caveats: string[];
}

export interface PersonalisationItem {
  participant_id: string;
  adaptation_status: string;
  calib_rows_total: number;
  calib_rows_purged: number;
  calib_rows_usable: number;
  calib_positives: number;
  eval_rows: number;
  eval_positives: number;
  t_pop: number;
  t_pers: number;
  pop_roc_auc: number | null;
  pers_roc_auc: number | null;
  delta_roc_auc: number | null;
  pop_avg_prec: number | null;
  pers_avg_prec: number | null;
  delta_avg_prec: number | null;
  pop_f1: number | null;
  pers_f1: number | null;
  delta_f1: number | null;
  pop_brier: number | null;
  pers_brier: number | null;
  delta_brier: number | null;
}

export interface PersonalisationResponse {
  task: string;
  adaptation_method: string;
  purge_gap_minutes: number;
  total_participants: number;
  successful_adaptations: number;
  fallback_adaptations: number;
  participants: PersonalisationItem[];
  summary_deltas: {
    mean_delta_brier: number;
    mean_delta_roc_auc: number;
    mean_delta_f1: number;
    participants_improved_brier: number;
  };
  caveats: string[];
}
