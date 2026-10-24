import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Failed to load data',
  message,
  onRetry,
}) => {
  return (
    <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-start gap-3 my-4">
      <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
        <p className="text-xs text-rose-700 mt-1">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 bg-white border border-rose-300 text-rose-800 text-xs font-medium rounded-lg hover:bg-rose-50/50 cursor-pointer transition-colors shadow-2xs"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Request
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;
