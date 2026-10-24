import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import type { HistoricalPredictionItem } from '../../types/api';

export interface PredictionTimelineChartProps {
  data: HistoricalPredictionItem[];
  threshold?: number;
  operationalThreshold?: number;
  height?: number;
}

export const PredictionTimelineChart: React.FC<PredictionTimelineChartProps> = ({
  data,
  threshold,
  operationalThreshold = 0.5,
  height = 300,
}) => {
  const effectiveThreshold = threshold ?? operationalThreshold;

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl bg-slate-50">
        No historical out-of-fold prediction records available.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    displayTime: new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    displayDate: new Date(d.time).toLocaleDateString([], { month: 'short', day: 'numeric' }),
    probability: d.predicted_probability,
    predictedClass: d.predicted_class,
    trueTarget: d.true_target,
    fold: d.cv_fold,
    threshold: d.operational_threshold,
  }));

  return (
    <div className="w-full">
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="displayTime"
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 10, fill: '#64748b' }}
            />
            <YAxis
              domain={[0, 1]}
              ticks={[0, 0.25, 0.5, 0.75, 1]}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                const isAlert = d.probability >= (d.threshold || effectiveThreshold);
                return (
                  <div className="bg-slate-900/95 text-white p-3 rounded-lg shadow-lg border border-slate-700 text-xs space-y-1">
                    <div className="text-slate-400 font-mono text-[10px]">
                      {d.displayDate} {d.displayTime}
                    </div>
                    <div className="font-semibold text-sm flex items-center justify-between gap-3">
                      <span>Predicted Probability:</span>
                      <span className="font-mono text-teal-300">
                        {(d.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 flex items-center justify-between">
                      <span>Threshold:</span>
                      <span className="font-mono">
                        {(d.threshold || effectiveThreshold).toFixed(4)}
                      </span>
                    </div>
                    <div className="text-[11px] flex items-center justify-between">
                      <span>Model Decision:</span>
                      <span
                        className={`font-semibold ${
                          isAlert ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {isAlert ? 'ALERT (Hypo Risk)' : 'Normal'}
                      </span>
                    </div>
                    {d.trueTarget !== null && (
                      <div className="text-[11px] border-t border-slate-700 pt-1 text-slate-300 flex items-center justify-between">
                        <span>Observed Outcome:</span>
                        <span
                          className={`font-semibold ${
                            d.trueTarget === 1 ? 'text-amber-400' : 'text-slate-400'
                          }`}
                        >
                          {d.trueTarget === 1 ? 'Event Occurred (<70)' : 'No Event'}
                        </span>
                      </div>
                    )}
                    {d.fold && (
                      <div className="text-[10px] text-slate-400 font-mono">
                        Held-Out Fold: {d.fold}
                      </div>
                    )}
                  </div>
                );
              }}
            />
            <ReferenceLine
              y={effectiveThreshold}
              stroke="#e11d48"
              strokeDasharray="4 4"
              strokeWidth={1.5}
            />
            <Area
              type="monotone"
              dataKey="probability"
              stroke="#0d9488"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#riskGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PredictionTimelineChart;
