import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Activity, Database, CheckCircle2, AlertTriangle, User } from 'lucide-react';
import { api } from '../../services/api';
import type { HealthResponse } from '../../types/api';

interface TopBarProps {
  selectedPatientId: string;
  onSelectPatient: (patientId: string) => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  selectedPatientId,
  onSelectPatient,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [patientIds, setPatientIds] = useState<string[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    // Fetch participants list and health status
    api.getPatients(1, 100)
      .then((res) => {
        const ids = res.patients.map((p) => p.participant_id);
        setPatientIds(ids);
      })
      .catch(() => {});

    api.getHealth()
      .then((res) => setHealth(res))
      .catch(() => setHealth(null));
  }, []);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Glucose Intelligence Overview';
    if (path.startsWith('/patients')) return 'Patient Digital Twin & Telemetry';
    if (path.startsWith('/predictions')) return 'Hypoglycemia Risk Predictions';
    if (path.startsWith('/personalisation')) return 'Personalisation Laboratory';
    if (path.startsWith('/evaluation')) return 'Population Model Evaluation';
    if (path.startsWith('/about')) return 'About GlycoTwin & Research Dataset';
    return 'GlycoTwin Dashboard';
  };

  const handlePatientChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    onSelectPatient(newId);
    if (location.pathname.startsWith('/patients/')) {
      navigate(`/patients/${newId}`);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Title & Context */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-bold text-slate-900 tracking-tight m-0">
          {getPageTitle()}
        </h1>
        <span className="hidden md:inline-flex items-center gap-1 text-[11px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">
          <Database className="w-3 h-3 text-slate-500" />
          Retrospective Data · 5-min Grid
        </span>
      </div>

      {/* Controls & Status Indicator */}
      <div className="flex items-center gap-4">
        {/* Participant Switcher */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-700 shadow-2xs">
          <User className="w-3.5 h-3.5 text-teal-600" />
          <span className="font-medium text-slate-500">Participant:</span>
          <select
            value={selectedPatientId}
            onChange={handlePatientChange}
            className="bg-transparent font-semibold text-slate-800 outline-none cursor-pointer pr-1"
          >
            {patientIds.length > 0 ? (
              patientIds.map((pid) => (
                <option key={pid} value={pid}>
                  {pid}
                </option>
              ))
            ) : (
              <option value="HUPA0001P">HUPA0001P</option>
            )}
          </select>
        </div>

        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-1.5 text-xs font-medium">
          {health?.status === 'healthy' ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200/80">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              API Connected
            </span>
          ) : health?.status === 'degraded' ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-amber-50 text-amber-700 border border-amber-200/80">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              API Degraded
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-rose-50 text-rose-700 border border-rose-200/80">
              <Activity className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
              Connecting...
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
