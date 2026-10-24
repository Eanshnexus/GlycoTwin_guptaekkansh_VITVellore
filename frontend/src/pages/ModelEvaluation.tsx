import React, { useEffect, useState, useMemo } from 'react';
import { 
  Target, 
  Layers, 
  ShieldAlert,
  Info
} from 'lucide-react';
import { fetchModelEvaluation } from '../services/api';
import type { EvaluationResponse, ModelEvaluationSummary } from '../types/api';
import MetricCard from '../components/shared/MetricCard';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorAlert from '../components/shared/ErrorAlert';
import EmptyState from '../components/shared/EmptyState';

export const ModelEvaluation: React.FC = () => {
  const [task, setTask] = useState<'task_b_impending_onset' | 'task_a_future_hypo'>('task_b_impending_onset');
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModelName, setSelectedModelName] = useState<string>('xgboost');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const taskParam = task === 'task_b_impending_onset' ? 'onset' : 'risk';

    fetchModelEvaluation(taskParam)
      .then((res: EvaluationResponse) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || 'Failed to load model evaluation metrics');
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [task]);

  const selectedModelData = useMemo(() => {
    if (!data) return null;
    return data.models.find((m: ModelEvaluationSummary) => m.model === selectedModelName) || data.models[0];
  }, [data, selectedModelName]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Model Evaluation & Benchmarking
            </h1>
            <span className="inline-flex items-center rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              5-Fold Cross Validation
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Authoritative clinical machine-learning benchmarks comparing rule-based, logistic regression, and XGBoost architectures.
          </p>
        </div>

        {/* Task Tabs */}
        <div className="inline-flex rounded-xl border border-slate-200 p-1 bg-slate-100">
          <button
            onClick={() => setTask('task_b_impending_onset')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              task === 'task_b_impending_onset'
                ? 'bg-white text-teal-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Task B: Impending Onset (g_t ≥ 70)
          </button>
          <button
            onClick={() => setTask('task_a_future_hypo')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              task === 'task_a_future_hypo'
                ? 'bg-white text-teal-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Task A: Future Hypo Risk
          </button>
        </div>
      </div>

      {error && (
        <ErrorAlert 
          title="Evaluation Service Error" 
          message={error} 
          onRetry={() => setLoading(true)} 
        />
      )}

      {/* Task Definition Summary Card */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-slate-900">
              {task === 'task_b_impending_onset' 
                ? 'Primary Research Benchmark: Task B (Impending Hypoglycaemia Onset)' 
                : 'Secondary Benchmark: Task A (Future Hypoglycaemia Risk)'}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {task === 'task_b_impending_onset' ? (
                <>
                  Strictly evaluated on records where <strong>current glucose is ≥ 70 mg/dL</strong>, testing whether the digital twin can foresee imminent glucose collapse across the next 30 minutes. Prevents trivial inflation from ongoing hypoglycemia episodes.
                </>
              ) : (
                <>
                  Evaluates 30-minute forward hypoglycemia risk across all available continuous monitoring timestamps, including periods where the participant is already in hypoglycemia.
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <LoadingSkeleton lines={2} />
            <LoadingSkeleton lines={2} />
            <LoadingSkeleton lines={2} />
            <LoadingSkeleton lines={2} />
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <LoadingSkeleton lines={5} />
          </div>
        </div>
      ) : data ? (
        <>
          {/* Champion Model Performance Highlights */}
          {selectedModelData && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetricCard
                title="Pooled ROC-AUC"
                value={selectedModelData.pooled_metrics.roc_auc != null ? selectedModelData.pooled_metrics.roc_auc.toFixed(4) : 'N/A'}
                subtitle={`Macro: ${selectedModelData.macro_metrics.roc_auc != null ? selectedModelData.macro_metrics.roc_auc.toFixed(4) : 'N/A'}`}
                badge={{ text: selectedModelData.model, variant: 'teal' }}
              />
              <MetricCard
                title="Average Precision (PR-AUC)"
                value={selectedModelData.pooled_metrics.average_precision != null ? selectedModelData.pooled_metrics.average_precision.toFixed(4) : 'N/A'}
                subtitle={`Macro: ${selectedModelData.macro_metrics.average_precision != null ? selectedModelData.macro_metrics.average_precision.toFixed(4) : 'N/A'}`}
                badge={{ text: 'PR-Curve Area', variant: 'teal' }}
              />
              <MetricCard
                title="Brier Calibration Score"
                value={selectedModelData.pooled_metrics.brier_score != null ? selectedModelData.pooled_metrics.brier_score.toFixed(4) : 'N/A'}
                subtitle="Mean squared error of probabilities"
                badge={{ text: 'Calibration', variant: 'neutral' }}
              />
              <MetricCard
                title="Operational Sensitivity"
                value={selectedModelData.pooled_metrics.sensitivity != null ? (selectedModelData.pooled_metrics.sensitivity * 100).toFixed(1) + '%' : 'N/A'}
                subtitle={`At cutoff t = ${selectedModelData.operational_threshold.toFixed(4)}`}
                badge={{ text: 'Calibrated Cutoff', variant: 'warning' }}
              />
            </div>
          )}

          {/* Model Architecture Comparison Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Comprehensive Architecture Comparison (5-Fold Cross Validation)
                </h3>
                <p className="text-xs text-slate-500">
                  Direct comparison across verified rule-based, linear, and gradient-boosted models
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                Method: 5-Fold GroupKFold CV
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">Architecture</th>
                    <th className="px-4 py-3">ROC-AUC (Pooled)</th>
                    <th className="px-4 py-3">PR-AUC (Avg Prec)</th>
                    <th className="px-4 py-3">Sensitivity (Recall)</th>
                    <th className="px-4 py-3">Specificity</th>
                    <th className="px-4 py-3">Precision</th>
                    <th className="px-4 py-3">F1-Score</th>
                    <th className="px-4 py-3">Brier Score</th>
                    <th className="px-4 py-3">Op Threshold</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {data.models.map((m: ModelEvaluationSummary) => {
                    const isXgb = m.model === 'xgboost';
                    const isSelected = m.model === selectedModelName;
                    return (
                      <tr 
                        key={m.model}
                        onClick={() => setSelectedModelName(m.model)}
                        className={`cursor-pointer transition-colors ${
                          isSelected 
                            ? 'bg-teal-50/60 font-medium' 
                            : 'hover:bg-slate-50/70'
                        }`}
                      >
                        <td className="px-4 py-3 font-semibold flex items-center gap-2">
                          <span className="font-mono text-slate-900">
                            {m.model === 'xgboost' && 'XGBoost (Champion GBDT)'}
                            {m.model === 'logistic_regression' && 'Logistic Regression'}
                            {m.model === 'rule_based' && 'Rule-Based Baseline'}
                          </span>
                          {isXgb && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-sm bg-teal-100 text-teal-800 text-[10px] font-bold">
                              Champion
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">
                          {m.pooled_metrics.roc_auc != null ? m.pooled_metrics.roc_auc.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono font-semibold text-teal-800">
                          {m.pooled_metrics.average_precision != null ? m.pooled_metrics.average_precision.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {m.pooled_metrics.sensitivity != null ? `${(m.pooled_metrics.sensitivity * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {m.pooled_metrics.specificity != null ? `${(m.pooled_metrics.specificity * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {m.pooled_metrics.precision != null ? `${(m.pooled_metrics.precision * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {m.pooled_metrics.f1_score != null ? m.pooled_metrics.f1_score.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-600">
                          {m.pooled_metrics.brier_score != null ? m.pooled_metrics.brier_score.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-500">
                          {m.operational_threshold.toFixed(4)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model Breakdown: Sample Counts & Macro-Averaging */}
          {selectedModelData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Sample Breakdown Card */}
              <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Target className="w-4 h-4 text-teal-600" />
                    Evaluation Sample Breakdown ({selectedModelData.model})
                  </h3>
                  <span className="text-xs font-mono text-slate-500">
                    Cutoff: {selectedModelData.operational_threshold.toFixed(4)}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-center">
                  <div className="bg-teal-50/60 border border-teal-200 rounded-xl p-4">
                    <div className="text-[11px] font-semibold text-teal-800 uppercase tracking-wider">
                      Positive Events
                    </div>
                    <div className="mt-1 text-2xl font-bold font-mono text-teal-950">
                      {selectedModelData.positive_count.toLocaleString()}
                    </div>
                    <p className="mt-1 text-[11px] text-teal-700">Hypoglycaemia instances</p>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <div className="text-[11px] font-semibold text-slate-800 uppercase tracking-wider">
                      Negative Events
                    </div>
                    <div className="mt-1 text-2xl font-bold font-mono text-slate-950">
                      {selectedModelData.negative_count.toLocaleString()}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-600">Euglycemic records</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>Total Evaluated Samples:</span>
                  <strong className="font-mono text-slate-800">
                    {selectedModelData.sample_count.toLocaleString()} observations
                  </strong>
                </div>
              </div>

              {/* Macro-Averaged Breakdown Card */}
              <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-teal-600" />
                    Pooled vs. Participant-Macro Metrics
                  </h3>
                  <span className="text-xs text-slate-400">
                    Cohort: 25 T1D Subjects
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-700">ROC-AUC:</span>
                    <div className="flex items-center gap-4 font-mono">
                      <span>Pooled: <strong>{selectedModelData.pooled_metrics.roc_auc != null ? selectedModelData.pooled_metrics.roc_auc.toFixed(4) : '—'}</strong></span>
                      <span className="text-slate-400">|</span>
                      <span>Macro: <strong>{selectedModelData.macro_metrics.roc_auc != null ? selectedModelData.macro_metrics.roc_auc.toFixed(4) : '—'}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-700">Average Precision:</span>
                    <div className="flex items-center gap-4 font-mono">
                      <span>Pooled: <strong>{selectedModelData.pooled_metrics.average_precision != null ? selectedModelData.pooled_metrics.average_precision.toFixed(4) : '—'}</strong></span>
                      <span className="text-slate-400">|</span>
                      <span>Macro: <strong>{selectedModelData.macro_metrics.average_precision != null ? selectedModelData.macro_metrics.average_precision.toFixed(4) : '—'}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-700">Sensitivity (Recall):</span>
                    <div className="flex items-center gap-4 font-mono">
                      <span>Pooled: <strong>{selectedModelData.pooled_metrics.sensitivity != null ? `${(selectedModelData.pooled_metrics.sensitivity * 100).toFixed(1)}%` : '—'}</strong></span>
                      <span className="text-slate-400">|</span>
                      <span>Macro: <strong>{selectedModelData.macro_metrics.sensitivity != null ? `${(selectedModelData.macro_metrics.sensitivity * 100).toFixed(1)}%` : '—'}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-700">Specificity:</span>
                    <div className="flex items-center gap-4 font-mono">
                      <span>Pooled: <strong>{selectedModelData.pooled_metrics.specificity != null ? `${(selectedModelData.pooled_metrics.specificity * 100).toFixed(1)}%` : '—'}</strong></span>
                      <span className="text-slate-400">|</span>
                      <span>Macro: <strong>{selectedModelData.macro_metrics.specificity != null ? `${(selectedModelData.macro_metrics.specificity * 100).toFixed(1)}%` : '—'}</strong></span>
                    </div>
                  </div>
                </div>

                <p className="text-[11px] text-slate-500 leading-normal">
                  <em>Methodological Note:</em> Macro-averaging computes metrics independently for each participant before taking the mean, preventing high-frequency monitoring participants from dominating aggregate performance.
                </p>
              </div>
            </div>
          )}

          {/* Clinical Research Caveats Card */}
          <div className="p-4 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-amber-950">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
              Scientific and Clinical Evaluation Caveats
            </div>
            <ul className="list-disc pl-5 space-y-1 text-amber-900/90 leading-relaxed">
              <li>
                <strong>Cohort Homogeneity:</strong> Trained on retrospective data from 25 adult participants with Type 1 Diabetes wearing continuous glucose monitors and insulin pumps (CSII). Generalization to pediatric or non-insulin cohorts cannot be assumed.
              </li>
              <li>
                <strong>Physiological Sensor Delay:</strong> Subcutaneous interstitial fluid glucose lags capillary blood glucose by approximately 5 to 15 minutes during rapid glycemic flux.
              </li>
              <li>
                <strong>Operational Threshold Calibration:</strong> Thresholds were tuned to achieve 90% sensitivity on the training sets, which prioritizes early safety alerts at the cost of a higher false-positive rate.
              </li>
              <li>
                <strong>Research Prototype:</strong> GlycoTwin is an academic research system and is not approved by regulatory bodies (FDA, EMA) for automated medical decision-making.
              </li>
            </ul>
          </div>
        </>
      ) : (
        <EmptyState 
          title="No evaluation results" 
          description="Evaluation benchmark metrics could not be loaded." 
        />
      )}
    </div>
  );
};

export default ModelEvaluation;
