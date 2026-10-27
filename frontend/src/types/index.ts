export interface DailyHistoricalQuote {
  date: string;
  close: number;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  volume?: number | null;
}

export interface StockResponse {
  symbol: string;
  price: number;
  currency: string;
  trading_date: string;
  change?: number | null;
  change_percent?: number | null;
  open_price?: number | null;
  high_price?: number | null;
  low_price?: number | null;
  volume?: number | null;
  
  // Azure integration status
  saved_to_azure: boolean;
  azure_save_status: 'SUCCESS' | 'FAILED' | 'SKIPPED' | 'NOT_CONFIGURED' | 'PENDING' | 'CACHED' | 'HISTORICAL_FALLBACK' | 'UNVERIFIED_HISTORICAL';
  azure_save_message?: string | null;
  azure_table_name: string;
  azure_logic_app: string;
  
  // Metadata
  is_mock: boolean;
  is_cached?: boolean;
  cached_at?: string | null;
  is_historical_fallback?: boolean;
  provenance_verified?: boolean;
  provenance_note?: string | null;
  data_source: string;
  retrieved_at: string;
  history: DailyHistoricalQuote[];
  raw_agent_message?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  azure_foundry_configured: boolean;
  foundry_endpoint: string;
  foundry_agent: string;
  foundry_model: string;
  logic_app_configured: boolean;
  logic_app_name: string;
  azure_table_name: string;
  mock_mode_allowed: boolean;
}

export interface SearchHistoryItem {
  symbol: string;
  price: number;
  currency: string;
  trading_date: string;
  timestamp: number;
  saved_to_azure: boolean;
  azure_save_status: string;
  is_mock: boolean;
}
