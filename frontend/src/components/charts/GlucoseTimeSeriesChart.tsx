import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  CartesianGrid
} from 'recharts';
import type { ObservationItem } from '../../types/api';

export interface GlucoseTimeSeriesChartProps {
  data: ObservationItem[];
  height?: number;
  showContextModalities?: boolean;
  showHeartRate?: boolean;
  showSteps?: boolean;
}

export const GlucoseTimeSeriesChart: React.FC<GlucoseTimeSeriesChartProps> = ({
  data,
  height = 360,
  showHeartRate = false,
  showSteps = false,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl bg-slate-50">
        No glucose observations available for the selected interval.
      </div>
    );
  }

  // Format data for Recharts
  const chartData = data.map((d) => ({
    rawTime: d.time,
    displayTime: new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    displayDate: new Date(d.time).toLocaleDateString([], { month: 'short', day: 'numeric' }),
    glucose: d.glucose,
    heartRate: d.heart_rate,
    steps: d.steps,
    basalRate: d.basal_rate,
    carbs: d.carb_input,
    bolus: d.bolus_volume,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      const isHypo = item.glucose < 70;
      const isHyper = item.glucose > 180;

      return (
        <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700/80 space-y-1.5 z-50">
          <div className="text-[11px] text-slate-400 font-medium">
            {item.displayDate} · {item.displayTime}
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-300">CGM Glucose:</span>
            <span
              className={`text-sm font-bold ${
                isHypo
                  ? 'text-rose-400'
                  : isHyper
                  ? 'text-amber-400'
                  : 'text-teal-400'
              }`}
            >
              {item.glucose} mg/dL
            </span>
          </div>

          {/* Context biometrics if active */}
          {showHeartRate && item.heartRate && (
            <div className="text-slate-300 text-[11px] flex justify-between">
              <span>Heart Rate:</span>
              <span className="font-semibold text-rose-300">{item.heartRate} bpm</span>
            </div>
          )}
          {showSteps && item.steps !== null && item.steps !== undefined && (
            <div className="text-slate-300 text-[11px] flex justify-between">
              <span>Steps:</span>
              <span className="font-semibold text-amber-300">{item.steps}</span>
            </div>
          )}
          {item.bolus && item.bolus > 0 && (
            <div className="text-slate-300 text-[11px] flex justify-between">
              <span>Bolus:</span>
              <span className="font-semibold text-blue-300">{item.bolus} U</span>
            </div>
          )}
          {item.carbs && item.carbs > 0 && (
            <div className="text-slate-300 text-[11px] flex justify-between">
              <span>Carbs:</span>
              <span className="font-semibold text-emerald-300">{item.carbs} g</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="displayTime"
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 10, fill: '#64748b' }}
            />
            <YAxis
              domain={[40, 300]}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 10, fill: '#64748b' }}
              unit=" mg/dL"
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Target Glycemic Range Band (70 - 180 mg/dL) */}
            <ReferenceArea
              y1={70}
              y2={180}
              fill="#14b8a6"
              fillOpacity={0.06}
              stroke="#14b8a6"
              strokeOpacity={0.15}
            />

            {/* Hypoglycemia Critical Threshold Line */}
            <ReferenceLine
              y={70}
              stroke="#e11d48"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{ value: '70 mg/dL (Hypo Alert)', fill: '#e11d48', fontSize: 10, position: 'insideBottomRight' }}
            />

            {/* Hyperglycemia Reference Line */}
            <ReferenceLine
              y={180}
              stroke="#d97706"
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{ value: '180 mg/dL (High)', fill: '#d97706', fontSize: 10, position: 'insideTopRight' }}
            />

            {/* Optional heart rate stream */}
            {showHeartRate && (
              <Line
                type="monotone"
                dataKey="heartRate"
                stroke="#f43f5e"
                strokeWidth={1.2}
                dot={false}
                strokeDasharray="2 2"
              />
            )}

            {/* Glucose Trend Line */}
            <Line
              type="monotone"
              dataKey="glucose"
              stroke="#0d9488"
              strokeWidth={2.2}
              dot={false}
              activeDot={{ r: 5, fill: '#0f766e', stroke: '#fff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default GlucoseTimeSeriesChart;
