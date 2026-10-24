import React from 'react';
import { Database } from 'lucide-react';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
}) => {
  return (
    <div className="bg-white border border-dashed border-slate-200 rounded-xl p-10 text-center flex flex-col items-center justify-center my-6">
      <div className="w-12 h-12 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400 mb-3">
        {icon || <Database className="w-6 h-6" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm mt-1">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium rounded-lg cursor-pointer transition-colors shadow-xs"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
