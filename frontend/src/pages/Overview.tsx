import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Activity,
  ShieldCheck,
  TrendingUp,
  Clock,
  ArrowRight,
  Database,
  BarChart2
} from 'lucide-react';
import { api } from '../services/api';
import type { MetadataResponse, EvaluationResponse, ObservationItem } from '../types/api';
import { MetricCard } from '../components/shared/MetricCard';
import { GlucoseTimeSeriesChart } from '../components/charts/GlucoseTimeSeriesChart';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorAlert } from '../components/shared/ErrorAlert';

interface OverviewProps {
  currentPatientId?: string;
  selectedPatientId?: string;
  onSelectPatient?: (patientId: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ 
  currentPatientId,
  selectedPatientId 
}) => {
  const activeId = selectedPatientId || currentPatientId || 'HUPA0001P';

  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [evalOnset, setEvalOnset] = useState<EvaluationResponse | null>(null);
  const [previewObs, setPreviewObs] = useState<ObservationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.getMetadata(),
      api.getModelEvaluation('onset'),
      api.getPatientObservations(activeId, { limit: 120 }),
    ])
      .then(([metaRes, onsetRes, obsRes]) => {
        setMetadata(metaRes);
        setEvalOnset(onsetRes);
        setPreviewObs(obsRes.observations);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load system metadata');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [activeId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton rows={4} height="h-28" />
        <LoadingSkeleton rows={2} height="h-64" />
      </div>
    );
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={loadData} />;
  }

  const championOnset = evalOnset?.models.find((m) => m.model === 'xgboost');

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-700/60 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 mb-3">
            <ShieldCheck className="w-3.5 h-3.5" /> Research Prototype · Retrospective Dataset
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white m-0">
            Predictive Diabetes Digital Twin Platform
          </h2>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Personalised blood glucose forecasting and subject-level transfer calibration using the open-access HUPA-UCM Clinical Cohort (25 participants with Type 1 Diabetes).
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-6">
            <Link
              to="/patients"
              className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-lg transition-all shadow-sm"
            >
              Explore Digital Twin Cohort
            </Link>
            <Link
              to="/personalisation"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs rounded-lg border border-slate-600 transition-all"
            >
              Inspect Personalisation Lab
            </Link>
          </div>
        </div>
      </div>

      {/* Cohort & Benchmark Metric Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Clinical Cohort"
          value={metadata?.total_participants ?? 25}
          subtitle="Adult Type 1 Diabetes"
          icon={<Users className="w-4 h-4" />}
          badge="HUPA-UCM"
          badgeColor="slate"
        />
        <MetricCard
          title="Verified Observations"
          value={metadata?.total_observations ? metadata.total_observations.toLocaleString() : '309,392'}
          subtitle="100.0% Uniform 5-Minute Grid"
          icon={<Database className="w-4 h-4" />}
          badge="Clean Data"
          badgeColor="blue"
        />
        <MetricCard
          title="Primary Task (Onset)"
          value={`${championOnset?.pooled_metrics.roc_auc ? (championOnset.pooled_metrics.roc_auc * 100).toFixed(1) : '97.0'}% AUC`}
          subtitle="Impending Onset in 30m (Current ≥70)"
          icon={<Activity className="w-4 h-4" />}
          change={{
            value: `PR-AUC: ${championOnset?.pooled_metrics.average_precision ? championOnset.pooled_metrics.average_precision.toFixed(3) : '0.627'}`,
            isPositive: true,
            label: 'XGBoost',
          }}
          badge="Champion"
          badgeColor="teal"
        />
        <MetricCard
          title="Prediction Horizon"
          value="30 Minutes"
          subtitle="Threshold: < 70 mg/dL (Hypo)"
          icon={<Clock className="w-4 h-4" />}
          badge="Operational"
          badgeColor="amber"
        />
      </div>

      {/* Historical CGM Preview for Selected Participant */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-teal-600" />
              Glucose Trajectory Preview: {activeId}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Initial 10-hour retrospective sensor window (5-minute uniform resolution).
            </p>
          </div>
          <Link
            to={`/patients/${activeId}`}
            className="text-xs font-semibold text-teal-600 hover:text-teal-700 inline-flex items-center gap-1 self-start sm:self-auto"
          >
            Open Full Digital Twin View <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <GlucoseTimeSeriesChart data={previewObs} height={300} />
      </div>

      {/* Population Models Comparison Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-teal-600" />
              Population Model Benchmarks (Task B: Impending Onset)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Authoritative 5-fold cross-validation performance across 25 participants.
            </p>
          </div>
          <Link
            to="/evaluation"
            className="text-xs font-semibold text-teal-600 hover:text-teal-700 inline-flex items-center gap-1"
          >
            Full Evaluation Details <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Model</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3 text-right">ROC-AUC</th>
                <th className="py-2.5 px-3 text-right">PR-AUC</th>
                <th className="py-2.5 px-3 text-right">Sensitivity (Recall)</th>
                <th className="py-2.5 px-3 text-right">Specificity</th>
                <th className="py-2.5 px-3 text-right">Brier Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-slate-700">
              {evalOnset?.models.map((m) => {
                const isChampion = m.model === 'xgboost';
                return (
                  <tr
                    key={m.model}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      isChampion ? 'bg-teal-50/40 font-semibold' : ''
                    }`}
                  >
                    <td className="py-3 px-3 font-sans font-bold text-slate-900 flex items-center gap-2">
                      {m.model.toUpperCase().replace('_', ' ')}
                      {isChampion && (
                        <span className="text-[10px] font-sans px-1.5 py-0.2 bg-teal-100 text-teal-800 rounded-sm font-semibold uppercase">
                          Champion
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-sans text-slate-500">
                      {m.model === 'rule_based' ? 'Baseline Heuristic' : m.model === 'logistic_regression' ? 'Linear Classifier' : 'Gradient Boosted Trees'}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-900">
                      {m.pooled_metrics.roc_auc != null ? m.pooled_metrics.roc_auc.toFixed(4) : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-right text-teal-700">
                      {m.pooled_metrics.average_precision != null ? m.pooled_metrics.average_precision.toFixed(4) : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      {m.pooled_metrics.sensitivity != null ? `${(m.pooled_metrics.sensitivity * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      {m.pooled_metrics.specificity != null ? `${(m.pooled_metrics.specificity * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-500">
                      {m.pooled_metrics.brier_score != null ? m.pooled_metrics.brier_score.toFixed(4) : 'N/A'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Overview;
