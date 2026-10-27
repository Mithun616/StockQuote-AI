import React, { useState } from 'react';
import { Search, Loader2, Sparkles, X, TrendingUp } from 'lucide-react';

interface SearchBarProps {
  onSearch: (symbol: string) => void;
  isLoading: boolean;
  activeSymbol: string;
}

const POPULAR_TICKERS = [
  { symbol: 'MSFT', label: 'Microsoft' },
  { symbol: 'AAPL', label: 'Apple' },
  { symbol: 'NVDA', label: 'NVIDIA' },
  { symbol: 'TSLA', label: 'Tesla' },
  { symbol: 'GOOGL', label: 'Alphabet' },
  { symbol: 'AMZN', label: 'Amazon' },
];

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading, activeSymbol }) => {
  const [inputValue, setInputValue] = useState('');
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = inputValue.trim().toUpperCase();

    if (!clean) {
      setValidationError('Please enter a ticker symbol (e.g., MSFT)');
      return;
    }

    if (!/^[A-Z0-9.]{1,10}$/.test(clean)) {
      setValidationError('Invalid symbol format. Use 1-10 uppercase letters or dots.');
      return;
    }

    setValidationError('');
    onSearch(clean);
  };

  const handleSelectQuickTicker = (ticker: string) => {
    setInputValue(ticker);
    setValidationError('');
    onSearch(ticker);
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
            {isLoading ? (
              <Loader2 className="h-5 w-5 text-emerald-400 animate-spin" />
            ) : (
              <Search className="h-5 w-5 text-slate-400 group-focus-within:text-emerald-400 transition-colors" />
            )}
          </div>

          <input
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value.toUpperCase());
              if (validationError) setValidationError('');
            }}
            placeholder="Search stock ticker (e.g. MSFT, AAPL, NVDA, TSLA)..."
            disabled={isLoading}
            className="w-full pl-12 pr-28 py-4 bg-navy-900 border-2 border-navy-800 rounded-2xl text-lg font-mono text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 shadow-2xl shadow-navy-950 transition-all duration-200"
          />

          {inputValue && (
            <button
              type="button"
              onClick={() => {
                setInputValue('');
                setValidationError('');
              }}
              className="absolute right-24 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-navy-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="absolute right-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 disabled:from-navy-800 disabled:to-navy-800 disabled:text-slate-600 text-navy-950 font-bold rounded-xl text-sm flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20 disabled:shadow-none transition-all duration-200"
          >
            <span>Quote</span>
            <TrendingUp className="w-4 h-4 ml-1" />
          </button>
        </div>

        {validationError && (
          <p className="mt-2 text-xs text-rose-400 font-mono pl-2 animate-fadeIn">
            {validationError}
          </p>
        )}
      </form>

      {/* Popular stock quick-select pills */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs text-slate-400 font-mono flex items-center mr-1">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400 mr-1" />
          Popular:
        </span>
        {POPULAR_TICKERS.map((t) => {
          const isActive = activeSymbol === t.symbol;
          return (
            <button
              key={t.symbol}
              type="button"
              onClick={() => handleSelectQuickTicker(t.symbol)}
              disabled={isLoading}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all duration-150 ${
                isActive
                  ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/10'
                  : 'bg-navy-900/90 border-navy-800 text-slate-300 hover:border-navy-700 hover:bg-navy-850 hover:text-white'
              }`}
            >
              <span className="font-bold">{t.symbol}</span>
              <span className="text-slate-400 ml-1.5 hidden sm:inline text-[11px]">{t.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
