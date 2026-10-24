import React from 'react';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  delta?: {
    value: string | number;
    isPositive?: boolean;
    neutral?: boolean;
    label?: string;
  };
  change?: {
    value: string | number;
    isPositive?: boolean;
    neutral?: boolean;
    label?: string;
  };
  icon?: React.ReactNode;
  badge?: {
    text: string;
    variant?: 'teal' | 'blue' | 'amber' | 'rose' | 'neutral' | 'warning';
  } | string;
  badgeColor?: 'teal' | 'blue' | 'amber' | 'red' | 'slate';
  tooltip?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  delta,
  change,
  icon,
  badge,
  badgeColor = 'teal',
  tooltip,
}) => {
  const effectiveChange = delta || change;

  const badgeText = typeof badge === 'object' ? badge.text : badge;
  const badgeVariant = typeof badge === 'object' ? badge.variant : badgeColor;

  const getBadgeStyle = () => {
    switch (badgeVariant) {
      case 'teal':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'blue':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'amber':
      case 'warning':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'rose':
      case 'red':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'slate':
      case 'neutral':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          <span title={tooltip}>{title}</span>
          {icon && <span className="text-slate-400">{icon}</span>}
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
            {value}
          </span>
          {badgeText && (
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getBadgeStyle()}`}
            >
              {badgeText}
            </span>
          )}
        </div>
      </div>

      {(subtitle || effectiveChange) && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          {subtitle && <span>{subtitle}</span>}
          {effectiveChange && (
            <span
              className={`font-medium ${
                effectiveChange.neutral
                  ? 'text-slate-600'
                  : effectiveChange.isPositive
                  ? 'text-teal-600'
                  : 'text-rose-600'
              }`}
            >
              {effectiveChange.value}{' '}
              {effectiveChange.label && (
                <span className="text-slate-400 font-normal">({effectiveChange.label})</span>
              )}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
