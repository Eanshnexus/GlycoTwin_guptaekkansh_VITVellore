import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Cell,
  CartesianGrid
} from 'recharts';
import type { PersonalisationItem } from '../../types/api';

export interface PersonalisationDeltaChartProps {
  data?: PersonalisationItem[];
  participants?: PersonalisationItem[];
  metricType?: 'brier' | 'f1';
  height?: number;
}

export const PersonalisationDeltaChart: React.FC<PersonalisationDeltaChartProps> = ({
  data,
  participants,
  metricType = 'brier',
  height = 320,
}) => {
  const items = participants || data || [];

  if (!items || items.length === 0) {
    return null;
  }

  const chartData = items.map((d) => {
    const delta = metricType === 'brier' ? d.delta_brier : d.delta_f1;
    return {
      pid: d.participant_id.replace('HUPA', 'P'),
      fullPid: d.participant_id,
      delta: delta != null ? Number(delta.toFixed(4)) : 0,
      popScore: metricType === 'brier' ? d.pop_brier : d.pop_f1,
      persScore: metricType === 'brier' ? d.pers_brier : d.pers_f1,
      status: d.adaptation_status,
      isFallback: d.adaptation_status !== 'personalised',
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700/80 space-y-1 z-50">
          <div className="font-bold text-slate-200">{item.fullPid}</div>
          <div className="text-[11px] text-slate-400">
            Status:{' '}
            <span className={item.isFallback ? 'text-amber-400 font-semibold' : 'text-teal-400 font-semibold'}>
              {item.status}
            </span>
          </div>
          <div className="pt-1 border-t border-slate-800 space-y-0.5 text-[11px]">
            <div>Population {metricType === 'brier' ? 'Brier' : 'F1'}: {item.popScore != null ? item.popScore.toFixed(4) : 'N/A'}</div>
            <div>Personalised {metricType === 'brier' ? 'Brier' : 'F1'}: {item.persScore != null ? item.persScore.toFixed(4) : 'N/A'}</div>
            <div className="font-semibold text-teal-300">
              Paired Delta ({metricType === 'brier' ? 'ΔBrier' : 'ΔF1'}): {item.delta > 0 ? `+${item.delta}` : item.delta}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="pid"
              interval={0}
              angle={-45}
              textAnchor="end"
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 9, fill: '#64748b' }}
            />
            <YAxis
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tick={{ fontSize: 10, fill: '#64748b' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1} />
            <Bar dataKey="delta" radius={[2, 2, 0, 0]}>
              {chartData.map((entry, index) => {
                let color = '#0d9488'; // Teal for improvement (negative delta for Brier)
                if (entry.isFallback) {
                  color = '#f59e0b'; // Amber for fallback
                } else if (metricType === 'brier' && entry.delta > 0) {
                  color = '#e11d48'; // Rose for degradation
                }
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PersonalisationDeltaChart;
