"use client";

import { useEffect, useState } from "react";
import { StockChart, MoatRadar, type MoatScores } from "@/components/charts";
import { getChartData, type ChartDataResponse } from "@/lib/moatTutorApi";

interface MoatDashboardProps {
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
}

// Mock MOAT scores for different companies
const MOCK_MOAT_SCORES: Record<string, MoatScores> = {
  NVDA: {
    networkEffects: 4.2,
    switchingCosts: 3.8,
    intangibleAssets: 4.7,
    costAdvantages: 4.0,
    efficientScale: 3.2,
  },
  AAPL: {
    networkEffects: 4.8,
    switchingCosts: 4.5,
    intangibleAssets: 4.9,
    costAdvantages: 3.8,
    efficientScale: 3.5,
  },
  MSFT: {
    networkEffects: 4.7,
    switchingCosts: 4.6,
    intangibleAssets: 4.5,
    costAdvantages: 4.0,
    efficientScale: 3.9,
  },
  AVGO: {
    networkEffects: 3.5,
    switchingCosts: 4.0,
    intangibleAssets: 4.2,
    costAdvantages: 3.8,
    efficientScale: 3.3,
  },
  ORCL: {
    networkEffects: 3.8,
    switchingCosts: 4.4,
    intangibleAssets: 4.0,
    costAdvantages: 3.5,
    efficientScale: 3.7,
  },
  AMD: {
    networkEffects: 3.2,
    switchingCosts: 3.0,
    intangibleAssets: 4.0,
    costAdvantages: 3.4,
    efficientScale: 2.9,
  },
  CSCO: {
    networkEffects: 4.0,
    switchingCosts: 4.2,
    intangibleAssets: 3.8,
    costAdvantages: 3.6,
    efficientScale: 3.5,
  },
  PLTR: {
    networkEffects: 3.5,
    switchingCosts: 3.7,
    intangibleAssets: 4.5,
    costAdvantages: 3.0,
    efficientScale: 3.2,
  },
  MU: {
    networkEffects: 2.8,
    switchingCosts: 2.5,
    intangibleAssets: 3.5,
    costAdvantages: 3.8,
    efficientScale: 3.0,
  },
  GOOGL: {
    networkEffects: 4.9,
    switchingCosts: 4.0,
    intangibleAssets: 4.8,
    costAdvantages: 4.3,
    efficientScale: 4.1,
  },
};

// Default scores if ticker not found
const DEFAULT_SCORES: MoatScores = {
  networkEffects: 3.0,
  switchingCosts: 3.0,
  intangibleAssets: 3.0,
  costAdvantages: 3.0,
  efficientScale: 3.0,
};

export function MoatDashboard({
  ticker = "NVDA",
  startDate = "2023-01-01",
  endDate = "2023-12-31",
}: MoatDashboardProps) {
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get MOAT scores for the selected ticker
  const moatScores = ticker ? (MOCK_MOAT_SCORES[ticker] || DEFAULT_SCORES) : DEFAULT_SCORES;

  useEffect(() => {
    const loadChartData = async () => {
      if (!ticker) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await getChartData({
          ticker,
          startDate,
          endDate,
          interval: "auto",
        });
        setChartData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chart data");
        console.error("Chart data error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadChartData();
  }, [ticker, startDate, endDate]);

  // Calculate price change
  const priceChange = chartData
    ? ((chartData.close[chartData.close.length - 1] - chartData.close[0]) /
        chartData.close[0]) *
      100
    : 0;

  return (
    <div
      className="flex h-full flex-col gap-6 rounded-[36px] border p-6"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "color-mix(in srgb, var(--surface) 75%, transparent)",
      }}
    >
      {/* Header Alert */}
      <div className="rounded-2xl border p-4" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
        <h2 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--risk)" }}>
          {ticker ? `${ticker} Price Analysis` : "Select a company to view analysis"}
        </h2>
      </div>

      {/* Main Content Grid */}
      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Stock Chart */}
        <div className="flex flex-col gap-3">
          <div
            className="relative rounded-xl border p-4"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--background)",
              minHeight: "300px",
            }}
          >
            {isLoading && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div
                    className="mb-2 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"
                    style={{ color: "var(--accent)" }}
                  />
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Loading chart data...
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-sm font-semibold" style={{ color: "var(--risk)" }}>
                    Error loading chart
                  </p>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {error}
                  </p>
                </div>
              </div>
            )}

            {!isLoading && !error && chartData && (
              <StockChart data={chartData} showVolume={true} showArea={true} height={280} />
            )}

            {!isLoading && !error && !chartData && !ticker && (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Select a company to view price chart
                </p>
              </div>
            )}
          </div>

          {chartData && (
            <div className="rounded-xl border p-3" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    Period Return
                  </span>
                  <p
                    className="text-lg font-bold"
                    style={{
                      color: priceChange >= 0 ? "#10b981" : "#ef4444",
                    }}
                  >
                    {priceChange >= 0 ? "▲" : "▼"} {Math.abs(priceChange).toFixed(2)}%
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    Price Range
                  </span>
                  <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    ${Math.min(...chartData.low).toFixed(2)} - $
                    {Math.max(...chartData.high).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Moat Radar */}
        <div
          className="flex flex-col items-center justify-center gap-4 rounded-xl border p-6"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--background)",
            minHeight: "300px",
          }}
        >
          {ticker ? (
            <MoatRadar scores={moatScores} size={280} />
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Select a company to view MOAT analysis
              </p>
            </div>
          )}
        </div>
      </div>

      {/* AI Explanation */}
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
        <h3 className="text-xs font-semibold uppercase tracking-[0.3em]" style={{ color: "var(--text-secondary)" }}>
          Price Movement Summary
        </h3>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
          {chartData ? (
            <>
              {ticker} {priceChange >= 0 ? "gained" : "declined"}{" "}
              <span className="font-semibold" style={{ color: priceChange >= 0 ? "#10b981" : "#ef4444" }}>
                {Math.abs(priceChange).toFixed(2)}%
              </span>{" "}
              from {new Date(chartData.start_date).toLocaleDateString()} to{" "}
              {new Date(chartData.end_date).toLocaleDateString()}, moving from $
              {chartData.close[0].toFixed(2)} to ${chartData.close[chartData.close.length - 1].toFixed(2)}.
              The stock reached a high of ${Math.max(...chartData.high).toFixed(2)} and a low of $
              {Math.min(...chartData.low).toFixed(2)} during this period.
            </>
          ) : (
            "Select a company and date range to view price movement analysis."
          )}
        </p>
      </div>
    </div>
  );
}

