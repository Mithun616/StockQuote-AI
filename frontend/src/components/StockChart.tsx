import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import type { DailyHistoricalQuote } from '../types';

interface StockChartProps {
  history: DailyHistoricalQuote[];
  symbol: string;
  currency: string;
}

export const StockChart: React.FC<StockChartProps> = ({ history, symbol, currency }) => {
  if (!history || history.length === 0) {
    return null;
  }

  // Calculate min and max for chart domain
  const prices = history.map((h) => h.close);
  const minPrice = Math.floor(Math.min(...prices) * 0.98);
  const maxPrice = Math.ceil(Math.max(...prices) * 1.02);

  const isUp = history[history.length - 1].close >= history[0].close;

  return (
    <div className="w-full bg-navy-900 border border-navy-800 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-navy-800/80 mb-6">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-navy-800 text-emerald-400">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white font-mono flex items-center space-x-2">
              <span>{symbol} Daily Close Price History</span>
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Historical daily closes from Alpha Vantage TIME_SERIES_DAILY
            </p>
          </div>
        </div>

        <div className="text-right font-mono text-xs">
          <span className="text-slate-400">Range: </span>
          <span className="text-emerald-400 font-bold">
            ${prices[0].toFixed(2)} → ${prices[prices.length - 1].toFixed(2)}
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="emeraldGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isUp ? '#10b981' : '#f43f5e'} stopOpacity={0.4} />
                <stop offset="95%" stopColor={isUp ? '#10b981' : '#f43f5e'} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
              tickFormatter={(val) => {
                // Shorten date format "2026-10-24" to "10/24"
                const parts = val.split('-');
                return parts.length === 3 ? `${parts[1]}/${parts[2]}` : val;
              }}
            />
            <YAxis
              domain={[minPrice, maxPrice]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `$${val}`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload as DailyHistoricalQuote;
                  return (
                    <div className="bg-navy-950 border border-navy-750 p-3 rounded-xl shadow-2xl font-mono text-xs space-y-1">
                      <div className="text-slate-400">{data.date}</div>
                      <div className="text-white text-base font-bold flex items-center space-x-1">
                        <span className="text-emerald-400">${data.close.toFixed(2)}</span>
                        <span className="text-xs text-slate-400 font-normal">{currency}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke={isUp ? '#10b981' : '#f43f5e'}
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#emeraldGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
