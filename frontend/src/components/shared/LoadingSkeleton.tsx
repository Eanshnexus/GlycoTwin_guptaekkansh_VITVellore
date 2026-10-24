import React from 'react';

export interface LoadingSkeletonProps {
  rows?: number;
  lines?: number;
  height?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  rows,
  lines,
  height = 'h-12',
}) => {
  const count = lines || rows || 3;
  return (
    <div className="space-y-3 w-full animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={`bg-slate-200/70 rounded-lg w-full ${height}`} />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
