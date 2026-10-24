import React, { useEffect, useState } from 'react';
import { 
  Zap, 
  History, 
  HelpCircle, 
  AlertTriangle, 
  CheckCircle2, 
  Sliders, 
  TrendingDown, 
  ShieldAlert, 
  Sparkles,
  Info
} from 'lucide-react';
import { 
  fetchPatientPredictions, 
  postPredictionInference 
} from '../services/api';
import type { 
  HistoricalPredictionItem, 
  HistoricalPredictionResponse,
  InferenceResponse 
} from '../types/api';
import MetricCard from '../components/shared/MetricCard';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorAlert from '../components/shared/ErrorAlert';
import EmptyState from '../components/shared/EmptyState';
import PredictionTimelineChart from '../components/charts/PredictionTimelineChart';

interface PredictionsPageProps {
  currentPatientId: string;
}

// Preset feature sets for Mode B Forward Inference
const INFERENCE_PRESETS: Record<string, { label: string; desc: string; features: Record<string, number> }> = {
  rapid_fall: {
    label: 'Impending Drop (Rapid Decline)',
    desc: 'Current glucose 82 mg/dL, dropping at -1.2 mg/dL/min with recent bolus',
    features: {
      glucose_current: 82.0,
      glucose_lag_5m: 88.0,
      glucose_lag_10m: 94.0,
      glucose_lag_15m: 100.0,
      glucose_lag_30m: 118.0,
      glucose_lag_60m: 145.0,
      glucose_change_5m: -6.0,
      glucose_change_15m: -18.0,
      glucose_change_30m: -36.0,
      glucose_slope_15m: -1.2,
      glucose_slope_30m: -1.2,
      glucose_mean_15m: 91.0,
      glucose_mean_30m: 104.0,
      glucose_mean_60m: 125.0,
      glucose_std_30m: 14.5,
      glucose_std_60m: 22.0,
      glucose_min_30m: 82.0,
      glucose_max_30m: 118.0,
      hour_sin: 0.707,
      hour_cos: -0.707,
      weekday_sin: 0.43,
      weekday_cos: 0.90,
      recent_calories: 18.0,
      recent_steps: 120.0,
      recent_heart_rate: 88.0,
      recent_basal_rate: 0.08,
      recent_bolus_volume: 3.5,
      recent_carb_input: 0.0
    }
  },
  stable_euglycemia: {
    label: 'Stable Euglycemia',
    desc: 'Current glucose 120 mg/dL, stable trend within 70-180 mg/dL target',
    features: {
      glucose_current: 120.0,
      glucose_lag_5m: 122.0,
      glucose_lag_10m: 121.0,
      glucose_lag_15m: 123.0,
      glucose_lag_30m: 125.0,
      glucose_lag_60m: 128.0,
      glucose_change_5m: -2.0,
      glucose_change_15m: -3.0,
      glucose_change_30m: -5.0,
      glucose_slope_15m: -0.2,
      glucose_slope_30m: -0.16,
      glucose_mean_15m: 121.5,
      glucose_mean_30m: 123.0,
      glucose_mean_60m: 125.0,
      glucose_std_30m: 2.5,
      glucose_std_60m: 3.8,
      glucose_min_30m: 120.0,
      glucose_max_30m: 125.0,
      hour_sin: 0.5,
      hour_cos: 0.86,
      weekday_sin: 0.0,
      weekday_cos: 1.0,
      recent_calories: 12.0,
      recent_steps: 45.0,
      recent_heart_rate: 72.0,
      recent_basal_rate: 0.08,
      recent_bolus_volume: 0.0,
      recent_carb_input: 0.0
    }
  },
  impaired_counterreg: {
    label: 'Borderline Low Onset',
    desc: 'Current glucose 73 mg/dL, hovering near hypo cutoff with slow downward drift',
    features: {
      glucose_current: 73.0,
      glucose_lag_5m: 75.0,
      glucose_lag_10m: 76.0,
      glucose_lag_15m: 78.0,
      glucose_lag_30m: 82.0,
      glucose_lag_60m: 92.0,
      glucose_change_5m: -2.0,
      glucose_change_15m: -5.0,
      glucose_change_30m: -9.0,
      glucose_slope_15m: -0.33,
      glucose_slope_30m: -0.30,
      glucose_mean_15m: 75.5,
      glucose_mean_30m: 78.0,
      glucose_mean_60m: 84.0,
      glucose_std_30m: 3.5,
      glucose_std_60m: 6.8,
      glucose_min_30m: 73.0,
      glucose_max_30m: 82.0,
      hour_sin: -0.5,
      hour_cos: -0.86,
      weekday_sin: 0.78,
      weekday_cos: 0.62,
      recent_calories: 5.0,
      recent_steps: 10.0,
      recent_heart_rate: 64.0,
      recent_basal_rate: 0.08,
      recent_bolus_volume: 0.0,
      recent_carb_input: 0.0
    }
  },
  hypo_condition_violation: {
    label: 'Already Hypoglycemic (62 mg/dL)',
    desc: 'Demonstrates Task B conditional integrity: rejected if glucose < 70 mg/dL',
    features: {
      glucose_current: 62.0,
      glucose_lag_5m: 65.0,
      glucose_lag_10m: 68.0,
      glucose_lag_15m: 72.0,
      glucose_lag_30m: 85.0,
      glucose_lag_60m: 110.0,
      glucose_change_5m: -3.0,
      glucose_change_15m: -10.0,
      glucose_change_30m: -23.0,
      glucose_slope_15m: -0.66,
      glucose_slope_30m: -0.76,
      glucose_mean_15m: 67.0,
      glucose_mean_30m: 74.0,
      glucose_mean_60m: 88.0,
      glucose_std_30m: 9.5,
      glucose_std_60m: 16.0,
      glucose_min_30m: 62.0,
      glucose_max_30m: 85.0,
      hour_sin: 0.2,
      hour_cos: 0.98,
      weekday_sin: 0.0,
      weekday_cos: 1.0,
      recent_calories: 8.0,
      recent_steps: 20.0,
      recent_heart_rate: 78.0,
      recent_basal_rate: 0.08,
      recent_bolus_volume: 0.0,
      recent_carb_input: 0.0
    }
  }
};

