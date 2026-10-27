import React from 'react';
import { Activity, Cloud, Database } from 'lucide-react';
import type { HealthResponse } from '../types';

interface NavbarProps {
  health: HealthResponse | null;
  loadingHealth: boolean;
  onOpenArchitecture: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ health, loadingHealth, onOpenArchitecture }) => {
  return (
    <header className="sticky top-0 z-40 border-b border-navy-800 bg-navy-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 p-0.5 shadow-lg shadow-emerald-500/20">
            <div className="h-full w-full bg-navy-950 rounded-[10px] flex items-center justify-center">
              <Activity className="h-5 w-5 text-emerald-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">StockQuote</span>
              <span className="text-xs px-1.5 py-0.5 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono hidden sm:block">
              Azure Foundry + Alpha Vantage MCP + Logic App
            </p>
          </div>
        </div>

        {/* Azure Status indicators */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          <button
            onClick={onOpenArchitecture}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-navy-850 hover:bg-navy-800 text-slate-300 border border-navy-750 transition-colors"
            title="View Azure Integration Architecture"
          >
            <Cloud className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden md:inline">Azure Architecture</span>
          </button>

          {/* Backend Health Badge */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-navy-900 border border-navy-800 text-xs font-mono">
            <span className="relative flex h-2 w-2">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  health?.status === 'HEALTHY' ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  health?.status === 'HEALTHY' ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
            </span>
            <span className="text-slate-300 hidden sm:inline">Backend:</span>
            <span
              className={
                health?.status === 'HEALTHY' ? 'text-emerald-400 font-semibold' : 'text-amber-400'
              }
            >
              {loadingHealth ? 'Checking...' : health?.status || 'Offline'}
            </span>
          </div>

          {/* Storage Account Status */}
          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-navy-900 border border-navy-800 text-xs font-mono text-slate-400">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span>Table: StockQuotes</span>
          </div>
        </div>
      </div>
    </header>
  );
};
