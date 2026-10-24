import React from 'react';
import { 
  Database, 
  Cpu, 
  ShieldAlert, 
  CheckCircle2, 
  GitBranch, 
  Layers,
  Activity
} from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header Banner */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            About GlycoTwin & Research Provenance
          </h1>
          <span className="inline-flex items-center rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
            Research Architecture
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Personalised glucose digital twin system developed with the HUPA-UCM clinical cohort for predictive hypoglycaemia onset anticipation.
        </p>
      </div>

      {/* Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Project Mission */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Activity className="w-4 h-4 text-teal-600" />
            Project Objectives & Vision
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            GlycoTwin bridges clinical physiology and computational intelligence. By reconstructing patient-specific continuous glucose trajectories from retrospective continuous glucose monitors (CGM) and insulin pumps, GlycoTwin evaluates whether transfer-learned individual calibration enhances event anticipation over population models.
          </p>
          <div className="pt-2 text-xs text-slate-700 space-y-1.5 font-medium">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
              <span>Full end-to-end reproducible machine learning pipeline</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
              <span>Rigorous leak-free feature engineering & temporal purge gaps</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
              <span>Interactive clinical research digital twin interface</span>
            </div>
          </div>
        </div>

        {/* Dataset Provenance */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Database className="w-4 h-4 text-teal-600" />
            HUPA-UCM Diabetes Dataset Provenance
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Data acquired from the open-access <strong>HUPA-UCM Diabetes Dataset</strong> collected by the Hospital Universitario Príncipe de Asturias (HUPA) and Universidad Complutense de Madrid (UCM).
          </p>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-[11px] text-slate-700 space-y-1">
            <div><strong>Citation:</strong> Hidalgo et al., <em>Data in Brief</em>, 2024.</div>
            <div><strong>Cohort:</strong> 25 anonymised adult participants with Type 1 Diabetes.</div>
            <div><strong>Modality:</strong> Dexcom G6 CGM, Medtronic/Tandem CSII pump, and smartband biometrics.</div>
            <div><strong>Licence:</strong> Creative Commons Attribution 4.0 International (CC BY 4.0).</div>
          </div>
        </div>
      </div>

      {/* Prediction Tasks & Personalisation Architecture */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-xs space-y-4">
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-teal-600" />
          Task Formulations & Scientific Methodology
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-teal-100 text-teal-800 text-[10px] font-bold">
              Task B (Primary Benchmark)
            </span>
            <h4 className="font-semibold text-slate-900 text-sm">Impending Hypoglycaemia Onset</h4>
            <p className="text-slate-600 leading-relaxed">
              Conditioned strictly on current glucose being ≥ 70 mg/dL: predicts whether glucose will fall below 70 mg/dL within the next 30 minutes (horizon = 30 minutes). Evaluates early prevention and actionable clinical onset warning.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-slate-200 text-slate-800 text-[10px] font-bold">
              Task A (Secondary Benchmark)
            </span>
            <h4 className="font-semibold text-slate-900 text-sm">Future Hypoglycaemia Risk</h4>
            <p className="text-slate-600 leading-relaxed">
              Unconditional prediction of whether any glucose value in the 30-minute forward window falls below 70 mg/dL, regardless of whether the patient is currently euglycemic or already hypoglycemic.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-teal-100 bg-teal-50/40 space-y-2 text-xs">
          <h4 className="font-semibold text-teal-950 text-sm flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-teal-700" />
            Subject-Level Transfer Personalisation Mechanism
          </h4>
          <p className="text-teal-900 leading-relaxed">
            The personalisation protocol trains a generalized population XGBoost gradient-boosted decision tree across the cohort, then adapts the model to each individual by fitting an individual-specific logistic calibration (Platt scaling) on the participant's first 40% chronological window. A 30-minute purge window is strictly enforced between the calibration period and the evaluation period to eliminate target overlap.
          </p>
        </div>
      </div>

      {/* Software Architecture & Technologies */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-xs space-y-4">
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-teal-600" />
          Technical Stack & System Architecture
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <div className="font-semibold text-slate-900">Backend API</div>
            <div className="text-slate-500 mt-1">Python 3.12, FastAPI, Pydantic v2, Uvicorn</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <div className="font-semibold text-slate-900">Machine Learning</div>
            <div className="text-slate-500 mt-1">XGBoost, Scikit-Learn, Joblib, NumPy, Pandas</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <div className="font-semibold text-slate-900">Frontend UI</div>
            <div className="text-slate-500 mt-1">React 19, TypeScript, Vite, React Router v7</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <div className="font-semibold text-slate-900">Visualization</div>
            <div className="text-slate-500 mt-1">Tailwind CSS v4, Recharts, Lucide React</div>
          </div>
        </div>
      </div>

      {/* Regulatory Notice & Ethics */}
      <div className="p-5 bg-rose-50/60 border border-rose-200/80 rounded-xl text-xs text-rose-900 space-y-2">
        <div className="flex items-center gap-2 font-bold text-rose-950 text-sm">
          <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
          Research Prototype & Regulatory Non-Medical Device Notice
        </div>
        <p className="leading-relaxed">
          GlycoTwin is an academic research software prototype built exclusively for scientific benchmarking, physiological modelling, and algorithmic evaluation.
        </p>
        <p className="leading-relaxed">
          It is <strong>not a medical device</strong> as defined by the EU Medical Device Regulation (MDR) or U.S. FDA regulations. It is not approved, cleared, or intended to diagnose, treat, cure, or prevent diabetes, hypoglycemia, or any other medical condition. Do not use predicted probabilities or simulated scenarios to adjust insulin dosages, carbohydrate consumption, or real-world medical care.
        </p>
      </div>
    </div>
  );
};

export default About;
