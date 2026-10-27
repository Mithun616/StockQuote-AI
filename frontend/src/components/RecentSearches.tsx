import React from 'react';
import { History, Trash2, CheckCircle, ArrowUpRight } from 'lucide-react';
import type { SearchHistoryItem } from '../types';

interface RecentSearchesProps {
  history: SearchHistoryItem[];
  onSelect: (symbol: string) => void;
  onClear: () => void;
}

export const RecentSearches: React.FC<RecentSearchesProps> = ({ history, onSelect, onClear }) => {
  if (history.length === 0) {
    return null;
  }

  return (
    <div className="w-full bg-navy-900/60 border border-navy-800/80 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between pb-3 border-b border-navy-800/80 mb-3">
        <div className="flex items-center space-x-2 text-slate-300">
          <History className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider">Recent Searches</h4>
        </div>

        <button
          onClick={onClear}
          className="text-[11px] text-slate-400 hover:text-rose-400 flex items-center space-x-1 font-mono transition-colors"
          title="Clear search history"
        >
          <Trash2 className="w-3 h-3" />
          <span>Clear</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {history.map((item) => (
          <button
            key={`${item.symbol}-${item.timestamp}`}
            onClick={() => onSelect(item.symbol)}
            className="flex items-center justify-between p-3 rounded-xl bg-navy-950/70 border border-navy-850 hover:border-emerald-500/40 hover:bg-navy-850 group transition-all text-left"
          >
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono font-black text-white group-hover:text-emerald-300 transition-colors">
                  {item.symbol}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-navy-800 text-slate-400 border border-navy-700 font-mono">
                  Historical
                </span>
                {item.saved_to_azure ? (
                  <span
                    className="inline-flex items-center text-[10px] text-emerald-400 font-mono"
                    title="Saved to Azure Table Storage"
                  >
                    <CheckCircle className="w-3 h-3 mr-0.5" /> Azure
                  </span>
                ) : (
                  <span
                    className="inline-flex items-center text-[10px] text-slate-400 font-mono"
                    title={item.azure_save_status}
                  >
                    {item.azure_save_status}
                  </span>
                )}
              </div>
              <div className="text-xs font-mono text-slate-300 mt-1 font-semibold">
                Close: ${item.price.toFixed(2)}
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                Date: {item.trading_date || 'N/A'}
              </div>
            </div>

            <div className="text-slate-500 group-hover:text-emerald-400 transition-colors">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
