import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { StockCard } from './components/StockCard';
import { StockChart } from './components/StockChart';
import { RecentSearches } from './components/RecentSearches';
import { ArchitectureModal } from './components/ArchitectureModal';
import { AlertCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { getApiUrl } from './config';
import type { StockResponse, HealthResponse, SearchHistoryItem } from './types';

const STORAGE_KEY = 'stockquote_search_history_v1';

export function App() {
  const [currentQuote, setCurrentQuote] = useState<StockResponse | null>(null);
  const [lastSearchedSymbol, setLastSearchedSymbol] = useState<string>('MSFT');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [showArchitecture, setShowArchitecture] = useState(false);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Fetch backend health status
  const checkHealth = async () => {
    setLoadingHealth(true);
    try {
      const res = await fetch(getApiUrl('/api/health'));
      if (res.ok) {
        const data: HealthResponse = await res.json();
        setHealth(data);
      } else {
        setHealth(null);
      }
    } catch (err) {
      console.warn('Backend health check error:', err);
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  // Perform stock search
  const handleSearch = async (symbol: string) => {
    const cleanSym = symbol.trim().toUpperCase();
    setLastSearchedSymbol(cleanSym);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetch(getApiUrl('/api/stock'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: cleanSym }),
      });

      if (!response.ok) {
        let errDetail = 'Failed to fetch stock quote';
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || errDetail;
        } catch {
          errDetail = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errDetail);
      }

      const data: StockResponse = await response.json();
      setCurrentQuote(data);

      // Save to recent search history
      setSearchHistory((prev) => {
        const filtered = prev.filter((item) => item.symbol !== data.symbol);
        const updated: SearchHistoryItem[] = [
          {
            symbol: data.symbol,
            price: data.price,
            currency: data.currency,
            trading_date: data.trading_date,
            timestamp: Date.now(),
            saved_to_azure: data.saved_to_azure,
            azure_save_status: data.azure_save_status,
            is_mock: data.is_mock,
          },
          ...filtered,
        ].slice(0, 8); // Keep top 8

        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        } catch {
          // ignore localStorage errors
        }
        return updated;
      });
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred while querying the stock.');
      // Clear stale quote display on failed live request
      setCurrentQuote(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setSearchHistory([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  };

  // Initial load
  useEffect(() => {
    checkHealth();
    // Default search for MSFT on startup
    handleSearch('MSFT');
  }, []);

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans grid-bg selection:bg-emerald-500/20 selection:text-emerald-300">
      <Navbar
        health={health}
        loadingHealth={loadingHealth}
        onOpenArchitecture={() => setShowArchitecture(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Mock Mode Notice Banner if mock fallback is active */}
        {currentQuote?.is_mock && (
          <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-600/40 flex items-start sm:items-center space-x-3 text-amber-200">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5 sm:mt-0" />
            <div className="flex-1 text-xs">
              <span className="font-bold">Development Mode Active:</span> Live Microsoft Foundry
              Agent credentials or Alpha Vantage MCP access not detected. Displaying realistic
              test quotes and simulating Azure integration. Configure your `.env` with Azure credentials
              to activate live Foundry agent runs.
            </div>
          </div>
        )}

        {/* Hero & Search Header */}
        <section className="text-center space-y-4 pt-2">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-navy-900 border border-navy-800 text-xs font-mono text-emerald-400 shadow-inner">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Microsoft Foundry AI Agent + Alpha Vantage MCP + Azure Logic App</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white font-mono">
            StockQuote <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">AI</span>
          </h1>

          <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-400">
            Query verified daily closing stock prices via Microsoft Foundry AI agents and Alpha Vantage MCP,
            with automatic persistence to Azure Table Storage via Logic App.
          </p>

          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            activeSymbol={currentQuote?.symbol || ''}
          />
        </section>

        {/* Error Alert */}
        {errorMessage && (
          <div className="max-w-3xl mx-auto p-4 rounded-xl bg-rose-950/40 border border-rose-600/40 text-rose-200 flex items-start space-x-3 animate-fadeIn">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 text-xs font-mono">
              <span className="font-bold">Query Error:</span> {errorMessage}
            </div>
            <button
              onClick={() => handleSearch(lastSearchedSymbol || 'MSFT')}
              className="text-xs underline text-rose-300 hover:text-white"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading && !currentQuote && (
          <div className="w-full bg-navy-900 border border-navy-800 rounded-2xl p-8 space-y-6 animate-pulse">
            <div className="h-10 bg-navy-800 rounded-lg w-1/3" />
            <div className="h-20 bg-navy-800 rounded-lg w-1/2" />
            <div className="grid grid-cols-4 gap-4">
              <div className="h-16 bg-navy-800 rounded-lg" />
              <div className="h-16 bg-navy-800 rounded-lg" />
              <div className="h-16 bg-navy-800 rounded-lg" />
              <div className="h-16 bg-navy-800 rounded-lg" />
            </div>
          </div>
        )}

        {/* Stock Information Card & Price Chart */}
        {currentQuote && (
          <section className="space-y-6">
            <StockCard quote={currentQuote} />

            {currentQuote.history && currentQuote.history.length > 0 && (
              <StockChart
                history={currentQuote.history}
                symbol={currentQuote.symbol}
                currency={currentQuote.currency}
              />
            )}
          </section>
        )}

        {/* Recent Search History */}
        <section>
          <RecentSearches
            history={searchHistory}
            onSelect={handleSearch}
            onClear={handleClearHistory}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-navy-800 bg-navy-950 py-6 mt-12 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            StockQuote AI — Powered by Microsoft Foundry & Alpha Vantage MCP
          </div>
          <div>
            Azure Storage Table: <span className="text-slate-400">StockQuotes</span> | Logic App: <span className="text-slate-400">stockworkflow616</span>
          </div>
        </div>
      </footer>

      {/* Architecture Modal */}
      <ArchitectureModal
        isOpen={showArchitecture}
        onClose={() => setShowArchitecture(false)}
      />
    </div>
  );
}

export default App;
