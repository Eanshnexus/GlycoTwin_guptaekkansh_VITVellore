import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  UserCheck, 
  Activity, 
  Calendar, 
  Heart, 
  Footprints, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  Filter,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import { 
  fetchPatients, 
  fetchPatientDetail, 
  fetchPatientObservations 
} from '../services/api';
import type { 
  PatientListItem, 
  PatientListResponse,
  PatientDetail, 
  ObservationItem,
  ObservationResponse
} from '../types/api';
import StatusBadge from '../components/shared/StatusBadge';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorAlert from '../components/shared/ErrorAlert';
import EmptyState from '../components/shared/EmptyState';
import GlucoseTimeSeriesChart from '../components/charts/GlucoseTimeSeriesChart';

interface PatientsPageProps {
  currentPatientId: string;
  onSelectPatient: (patientId: string) => void;
}

export const Patients: React.FC<PatientsPageProps> = ({
  currentPatientId,
  onSelectPatient
}) => {
  const { patientId: paramPatientId } = useParams<{ patientId?: string }>();
  const navigate = useNavigate();

  // Active patient ID from route param or prop
  const activeId = paramPatientId || currentPatientId;

  // State
  const [patientsList, setPatientsList] = useState<PatientListItem[]>([]);
  const [patientDetail, setPatientDetail] = useState<PatientDetail | null>(null);
  const [observations, setObservations] = useState<ObservationItem[]>([]);
  const [obsCount, setObsCount] = useState<number>(0);
  const [obsLimit, setObsLimit] = useState<number>(300);
  const [obsOffset, setObsOffset] = useState<number>(0);

  // Modality display toggle
  const [showHeartRate, setShowHeartRate] = useState<boolean>(false);
  const [showSteps, setShowSteps] = useState<boolean>(false);

  // Search filter for patients
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Loading & error states
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(true);
  const [loadingObs, setLoadingObs] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load cohort list on mount
  useEffect(() => {
    let isMounted = true;
    setLoadingList(true);
    fetchPatients(1, 25)
      .then((res: PatientListResponse) => {
        if (isMounted) {
          setPatientsList(res.patients);
          setLoadingList(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || 'Failed to load patient directory');
          setLoadingList(false);
        }
      });
    return () => { isMounted = false; };
  }, []);

  // Update URL and prop when activeId changes
  useEffect(() => {
    if (activeId && activeId !== currentPatientId) {
      onSelectPatient(activeId);
    }
  }, [activeId, currentPatientId, onSelectPatient]);

  // Load patient detail
  useEffect(() => {
    if (!activeId) return;
    let isMounted = true;
    setLoadingDetail(true);
    setError(null);

    fetchPatientDetail(activeId)
      .then((detail: PatientDetail) => {
        if (isMounted) {
          setPatientDetail(detail);
          setLoadingDetail(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || `Failed to load details for ${activeId}`);
          setLoadingDetail(false);
        }
      });

    return () => { isMounted = false; };
  }, [activeId]);

  // Load observations (with pagination)
  useEffect(() => {
    if (!activeId) return;
    let isMounted = true;
    setLoadingObs(true);

    fetchPatientObservations(activeId, {
      limit: obsLimit,
      offset: obsOffset
    })
      .then((res: ObservationResponse) => {
        if (isMounted) {
          setObservations(res.observations);
          setObsCount(res.pagination.total_items);
          setLoadingObs(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || 'Failed to load patient glucose telemetry');
          setLoadingObs(false);
        }
      });

    return () => { isMounted = false; };
  }, [activeId, obsLimit, obsOffset]);

  // Navigation handlers: previous / next participant
  const currentIndex = useMemo(() => {
    return patientsList.findIndex(p => p.participant_id === activeId);
  }, [patientsList, activeId]);

  const handlePrevPatient = () => {
    if (currentIndex > 0) {
      const prevId = patientsList[currentIndex - 1].participant_id;
      navigate(`/patients/${prevId}`);
      onSelectPatient(prevId);
      setObsOffset(0);
    }
  };

  const handleNextPatient = () => {
    if (currentIndex < patientsList.length - 1 && currentIndex !== -1) {
      const nextId = patientsList[currentIndex + 1].participant_id;
      navigate(`/patients/${nextId}`);
      onSelectPatient(nextId);
      setObsOffset(0);
    }
  };

  const filteredPatients = useMemo(() => {
    if (!searchQuery.trim()) return patientsList;
    return patientsList.filter(p => 
      p.participant_id.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [patientsList, searchQuery]);

  // Computed metrics from loaded observations
  const currentWindowMetrics = useMemo(() => {
    if (!observations.length) return null;
    const values = observations.map(o => o.glucose).filter(g => g !== null) as number[];
    if (!values.length) return null;

    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const tirCount = values.filter(v => v >= 70 && v <= 180).length;
    const tbrCount = values.filter(v => v < 70).length;
    const tarCount = values.filter(v => v > 180).length;

    return {
      mean: Math.round(mean * 10) / 10,
      min,
      max,
      tir: Math.round((tirCount / values.length) * 100),
      tbr: Math.round((tbrCount / values.length) * 100),
      tar: Math.round((tarCount / values.length) * 100)
    };
  }, [observations]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Participant Digital Twin
            </h1>
            <span className="inline-flex items-center rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              Retrospective CGM Telemetry
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Continuous glucose monitoring, contextual biometrics, and historical recording coverage for anonymised research participants.
          </p>
        </div>

        {/* Prev / Next Navigation Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPatient}
            disabled={currentIndex <= 0}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-xs transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>
          <span className="text-xs font-semibold text-slate-600 px-2">
            {currentIndex >= 0 ? `${currentIndex + 1} of ${patientsList.length}` : '—'}
          </span>
          <button
            onClick={handleNextPatient}
            disabled={currentIndex >= patientsList.length - 1 || currentIndex === -1}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-xs transition-colors"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <ErrorAlert 
          title="Telemetry Feed Error" 
          message={error} 
          onRetry={() => {
            setError(null);
            setObsOffset(0);
          }} 
        />
      )}

      {/* Grid: Left Column (Participant Selector) & Right Column (Digital Twin Telemetry) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Col: Participant Directory */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200/80 shadow-xs p-4 flex flex-col h-[750px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-teal-600" />
              Cohort Directory
            </h2>
            <span className="text-xs font-bold text-slate-400">
              {patientsList.length} Cohort
            </span>
          </div>

          {/* Search bar */}
          <div className="relative mt-3 mb-3">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search participant ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 placeholder-slate-400"
            />
          </div>

          {/* Scrollable List */}
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 text-xs">
            {loadingList ? (
              <div className="p-4 space-y-2">
                <LoadingSkeleton lines={6} />
              </div>
            ) : filteredPatients.length === 0 ? (
              <p className="text-center py-8 text-slate-400 text-xs">No participants found</p>
            ) : (
              filteredPatients.map((p) => {
                const isSelected = p.participant_id === activeId;
                return (
                  <button
                    key={p.participant_id}
                    onClick={() => {
                      navigate(`/patients/${p.participant_id}`);
                      onSelectPatient(p.participant_id);
                      setObsOffset(0);
                    }}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                      isSelected
                        ? 'border-teal-500 bg-teal-50/50 shadow-xs'
                        : 'border-slate-100 bg-slate-50/50 hover:bg-slate-100/70 hover:border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`font-mono font-semibold ${isSelected ? 'text-teal-900' : 'text-slate-800'}`}>
                        {p.participant_id}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        {p.observation_count.toLocaleString()} pts
                      </span>
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                      <span>{Math.round(p.duration_days)} days</span>
                      {p.available_modalities.length > 0 && (
                        <span className="text-teal-600 font-medium">
                          +{p.available_modalities.length} streams
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right 3 Cols: Telemetry, Summary, & Context */}
        <div className="lg:col-span-3 space-y-6">
          {loadingDetail ? (
            <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs">
              <LoadingSkeleton lines={4} />
            </div>
          ) : patientDetail ? (
            <>
              {/* Participant Profile Banner */}
              <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold font-mono text-slate-900">
                        {patientDetail.participant_id}
                      </h2>
                      <StatusBadge status="normal" label="Type 1 Diabetes (Adult Cohort)" />
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        Duration: <strong className="text-slate-700">{patientDetail.duration_days.toFixed(1)} days</strong>
                      </span>
                      <span>•</span>
                      <span>
                        Telemetry Range: <strong className="text-slate-700">{patientDetail.start_time?.slice(0, 10)}</strong> to <strong className="text-slate-700">{patientDetail.end_time?.slice(0, 10)}</strong>
                      </span>
                      <span>•</span>
                      <span>
                        Predictions: <strong className="text-slate-700">{(patientDetail.risk_predictions_count + patientDetail.onset_predictions_count).toLocaleString()} saved</strong>
                      </span>
                    </div>
                  </div>

                  {/* Modality Stream Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {patientDetail.available_modalities.map(m => (
                      <span 
                        key={m} 
                        className="inline-flex items-center px-2 py-0.5 rounded-sm bg-slate-100 text-slate-600 text-[11px] font-medium border border-slate-200"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Glycemic Metrics Bar */}
                {currentWindowMetrics && (
                  <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Window Mean</div>
                      <div className="mt-1 text-lg font-bold text-slate-800">
                        {currentWindowMetrics.mean} <span className="text-xs font-normal text-slate-500">mg/dL</span>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Min - Max</div>
                      <div className="mt-1 text-sm font-bold text-slate-800">
                        {currentWindowMetrics.min} - {currentWindowMetrics.max} <span className="text-[10px] font-normal text-slate-500">mg/dL</span>
                      </div>
                    </div>
                    <div className="bg-teal-50/50 rounded-lg p-2.5 border border-teal-100">
                      <div className="text-[10px] uppercase font-bold text-teal-700">TIR (70-180)</div>
                      <div className="mt-1 text-lg font-bold text-teal-800">
                        {currentWindowMetrics.tir}%
                      </div>
                    </div>
                    <div className="bg-rose-50/50 rounded-lg p-2.5 border border-rose-100">
                      <div className="text-[10px] uppercase font-bold text-rose-700">TBR (&lt;70)</div>
                      <div className="mt-1 text-lg font-bold text-rose-800">
                        {currentWindowMetrics.tbr}%
                      </div>
                    </div>
                    <div className="bg-amber-50/50 rounded-lg p-2.5 border border-amber-100">
                      <div className="text-[10px] uppercase font-bold text-amber-700">TAR (&gt;180)</div>
                      <div className="mt-1 text-lg font-bold text-amber-800">
                        {currentWindowMetrics.tar}%
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Loaded Points</div>
                      <div className="mt-1 text-lg font-bold text-slate-800">
                        {observations.length} <span className="text-xs font-normal text-slate-500">of {obsCount}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Time Series Telemetry Card with Filter Controls */}
              <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                      <Activity className="w-4 h-4 text-teal-600" />
                      Continuous Glucose Telemetry (CGM)
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Standard nominal 5-minute continuous glucose records from clinical sensor.
                    </p>
                  </div>

                  {/* Contextual stream toggles */}
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={showHeartRate} 
                        onChange={(e) => setShowHeartRate(e.target.checked)} 
                        className="rounded-sm text-teal-600 focus:ring-teal-500 border-slate-300" 
                      />
                      <Heart className="w-3.5 h-3.5 text-rose-500" />
                      Heart Rate
                    </label>
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={showSteps} 
                        onChange={(e) => setShowSteps(e.target.checked)} 
                        className="rounded-sm text-teal-600 focus:ring-teal-500 border-slate-300" 
                      />
                      <Footprints className="w-3.5 h-3.5 text-amber-500" />
                      Steps
                    </label>
                  </div>
                </div>

                {/* Filter and Pagination Bar */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <Filter className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-semibold text-slate-700">Display Window:</span>
                    <select
                      value={obsLimit}
                      onChange={(e) => {
                        setObsLimit(Number(e.target.value));
                        setObsOffset(0);
                      }}
                      className="bg-white border border-slate-300 rounded-md px-2 py-1 text-xs focus:ring-teal-500"
                    >
                      <option value={100}>100 points (~8 hours)</option>
                      <option value={300}>300 points (~24 hours)</option>
                      <option value={600}>600 points (~2 days)</option>
                      <option value={1000}>1,000 points (~3.5 days)</option>
                    </select>
                  </div>

                  {/* Pagination Offset Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setObsOffset(Math.max(0, obsOffset - obsLimit))}
                      disabled={obsOffset === 0 || loadingObs}
                      className="px-2.5 py-1 bg-white border border-slate-300 rounded-md text-slate-700 hover:bg-slate-100 disabled:opacity-40 text-xs font-medium"
                    >
                      ← Newer
                    </button>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {obsOffset + 1} - {Math.min(obsOffset + obsLimit, obsCount)} of {obsCount}
                    </span>
                    <button
                      onClick={() => setObsOffset(obsOffset + obsLimit)}
                      disabled={obsOffset + obsLimit >= obsCount || loadingObs}
                      className="px-2.5 py-1 bg-white border border-slate-300 rounded-md text-slate-700 hover:bg-slate-100 disabled:opacity-40 text-xs font-medium"
                    >
                      Older →
                    </button>
                  </div>
                </div>

                {/* Chart Render */}
                <div className="mt-4">
                  {loadingObs ? (
                    <div className="h-80 flex items-center justify-center">
                      <LoadingSkeleton lines={6} />
                    </div>
                  ) : observations.length === 0 ? (
                    <EmptyState 
                      title="No observations loaded" 
                      description="No continuous glucose points were returned for the selected filter window." 
                    />
                  ) : (
                    <GlucoseTimeSeriesChart
                      data={observations}
                      height={360}
                      showHeartRate={showHeartRate}
                      showSteps={showSteps}
                    />
                  )}
                </div>

                {/* Notice below chart */}
                <div className="mt-4 p-3 bg-amber-50/70 border border-amber-200/80 rounded-lg flex items-start gap-2.5 text-xs text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Research Data Handling:</span> Sensor readings reflect continuous subcutaneous interstitial glucose. The red dotted line denotes <strong>70 mg/dL</strong> (hypoglycaemic threshold). Missing carbohydrate or insulin entries represent unrecorded events rather than confirmed zero values.
                  </div>
                </div>
              </div>

              {/* Action Links */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => navigate('/predictions')}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-600 text-white font-medium text-xs hover:bg-teal-700 shadow-xs transition-colors"
                >
                  View Historical Predictions for {patientDetail.participant_id}
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </>
          ) : (
            <EmptyState 
              title="No participant selected" 
              description="Please select an anonymised participant from the cohort directory." 
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Patients;
