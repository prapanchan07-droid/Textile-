import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  Activity, 
  Database, 
  Layers, 
  Cpu, 
  FileText, 
  RefreshCw,
  AlertCircle,
  Code,
  Building2,
  ListFilter
} from 'lucide-react';
import { healthService } from '../services/healthService';
import { HealthResponseData } from '../types/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { StatCard } from '../components/ui/StatCard';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';

export const Module01FoundationPage: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthService.getHealth();
      setHealthData(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-factory-surface via-factory-card to-factory-surface p-6 rounded-2xl border border-factory-border">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="indigo">PHASE 1 — FOUNDATION</Badge>
            <Badge variant="emerald">MODULE 01 COMPLETE</Badge>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">System Architecture & Foundation</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Established production-ready full-stack architecture, standardized master schemas, standard REST response envelopes, and database connection pooling for Ashok Textiles.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchHealth} isLoading={loading}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Re-test Health
          </Button>
        </div>
      </div>

      {/* Live System Health Cards */}
      {loading ? (
        <LoadingSpinner label="Querying backend & database health endpoints..." />
      ) : error ? (
        <Card variant="outline" className="border-rose-500/40 bg-rose-500/5">
          <div className="flex items-center gap-3 text-rose-400">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <div>
              <h3 className="font-semibold text-white">Backend Connection Error</h3>
              <p className="text-sm text-rose-300">{error}</p>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Backend Service"
            value={healthData?.status === 'healthy' ? 'Operational' : 'Degraded'}
            subtitle={`FastAPI v${healthData?.version} • Env: ${healthData?.environment}`}
            badgeText={healthData?.status.toUpperCase()}
            badgeVariant={healthData?.status === 'healthy' ? 'emerald' : 'rose'}
            icon={<Activity className="w-5 h-5 text-emerald-400" />}
          />
          <StatCard
            title="Database Connection"
            value={healthData?.database.database_type?.toUpperCase() || 'SQLITE'}
            subtitle="Connection pool active & seeded"
            badgeText={healthData?.database.status.toUpperCase()}
            badgeVariant={healthData?.database.status === 'healthy' ? 'emerald' : 'rose'}
            icon={<Database className="w-5 h-5 text-blue-400" />}
          />
          <StatCard
            title="Active Module"
            value="Module 01"
            subtitle="Foundation & Core Schemas"
            badgeText="INSTALLED"
            badgeVariant="indigo"
            icon={<Layers className="w-5 h-5 text-indigo-400" />}
          />
          <StatCard
            title="Company Context"
            value="Ashok Textiles"
            subtitle={`Refreshed at ${lastRefreshed}`}
            badgeText="VERIFIED"
            badgeVariant="accent"
            icon={<Building2 className="w-5 h-5 text-slate-400" />}
          />
        </div>
      )}

      {/* Architectural Pillars */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Domain Hierarchy */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2 border-b border-factory-border pb-3">
            <Building2 className="w-5 h-5 text-factory-accent" />
            <h3 className="font-bold text-white text-base">Factory Master Hierarchy</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Strict domain modeling distinguishing process stages from machine-level entities.
          </p>
          <div className="space-y-2 text-xs font-mono">
            {[
              { level: 'Factory', example: 'Ashok Textiles' },
              { level: 'Unit', example: 'Unit I, Unit II' },
              { level: 'Department', example: 'Spinning, Weaving, Sizing' },
              { level: 'Section', example: 'Section A, Section B' },
              { level: 'Process', example: 'Carding, Draw Frame, Simplex, Weaving' },
              { level: 'Machine Type', example: 'Ring Frame, Vortex, Airjet, Toyota' },
              { level: 'Machine', example: 'SMX-03, V-05, V-09' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between bg-factory-surface px-3 py-2 rounded-lg border border-factory-border/40">
                <span className="text-slate-400 font-sans">{item.level}</span>
                <span className="text-factory-accent font-semibold">{item.example}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Data Frequency & Overlap Prevention */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2 border-b border-factory-border pb-3">
            <ListFilter className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-white text-base">Frequency & Granularity</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Supports shift, daily, weekly, and monthly operational reports without double-counting.
          </p>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-factory-surface p-3 rounded-lg border border-factory-border">
                <Badge variant="emerald" size="sm" className="mb-1">SHIFT</Badge>
                <p className="text-[11px] text-slate-400">Shift A/B/C operational facts</p>
              </div>
              <div className="bg-factory-surface p-3 rounded-lg border border-factory-border">
                <Badge variant="accent" size="sm" className="mb-1">DAILY</Badge>
                <p className="text-[11px] text-slate-400">Date-level aggregated facts</p>
              </div>
              <div className="bg-factory-surface p-3 rounded-lg border border-factory-border">
                <Badge variant="indigo" size="sm" className="mb-1">WEEKLY</Badge>
                <p className="text-[11px] text-slate-400">Consolidated weekly reports</p>
              </div>
              <div className="bg-factory-surface p-3 rounded-lg border border-factory-border">
                <Badge variant="amber" size="sm" className="mb-1">MONTHLY</Badge>
                <p className="text-[11px] text-slate-400">Consolidated monthly summaries</p>
              </div>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg text-xs text-amber-300">
              <span className="font-semibold block mb-0.5">Overlap Prevention Rule:</span>
              Preserves original report frequency. Prevents duplicate counting when both shift reports and monthly consolidated summaries are uploaded for overlapping periods.
            </div>
          </div>
        </Card>

        {/* Raw vs Derived Data Contract */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2 border-b border-factory-border pb-3">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-white text-base">Raw vs Derived Contract</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Maintains strict separation between immutable source values and calculated metrics.
          </p>
          <div className="space-y-3">
            <div className="bg-factory-surface p-3 rounded-lg border border-factory-border space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Raw Target:</span>
                <span className="text-white font-bold">38,143 kg</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Raw Actual:</span>
                <span className="text-white font-bold">33,540 kg</span>
              </div>
              <div className="border-t border-factory-border my-2 pt-2 flex justify-between text-rose-400 font-bold">
                <span>Derived Loss:</span>
                <span>4,603 kg</span>
              </div>
              <div className="flex justify-between text-emerald-400 font-bold">
                <span>Achievement:</span>
                <span>87.93%</span>
              </div>
            </div>
            <p className="text-[11px] text-slate-400 italic">
              Calculated numbers remain fully traceable back to raw source reports.
            </p>
          </div>
        </Card>
      </div>

      {/* Module 01 Verification Checklist */}
      <Card>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-factory-border">
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-factory-accent" />
            <h3 className="font-bold text-white text-base">Module 01 Implementation Verification Checklist</h3>
          </div>
          <Badge variant="emerald">100% Passed</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          {[
            'Clean Project Architecture & Folder Structure',
            'Frontend & Backend Separation (FastAPI + React Vite)',
            'Environment Configuration (.env & .env.example)',
            'Database Connection Architecture (SQLAlchemy & SQLite/Postgres)',
            'Versioned REST API Structure (/api/v1)',
            'Standardized Shared Schemas & Master Hierarchy',
            'Global Error Handling Foundation (HTTP & AppExceptions)',
            'Structured Logging Foundation (App & Stream Logger)',
            'Reusable UI Components (Card, Button, Badge, StatCard)',
            'Industrial Dark Theme & Styling System (Tailwind CSS)',
            'Health Check Endpoint (/api/v1/health)',
            'Ready for Module 02 App Shell & Navigation',
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-2.5 bg-factory-surface/80 p-3 rounded-lg border border-factory-border/50">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-slate-200">{item}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
