import React from 'react';

export interface StatusBadgeProps {
  status?: string;
  label?: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'normal';
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  variant = 'neutral',
  size = 'md',
}) => {
  const text = label || status || '';
  const effectiveVariant = variant === 'normal' ? 'info' : variant;

  const variantStyles = {
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
    info: 'bg-teal-50 text-teal-700 border-teal-200',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  }[effectiveVariant];

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  }[size];

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${variantStyles} ${sizeStyles}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-75" />
      {text}
    </span>
  );
};

export default StatusBadge;
