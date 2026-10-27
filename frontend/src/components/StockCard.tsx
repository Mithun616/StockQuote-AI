import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Clock,
  Info,
} from 'lucide-react';
import type { StockResponse } from '../types';

interface StockCardProps {
  quote: StockResponse;
}

export const StockCard: React.FC<StockCardProps> = ({ quote }) => {
  const isPositive = (quote.change ?? 0) >= 0;

  return (
    <div className="w-full bg-navy-900 border border-navy-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
      {/* Subtle background glow */}
      <div
        className={`absolute -top-24 -right-24 w-72 h-72 rounded-full blur-3xl opacity-15 pointer-events-none ${
          isPositive ? 'bg-emerald-500' : 'bg-rose-500'
        }`}
      />

      {/* Header: Ticker & Badges */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-navy-800/80">
        <div className="flex items-center space-x-4">
          <div className="h-14 w-14 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center font-mono font-black text-2xl text-emerald-400 shadow-inner">
            {quote.symbol.slice(0, 2)}
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-3xl font-black font-mono text-white tracking-wider">
                {quote.symbol}
              </h2>
              <span className="text-xs px-2.5 py-1 rounded-md font-mono uppercase bg-navy-800 text-slate-300 border border-navy-700">
                {quote.currency}
              </span>
              {quote.is_mock && (
                <span className="text-xs px-2.5 py-1 rounded-md font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  Mock Data
                </span>
              )}
              {quote.is_cached && !quote.is_historical_fallback && (
                <span className="text-xs px-2.5 py-1 rounded-md font-mono font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30" title="Served from Azure Table Storage cache to conserve Alpha Vantage daily quota">
                  Cached Daily Close
                </span>
              )}
              {quote.is_historical_fallback && quote.provenance_verified !== false && (
                <span className="text-xs px-2.5 py-1 rounded-md font-mono font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30" title="Live Alpha Vantage quota reached. Displaying verified historical record from Azure Table Storage">
                  Verified Historical Data
                </span>
              )}
              {quote.provenance_verified === false && (
                <span className="text-xs px-2.5 py-1 rounded-md font-mono font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30" title="Provenance cannot be verified against live market provider.">
                  Unverified Historical Data
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1 flex items-center">
              <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
              Trading Close Date: <strong className={`ml-1 ${quote.provenance_verified === false ? 'text-amber-400 font-bold' : 'text-slate-300'}`}>{quote.trading_date}</strong>
              {quote.cached_at && (
                <span className="ml-3 text-slate-500 hidden sm:inline">
                  (Cached At: {quote.cached_at.slice(0, 19).replace('T', ' ')} UTC)
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Closing Price and Daily Change */}
        <div className="flex flex-col sm:items-end">
          <div className="text-4xl sm:text-5xl font-black font-mono tracking-tight text-white flex items-baseline">
            <span className="text-2xl sm:text-3xl font-bold text-slate-400 mr-1">$</span>
            {quote.price.toFixed(2)}
          </div>

          {quote.change !== null && quote.change !== undefined && (
            <div
              className={`mt-1.5 flex items-center space-x-1.5 text-sm font-mono font-bold px-2.5 py-0.5 rounded-lg border ${
                isPositive
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}
            >
              {isPositive ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {isPositive ? '+' : ''}
                {quote.change.toFixed(2)} ({isPositive ? '+' : ''}
                {quote.change_percent?.toFixed(2)}%)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-b border-navy-800/80">
        <div className="bg-navy-950/60 p-3.5 rounded-xl border border-navy-800/60">
          <span className="text-xs font-mono text-slate-400 block mb-1">Open</span>
          <span className="text-lg font-mono font-semibold text-slate-200">
            {quote.open_price ? `$${quote.open_price.toFixed(2)}` : '—'}
          </span>
        </div>
        <div className="bg-navy-950/60 p-3.5 rounded-xl border border-navy-800/60">
          <span className="text-xs font-mono text-slate-400 block mb-1">Day High</span>
          <span className="text-lg font-mono font-semibold text-emerald-300">
            {quote.high_price ? `$${quote.high_price.toFixed(2)}` : '—'}
          </span>
        </div>
        <div className="bg-navy-950/60 p-3.5 rounded-xl border border-navy-800/60">
          <span className="text-xs font-mono text-slate-400 block mb-1">Day Low</span>
          <span className="text-lg font-mono font-semibold text-rose-300">
            {quote.low_price ? `$${quote.low_price.toFixed(2)}` : '—'}
          </span>
        </div>
        <div className="bg-navy-950/60 p-3.5 rounded-xl border border-navy-800/60">
          <span className="text-xs font-mono text-slate-400 block mb-1">Volume</span>
          <span className="text-lg font-mono font-semibold text-slate-200">
            {quote.volume ? quote.volume.toLocaleString() : '—'}
          </span>
        </div>
      </div>

      {/* Azure Persistence Confirmation Status */}
      <div className="mt-6 pt-1">
        <div
          className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
            quote.saved_to_azure
              ? 'bg-emerald-950/30 border-emerald-600/40 text-emerald-200'
              : quote.azure_save_status === 'NOT_CONFIGURED'
              ? 'bg-sky-950/30 border-sky-600/40 text-sky-200'
              : 'bg-rose-950/30 border-rose-600/40 text-rose-200'
          }`}
        >
          <div className="flex items-start sm:items-center space-x-3">
            {quote.saved_to_azure ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5 sm:mt-0" />
            ) : quote.azure_save_status === 'NOT_CONFIGURED' ? (
              <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5 sm:mt-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5 sm:mt-0" />
            )}
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-sm">
                  {quote.saved_to_azure
                    ? 'Saved to Azure Table Storage'
                    : quote.azure_save_status === 'NOT_CONFIGURED'
                    ? 'Azure Logic App Save Pending Configuration'
                    : 'Azure Storage Save Failed'}
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    quote.saved_to_azure
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : quote.azure_save_status === 'NOT_CONFIGURED'
                      ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  }`}
                >
                  {quote.azure_save_status}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                {quote.azure_save_message ||
                  `Workflow: ${quote.azure_logic_app} | Table: ${quote.azure_table_name}`}
              </p>
            </div>
          </div>

          <div className="text-right font-mono text-[11px] text-slate-400 shrink-0 sm:border-l sm:border-slate-800 sm:pl-4">
            <div>
              Table: <span className="text-slate-200 font-semibold">{quote.azure_table_name}</span>
            </div>
            <div>
              Workflow: <span className="text-slate-200 font-semibold">{quote.azure_logic_app}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quote Notice Footer */}
      <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-400 font-mono gap-2 pt-2">
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>
            {quote.provenance_verified === false
              ? 'Notice: Historical record without verified market provenance. Not guaranteed market quote.'
              : quote.is_cached
              ? 'Notice: Showing verified daily close from Azure Table Storage cache. Not a live streaming quote.'
              : 'Notice: Prices are latest available daily closes (TIME_SERIES_DAILY). Not real-time streaming quotes.'}
          </span>
        </div>
        <div className="text-slate-400 text-right">
          {quote.cached_at ? `Cached: ${quote.cached_at.slice(0, 19).replace('T', ' ')} UTC` : `Retrieved: ${new Date(quote.retrieved_at).toLocaleTimeString()}`}
        </div>
      </div>
    </div>
  );
};
