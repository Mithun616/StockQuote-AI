import React from 'react';
import { X, ArrowRight, Cloud, Database, Cpu, Server, Shield } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ArchitectureModal: React.FC<ArchitectureModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-4xl bg-navy-900 border border-navy-750 rounded-2xl shadow-2xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-navy-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 pb-6 border-b border-navy-800">
          <div className="p-2.5 rounded-xl bg-azure-500/20 text-sky-400 border border-azure-500/30">
            <Cloud className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white font-mono">StockQuote AI Architecture</h3>
            <p className="text-xs text-slate-400 font-mono">
              Live Azure Cloud Infrastructure & Data Flow
            </p>
          </div>
        </div>

        {/* Flow Diagram */}
        <div className="py-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center text-center">
            {/* Step 1 */}
            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-2">
                <span className="font-mono font-bold text-sm">1</span>
              </div>
              <h5 className="font-mono font-bold text-xs text-white">React UI</h5>
              <p className="text-[11px] text-slate-400 mt-1">Ticker Search & Charts</p>
            </div>

            <div className="hidden md:flex justify-center text-slate-600">
              <ArrowRight className="w-5 h-5" />
            </div>

            {/* Step 2 */}
            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center">
              <div className="h-10 w-10 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center mb-2">
                <Server className="w-5 h-5" />
              </div>
              <h5 className="font-mono font-bold text-xs text-white">FastAPI</h5>
              <p className="text-[11px] text-slate-400 mt-1">Validation & Azure Auth</p>
            </div>

            <div className="hidden md:flex justify-center text-slate-600">
              <ArrowRight className="w-5 h-5" />
            </div>

            {/* Step 3 */}
            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center">
              <div className="h-10 w-10 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-2">
                <Cpu className="w-5 h-5" />
              </div>
              <h5 className="font-mono font-bold text-xs text-white">Foundry AI</h5>
              <p className="text-[11px] text-slate-400 mt-1">StockQuoteAgent + MCP</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center text-center">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-2">
                <span className="font-mono font-bold text-xs">MCP</span>
              </div>
              <h5 className="font-mono font-bold text-xs text-white">Alpha Vantage MCP</h5>
              <p className="text-[11px] text-slate-400 mt-1">TIME_SERIES_DAILY Tool</p>
            </div>

            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center text-center">
              <div className="h-10 w-10 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center mb-2">
                <Cloud className="w-5 h-5" />
              </div>
              <h5 className="font-mono font-bold text-xs text-white">Azure Logic App</h5>
              <p className="text-[11px] text-slate-400 mt-1">stockworkflow616 (HTTP POST)</p>
            </div>

            <div className="p-4 rounded-xl bg-navy-950 border border-navy-800 flex flex-col items-center text-center">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-2">
                <Database className="w-5 h-5" />
              </div>
              <h5 className="font-mono font-bold text-xs text-white">Table Storage</h5>
              <p className="text-[11px] text-slate-400 mt-1">stockagent / StockQuotes</p>
            </div>
          </div>

          {/* Existing Azure Resource Specs */}
          <div className="bg-navy-950 p-5 rounded-xl border border-navy-800 space-y-3 font-mono text-xs">
            <h5 className="text-emerald-400 font-bold uppercase tracking-wider flex items-center">
              <Shield className="w-4 h-4 mr-2" /> Verified Azure Resources
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
              <div>
                <span className="text-slate-500">Resource Group:</span> stock-agent-rg
              </div>
              <div>
                <span className="text-slate-500">Foundry Resource:</span> stock-foundry-us616
              </div>
              <div>
                <span className="text-slate-500">Foundry Project:</span> StockQuotesAgentUS
              </div>
              <div>
                <span className="text-slate-500">Foundry Agent:</span> StockQuoteAgent
              </div>
              <div>
                <span className="text-slate-500">Model Deployment:</span> gpt-5-mini
              </div>
              <div>
                <span className="text-slate-500">MCP Protocol:</span> Alpha Vantage TIME_SERIES_DAILY
              </div>
              <div>
                <span className="text-slate-500">Logic App:</span> stockworkflow616
              </div>
              <div>
                <span className="text-slate-500">Storage Account:</span> stockagent (StockQuotes table)
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-navy-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-navy-800 hover:bg-navy-750 text-white rounded-xl text-xs font-mono font-bold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
