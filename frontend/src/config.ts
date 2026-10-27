/**
 * StockQuote AI Frontend Configuration
 * Manages API Base URL resolution for local and cloud environments.
 */

// Reads VITE_API_BASE_URL from environment variables (defaults to empty string for relative paths / Vite proxy in local dev)
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || '';

// Clean any trailing slash
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

/**
 * Returns full URL for a given API endpoint.
 * E.g., getApiUrl('/api/health') -> 'https://<backend>/api/health' or '/api/health'
 */
export const getApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${cleanEndpoint}`;
};