export const Predictions: React.FC<PredictionsPageProps> = ({ currentPatientId }) => {
  // Mode selection: Mode A (Historical OOF) vs Mode B (Live Forward Inference)
  const [activeTab, setActiveTab] = useState<'historical' | 'inference'>('historical');

  // Task selection
  const [task, setTask] = useState<'task_b_impending_onset' | 'task_a_future_hypo'>('task_b_impending_onset');
  const [selectedModel, setSelectedModel] = useState<'rule_based' | 'logistic_regression' | 'xgboost'>('xgboost');

  // Mode A: Historical predictions state
  const [historicalData, setHistoricalData] = useState<HistoricalPredictionItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyLimit, setHistoryLimit] = useState<number>(30);

  // Mode B: Inference state
  const [selectedPresetKey, setSelectedPresetKey] = useState<string>('rapid_fall');
  const [activeFeatures, setActiveFeatures] = useState<Record<string, number>>(
    INFERENCE_PRESETS.rapid_fall.features
  );
  const [inferenceResult, setInferenceResult] = useState<InferenceResponse | null>(null);
  const [inferring, setInferring] = useState<boolean>(false);
  const [inferenceError, setInferenceError] = useState<string | null>(null);

  // Fetch Mode A historical predictions
  useEffect(() => {
    if (!currentPatientId) return;
    let isMounted = true;
    setLoadingHistory(true);
    setHistoryError(null);

    const taskQuery = task === 'task_b_impending_onset' ? 'onset' : 'risk';

    fetchPatientPredictions(currentPatientId, {
      task: taskQuery,
      model: selectedModel,
      limit: historyLimit
    })
      .then((res: HistoricalPredictionResponse) => {
        if (isMounted) {
          setHistoricalData(res.predictions);
          setLoadingHistory(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setHistoryError(err.message || 'Failed to load historical predictions');
          setLoadingHistory(false);
        }
      });

    return () => { isMounted = false; };
  }, [currentPatientId, task, selectedModel, historyLimit]);

  // Handle Preset selection change
  const handleSelectPreset = (key: string) => {
    setSelectedPresetKey(key);
    setActiveFeatures(INFERENCE_PRESETS[key].features);
    setInferenceResult(null);
    setInferenceError(null);
  };

  // Run Forward Inference
  const handleRunInference = async () => {
    setInferring(true);
    setInferenceError(null);
    setInferenceResult(null);

    const taskParam = task === 'task_b_impending_onset' ? 'onset' : 'risk';

    try {
      const response = await postPredictionInference({
        task: taskParam,
        model: selectedModel,
        features: activeFeatures,
        participant_id: currentPatientId
      });
      setInferenceResult(response);
    } catch (err: any) {
      setInferenceError(err.message || 'Inference execution failed');
    } finally {
      setInferring(false);
    }
  };

  // Calculate Mode A summary metrics from loaded batch
  const historicalSummary = React.useMemo(() => {
    if (!historicalData.length) return null;
    const avgProb = historicalData.reduce((acc, p) => acc + p.predicted_probability, 0) / historicalData.length;
    const alertCount = historicalData.filter(p => p.predicted_class === 1).length;
    const threshold = historicalData[0].operational_threshold;
    const trueEvents = historicalData.filter(p => p.true_target === 1).length;
    return {
      count: historicalData.length,
      avgProb: Math.round(avgProb * 1000) / 1000,
      alertRate: Math.round((alertCount / historicalData.length) * 100),
      threshold,
      trueEvents
    };
  }, [historicalData]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Glucose Predictions & Inference
            </h1>
            <span className="inline-flex items-center rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              30-Minute Horizon Forecasts
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Strict separation between Mode A (historical out-of-fold cross-validation) and Mode B (forward model deployment inference).
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setActiveTab('historical')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'historical'
                ? 'bg-white text-teal-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Mode A: Saved Historical Predictions
          </button>
          <button
            onClick={() => setActiveTab('inference')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'inference'
                ? 'bg-white text-teal-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            Mode B: Forward Research Inference
          </button>
        </div>
      </div>

      {/* Task & Model Control Bar */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Task Toggle Buttons */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
              Task Definition:
            </span>
            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
              <button
                onClick={() => setTask('task_b_impending_onset')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  task === 'task_b_impending_onset'
                    ? 'bg-white text-teal-900 shadow-xs ring-1 ring-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Task B: Impending Onset (g_t ≥ 70)
              </button>
              <button
                onClick={() => setTask('task_a_future_hypo')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  task === 'task_a_future_hypo'
                    ? 'bg-white text-teal-900 shadow-xs ring-1 ring-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Task A: Future Hypo Risk
              </button>
            </div>
          </div>

          {/* Model Selector */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Model:
            </span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as 'rule_based' | 'logistic_regression' | 'xgboost')}
              className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-800 focus:ring-teal-500"
            >
              <option value="xgboost">XGBoost (Champion GBDT)</option>
              <option value="logistic_regression">Logistic Regression (Calibrated)</option>
              <option value="rule_based">Rule-Based Clinical Baseline</option>
            </select>
          </div>
        </div>

        {/* Task Definition Alert Card */}
        <div className="mt-3.5 p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
          <div>
            {task === 'task_b_impending_onset' ? (
              <span>
                <strong>Task B (Impending Hypoglycaemia Onset):</strong> Predicts whether glucose will fall below 70 mg/dL within the next 30 minutes, <em>strictly conditioned on current glucose being ≥ 70 mg/dL</em>. This evaluates prevention rather than ongoing detection.
              </span>
            ) : (
              <span>
                <strong>Task A (Future Hypoglycaemia Risk):</strong> Unconditional prediction of whether any glucose measurement within the next 30 minutes will be &lt; 70 mg/dL, regardless of current glycemic state.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* MODE A: HISTORICAL PREDICTIONS VIEW */}
      {activeTab === 'historical' && (
        <div className="space-y-6">
          {historyError && (
            <ErrorAlert 
              title="Historical Prediction Query Error" 
              message={historyError} 
              onRetry={() => setLoadingHistory(true)} 
            />
          )}

          {/* Summary Metric Strip */}
          {historicalSummary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetricCard
                title="Historical OOF Batch"
                value={`${historicalSummary.count} records`}
                subtitle={`Participant: ${currentPatientId}`}
                badge={{ text: 'Retrospective', variant: 'neutral' }}
              />
              <MetricCard
                title="Operational Threshold"
                value={historicalSummary.threshold.toFixed(4)}
                subtitle="Calibrated 90% sensitivity"
                badge={{ text: 'Fixed Cutoff', variant: 'teal' }}
              />
              <MetricCard
                title="Model Mean Probability"
                value={(historicalSummary.avgProb * 100).toFixed(1) + '%'}
                subtitle={`Alert rate: ${historicalSummary.alertRate}%`}
                badge={{ text: selectedModel, variant: 'neutral' }}
              />
              <MetricCard
                title="Observed Positive Labels"
                value={`${historicalSummary.trueEvents} positive windows`}
                subtitle="Future target in 30m horizon"
                badge={{ text: 'Retrospective Label', variant: 'warning' }}
              />
            </div>
          )}

          {/* Historical Timeline Chart Card */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-teal-600" />
                  Out-of-Fold Forecast Probabilities Timeline
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Saved predictions from 5-fold cross-validation. Red markers denote ground-truth positive prediction windows.
                </p>
              </div>

              {/* Limit selector */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">Show latest:</span>
                <select
                  value={historyLimit}
                  onChange={(e) => setHistoryLimit(Number(e.target.value))}
                  className="bg-white border border-slate-300 rounded-md px-2 py-1 text-xs"
                >
                  <option value={15}>15 records</option>
                  <option value={30}>30 records</option>
                  <option value={60}>60 records</option>
                  <option value={100}>100 records</option>
                </select>
              </div>
            </div>

            {loadingHistory ? (
              <div className="h-72 flex items-center justify-center">
                <LoadingSkeleton lines={5} />
              </div>
            ) : historicalData.length === 0 ? (
              <EmptyState 
                title="No saved historical predictions" 
                description={`No cross-validation predictions found for ${currentPatientId} on ${task}.`} 
              />
            ) : (
              <div className="mt-4">
                <PredictionTimelineChart
                  data={historicalData}
                  threshold={historicalSummary?.threshold ?? 0.5}
                  height={320}
                />
              </div>
            )}
          </div>

          {/* Historical Records Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">
                Detailed Prediction Log (Chronological Sequence)
              </h3>
              <span className="text-xs text-slate-400">
                Provenance: Out-of-Fold 5-Fold Cross Validation
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Predicted Probability</th>
                    <th className="px-4 py-3">Operational Threshold</th>
                    <th className="px-4 py-3">Model Decision</th>
                    <th className="px-4 py-3">Observed Future Label (30m)</th>
                    <th className="px-4 py-3">CV Fold</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {historicalData.map((p, idx) => {
                    const isAlert = p.predicted_class === 1;
                    const isTrueEvent = p.true_target === 1;
                    return (
                      <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-4 py-2.5 font-mono text-slate-800">
                          {p.time.replace('T', ' ').slice(0, 19)}
                        </td>
                        <td className="px-4 py-2.5 font-mono font-semibold">
                          <div className="flex items-center gap-2">
                            <span>{(p.predicted_probability * 100).toFixed(1)}%</span>
                            <div className="w-16 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                              <div 
                                className={`h-full ${p.predicted_probability >= p.operational_threshold ? 'bg-rose-500' : 'bg-teal-500'}`} 
                                style={{ width: `${Math.min(100, p.predicted_probability * 100)}%` }} 
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-slate-500">
                          {p.operational_threshold.toFixed(4)}
                        </td>
                        <td className="px-4 py-2.5">
                          {isAlert ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                              Alert (Onset Risk)
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600">
                              Normal
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2.5">
                          {p.true_target !== null ? (
                            isTrueEvent ? (
                              <span className="inline-flex items-center gap-1 font-semibold text-rose-600">
                                <AlertTriangle className="w-3 h-3" />
                                Hypo Window (&lt;70 mg/dL)
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-slate-500">
                                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                Euglycemic Window
                              </span>
                            )
                          ) : (
                            <span className="text-slate-400 italic">Unlabeled</span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-slate-400">
                          Fold {p.cv_fold ?? '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODE B: FORWARD RESEARCH INFERENCE VIEW */}
      {activeTab === 'inference' && (
        <div className="space-y-6">
          {/* Preset Selector */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
              <Sliders className="w-4 h-4 text-teal-600" />
              Select Standard Clinical Simulation Preset
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(INFERENCE_PRESETS).map(([key, preset]) => {
                const isSelected = selectedPresetKey === key;
                return (
                  <button
                    key={key}
                    onClick={() => handleSelectPreset(key)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      isSelected
                        ? 'border-teal-500 bg-teal-50/50 ring-1 ring-teal-500'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-800">{preset.label}</span>
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500 line-clamp-2">{preset.desc}</p>
                    <div className="mt-2 text-[11px] font-mono text-slate-600 font-medium">
                      Glucose: {preset.features.glucose_current} mg/dL
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Interactive Feature Adjustment & Execution Form */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Feature Controls (2 Cols) */}
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-semibold text-slate-900">
                  Feature Vector (28 Manifest Features)
                </h3>
                <span className="text-xs text-slate-400">
                  Target-derived features strictly excluded
                </span>
              </div>

              {/* Key Feature Quick Sliders */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Current Glucose: <span className="font-mono text-teal-700">{activeFeatures.glucose_current} mg/dL</span>
                  </label>
                  <input
                    type="range"
                    min={40}
                    max={300}
                    step={1}
                    value={activeFeatures.glucose_current}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setActiveFeatures(prev => ({
                        ...prev,
                        glucose_current: val,
                        glucose_min_30m: Math.min(prev.glucose_min_30m, val),
                        glucose_max_30m: Math.max(prev.glucose_max_30m, val)
                      }));
                    }}
                    className="w-full mt-2 accent-teal-600"
                  />
                  {task === 'task_b_impending_onset' && activeFeatures.glucose_current < 70 && (
                    <p className="text-[11px] text-rose-600 font-semibold mt-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Task B Precondition Violation: Glucose must be ≥ 70 mg/dL.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    15-Minute Rate of Change (Slope): <span className="font-mono text-teal-700">{activeFeatures.glucose_slope_15m.toFixed(2)} mg/dL/min</span>
                  </label>
                  <input
                    type="range"
                    min={-3}
                    max={3}
                    step={0.1}
                    value={activeFeatures.glucose_slope_15m}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setActiveFeatures(prev => ({
                        ...prev,
                        glucose_slope_15m: val,
                        glucose_change_15m: val * 15.0
                      }));
                    }}
                    className="w-full mt-2 accent-teal-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Recent Bolus Volume: <span className="font-mono text-teal-700">{activeFeatures.recent_bolus_volume} U</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={25}
                    step={0.5}
                    value={activeFeatures.recent_bolus_volume}
                    onChange={(e) => {
                      const val = Math.max(0, Number(e.target.value));
                      setActiveFeatures(prev => ({ ...prev, recent_bolus_volume: val }));
                    }}
                    className="w-full mt-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Recent Carbohydrate Intake: <span className="font-mono text-teal-700">{activeFeatures.recent_carb_input} g</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={120}
                    step={5}
                    value={activeFeatures.recent_carb_input}
                    onChange={(e) => {
                      const val = Math.max(0, Number(e.target.value));
                      setActiveFeatures(prev => ({ ...prev, recent_carb_input: val }));
                    }}
                    className="w-full mt-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Target endpoint: <code className="font-mono text-slate-700">POST /api/predictions</code>
                </span>
                <button
                  onClick={handleRunInference}
                  disabled={inferring}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 text-white font-medium text-xs hover:bg-teal-700 disabled:opacity-50 shadow-xs transition-colors"
                >
                  <Zap className="w-4 h-4" />
                  {inferring ? 'Evaluating Feature Vector...' : 'Execute Forward Inference'}
                </button>
              </div>
            </div>

            {/* Inference Result Card (1 Col) */}
            <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  Inference Prediction Output
                </h3>

                {inferenceError && (
                  <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
                    <div className="font-semibold flex items-center gap-1.5 mb-1">
                      <ShieldAlert className="w-4 h-4 text-rose-600" />
                      Inference Rejected
                    </div>
                    {inferenceError}
                  </div>
                )}

                {inferenceResult && (
                  <div className="mt-4 space-y-4">
                    <div className="text-center p-4 bg-slate-50 rounded-xl border border-slate-200/80">
                      <div className="text-xs uppercase font-semibold text-slate-400">
                        Predicted Probability (30m Horizon)
                      </div>
                      <div className="mt-2 text-3xl font-extrabold text-slate-900 font-mono">
                        {(inferenceResult.predicted_probability * 100).toFixed(1)}%
                      </div>
                      <div className="mt-2">
                        {inferenceResult.predicted_class === 1 ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300">
                            Alert: High Onset Probability
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                            Low Onset Risk
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2 text-xs border-t border-slate-100 pt-3">
                      <div className="flex justify-between text-slate-600">
                        <span>Task:</span>
                        <strong className="font-mono text-slate-800">{inferenceResult.task}</strong>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Model:</span>
                        <strong className="font-mono text-slate-800">{inferenceResult.model}</strong>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Current Glucose:</span>
                        <strong className="font-mono text-slate-800">{inferenceResult.glucose_current} mg/dL</strong>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Operational Threshold:</span>
                        <strong className="font-mono text-slate-800">{inferenceResult.operational_threshold.toFixed(4)}</strong>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Feature Manifest:</span>
                        <span className="text-slate-500">{inferenceResult.feature_schema_version}</span>
                      </div>
                    </div>
                  </div>
                )}

                {!inferenceResult && !inferenceError && (
                  <div className="py-12 text-center text-xs text-slate-400">
                    <HelpCircle className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    Select a clinical preset and click "Execute Forward Inference" to evaluate the feature vector against the champion model.
                  </div>
                )}
              </div>

              {/* Research Prototype Disclaimer */}
              <div className="mt-6 p-3 bg-amber-50/70 border border-amber-200/70 rounded-lg text-[11px] text-amber-900 leading-tight">
                <strong>Notice:</strong> Research prototype inference. Not clinically certified for real-time treatment or automated insulin delivery adjustments.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Predictions;
