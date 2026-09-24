import React from 'react';

export const LoadingSpinner: React.FC<{ label?: string }> = ({ label = 'Loading application architecture...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="w-10 h-10 border-4 border-factory-accent/30 border-t-factory-accent rounded-full animate-spin mb-4" />
      <p className="text-sm font-medium text-slate-400">{label}</p>
    </div>
  );
};
