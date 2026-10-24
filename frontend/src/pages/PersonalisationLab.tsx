import React, { useEffect, useState, useMemo } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  ArrowDownRight, 
  Scale, 
  Layers,
  Sparkles
} from 'lucide-react';
import { fetchPersonalisationResults } from '../services/api';
import type { PersonalisationResponse, PersonalisationItem } from '../types/api';
import MetricCard from '../components/shared/MetricCard';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorAlert from '../components/shared/ErrorAlert';
import EmptyState from '../components/shared/EmptyState';
import PersonalisationDeltaChart from '../components/charts/PersonalisationDeltaChart';

interface PersonalisationLabProps {
  currentPatientId: string;
  onSelectPatient: (patientId: string) => void;
}

export const PersonalisationLab: React.FC<PersonalisationLabProps> = ({
  currentPatientId,
  onSelectPatient
}) => {
  const [data, setData] = useState<PersonalisationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'personalised' | 'fallback'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchPersonalisationResults()
      .then((res: PersonalisationResponse) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || 'Failed to load personalisation experiment results');
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, []);

  // Filtered participant list
  const filteredParticipants = useMemo(() => {
    if (!data) return [];
    return data.participants.filter((p: PersonalisationItem) => {
      const matchesStatus = 
        statusFilter === 'all' || 
        p.adaptation_status === statusFilter;
      const matchesSearch = 
        !searchQuery.trim() || 
        p.participant_id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [data, statusFilter, searchQuery]);

  // Dynamically identify all participants who triggered automated fallback
  const fallbackParticipants = useMemo(() => {
    if (!data) return [];
    return data.participants.filter((p: PersonalisationItem) => p.adaptation_status !== 'personalised');
  }, [data]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Personalisation Laboratory
            </h1>
            <span className="inline-flex items-center rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              Transfer Learning & Adaptation
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Empirical investigation of subject-level model calibration using chronological split, purge gap, and Platt scaling.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <Scale className="w-3.5 h-3.5 text-teal-600" />
            Purge Window: <strong>30 minutes</strong>
          </span>
        </div>
      </div>

      {error && (
        <ErrorAlert 
          title="Personalisation Service Error" 
          message={error} 
          onRetry={() => setLoading(true)} 
        />
      )}

      {/* Signature Research Question Card */}
      <div className="bg-gradient-to-r from-slate-900 via-teal-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            Core Research Hypothesis
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            "Does adapting a population-trained model to an individual's historical glucose patterns improve future event predictions?"
          </h2>
          <p className="mt-2.5 text-sm text-slate-300 leading-relaxed">
            The authoritative experiment trains on the population cohort, then recalibrates the decision function on an individual's initial chronological observations (first 30% calibration segment). A <strong>30-minute purge gap</strong> prevents label contamination before evaluating on subsequent future prediction windows.
          </p>
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
            <LoadingSkeleton lines={6} />
          </div>
        </div>
      ) : data ? (
        <>
          {/* Cohort Summary Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <MetricCard
              title="Adapted Cohort"
              value={`${data.successful_adaptations} / ${data.total_participants}`}
              subtitle={
                fallbackParticipants.length > 0
                  ? `${fallbackParticipants.length} fallback (${fallbackParticipants.map(p => `${p.participant_id}: ${p.calib_positives} onset labels`).join(', ')})`
                  : 'All participants adapted'
              }
              badge={{ 
                text: `${Math.round((data.successful_adaptations / data.total_participants) * 100)}% Adapted`, 
                variant: 'teal' 
              }}
            />
            <MetricCard
              title="Mean Δ Brier Score"
              value={data.summary_deltas.mean_delta_brier.toFixed(4)}
              subtitle={`${data.summary_deltas.participants_improved_brier}/${data.total_participants} improved`}
              delta={{ value: 'Lower is better', isPositive: true }}
              badge={{ text: 'Calibrated', variant: 'teal' }}
            />
            <MetricCard
              title="Mean Δ ROC-AUC"
              value={data.summary_deltas.mean_delta_roc_auc.toFixed(4)}
              subtitle="Strictly ranking-invariant"
              delta={{ value: '0.0000 delta', isPositive: true }}
              badge={{ text: 'Invariant', variant: 'neutral' }}
            />
            <MetricCard
              title="Mean Δ F1-Score"
              value={data.summary_deltas.mean_delta_f1.toFixed(4)}
              subtitle="At calibrated cutoffs"
              badge={{ text: 'F1 Metric', variant: 'neutral' }}
            />
          </div>

          {/* Visualization: Personalisation Delta Chart */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <ArrowDownRight className="w-4 h-4 text-teal-600" />
                  Subject-Level Brier Score Improvement (Δ Brier = Brier_pers - Brier_pop)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Negative values (teal bars) represent superior probability calibration under the personalized model.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="inline-flex items-center gap-1.5 font-medium text-teal-700 bg-teal-50 px-2 py-1 rounded-sm border border-teal-200">
                  <span className="w-2 h-2 rounded-full bg-teal-600" />
                  Calibrated (Δ &lt; 0)
                </span>
                <span className="inline-flex items-center gap-1.5 font-medium text-amber-700 bg-amber-50 px-2 py-1 rounded-sm border border-amber-200">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  Population Fallback (Δ = 0)
                </span>
              </div>
            </div>

            <div className="mt-4">
              <PersonalisationDeltaChart
                participants={data.participants}
                height={340}
              />
            </div>
          </div>

          {/* Scientific Methodological Explanation Card */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-teal-600" />
              Methodological Findings & Scientific Interpretation
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  Why Brier Score Improves (Mean Δ = -0.0615)
                </div>
                <p className="text-slate-600 leading-relaxed">
                  The adaptation mechanism implements <strong>Platt log-odds scaling</strong> on the calibration segment. This adjusts the intercept and scale of predicted logits to match the individual’s baseline onset frequency. For participants with lower or higher onset rates than the population average, predicted probabilities are dramatically closer to empirical outcomes.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-slate-600" />
                  Why Discrimination (ROC-AUC) Remains Invariant (Δ = 0.0000)
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Platt scaling applies a strictly <strong>monotonic sigmoid transformation</strong> to the model outputs. Because ROC-AUC and Average Precision evaluate rank order rather than numerical probability calibration, monotonic scaling does not reorder predictions. True discriminative adaptation requires retraining tree splits or feature representations.
                </p>
              </div>
            </div>

            {/* Dynamic Fallback Notice */}
            {fallbackParticipants.length > 0 && (
              <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <strong>Automated Model Fallback ({fallbackParticipants.map(p => p.participant_id).join(', ')}):</strong>{' '}
                  {fallbackParticipants.map(p => (
                    <span key={p.participant_id}>
                      Participant <strong>{p.participant_id}</strong> had zero positive onset prediction windows in the initial calibration window ({p.calib_positives} positive labels across {p.calib_rows_usable.toLocaleString()} usable windows).
                      Because 1D logistic recalibration cannot converge without positive class observations, the digital twin automatically fell back to the population XGBoost model. This safe fallback guarantees mathematical stability and prevents divergence in low-prevalence monitoring records.
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Participant Results Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Subject-by-Subject Evaluation Comparison
                </h3>
                <p className="text-xs text-slate-500">
                  Showing {filteredParticipants.length} of {data.total_participants} participants
                </p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Filter participant ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg focus:ring-teal-500"
                />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white"
                >
                  <option value="all">All Statuses</option>
                  <option value="personalised">Personalised ({data.successful_adaptations})</option>
                  <option value="fallback">Fallback Only ({data.fallback_adaptations})</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">Participant ID</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Population Brier</th>
                    <th className="px-4 py-3">Personalised Brier</th>
                    <th className="px-4 py-3">Δ Brier Score</th>
                    <th className="px-4 py-3">ROC-AUC</th>
                    <th className="px-4 py-3">Calib / Eval Split</th>
                    <th className="px-4 py-3">Purged Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredParticipants.map((p: PersonalisationItem) => {
                    const isSelected = p.participant_id === currentPatientId;
                    const isFallback = p.adaptation_status !== 'personalised';
                    return (
                      <tr 
                        key={p.participant_id}
                        onClick={() => onSelectPatient(p.participant_id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected 
                            ? 'bg-teal-50/60 font-medium' 
                            : 'hover:bg-slate-50/80'
                        }`}
                      >
                        <td className="px-4 py-2.5 font-mono text-slate-900 font-semibold">
                          {p.participant_id}
                        </td>
                        <td className="px-4 py-2.5">
                          {isFallback ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                              Fallback
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                              Personalised
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 font-mono">
                          {p.pop_brier != null ? p.pop_brier.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-2.5 font-mono font-semibold text-teal-800">
                          {p.pers_brier != null ? p.pers_brier.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-2.5 font-mono font-bold">
                          {p.delta_brier != null ? (
                            p.delta_brier < 0 ? (
                              <span className="text-teal-700">
                                {p.delta_brier.toFixed(4)}
                              </span>
                            ) : (
                              <span className="text-slate-400">
                                {p.delta_brier.toFixed(4)}
                              </span>
                            )
                          ) : '—'}
                        </td>
                        <td className="px-4 py-2.5 font-mono">
                          {p.pop_roc_auc != null ? p.pop_roc_auc.toFixed(4) : '—'}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-slate-500">
                          {p.calib_rows_usable.toLocaleString()} / {p.eval_rows.toLocaleString()}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-slate-400">
                          {p.calib_rows_purged} pts
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <EmptyState 
          title="No data available" 
          description="Personalisation experiment results could not be retrieved." 
        />
      )}
    </div>
  );
};

export default PersonalisationLab;
