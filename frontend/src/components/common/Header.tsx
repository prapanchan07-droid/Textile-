import React from 'react';
import { Factory, Server, ShieldCheck } from 'lucide-react';
import { StatusDot } from '../ui/StatusDot';
import { Badge } from '../ui/Badge';

interface HeaderProps {
  apiStatus: 'healthy' | 'unhealthy' | 'degraded';
  dbStatus: 'healthy' | 'unhealthy' | 'degraded';
}

export const Header: React.FC<HeaderProps> = ({ apiStatus, dbStatus }) => {
  return (
    <header className="bg-factory-surface border-b border-factory-border px-6 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-factory-accent/10 border border-factory-accent/30 p-2 rounded-xl text-factory-accent">
            <Factory className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-wide">AI FACTORY MANAGER</h1>
              <Badge variant="indigo" size="sm">Ashok Textiles</Badge>
            </div>
            <p className="text-xs text-slate-400">Enterprise Decision-Support Platform • Module 01 Foundation</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-300">
          <div className="flex items-center gap-2 bg-factory-card border border-factory-border px-3 py-1.5 rounded-lg">
            <Server className="w-4 h-4 text-slate-400" />
            <span>API Service</span>
            <StatusDot status={apiStatus} />
          </div>

          <div className="flex items-center gap-2 bg-factory-card border border-factory-border px-3 py-1.5 rounded-lg">
            <ShieldCheck className="w-4 h-4 text-slate-400" />
            <span>Database</span>
            <StatusDot status={dbStatus} />
          </div>
        </div>
      </div>
    </header>
  );
};
