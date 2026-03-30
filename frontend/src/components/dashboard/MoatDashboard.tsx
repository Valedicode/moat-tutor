"use client";

import { useEffect, useState } from "react";
import { StockChart, MoatRadar, type MoatScores } from "@/components/charts";
import { getChartData, type ChartDataResponse, type MoatAssessment } from "@/lib/moatTutorApi";
import { availableCompanies } from "@/constants/companies";

interface MoatDashboardProps {
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  initialMoatAssessment?: MoatAssessment | null;
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
  initialMoatAssessment,
}: MoatDashboardProps) {
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use the moat assessment passed from chat, or fallback to mock data
  const moatAssessment = initialMoatAssessment;

  // Convert MoatAssessment to MoatScores for radar chart
  const moatScores: MoatScores = moatAssessment ? {
    networkEffects: moatAssessment.network_effects.score,
    switchingCosts: moatAssessment.switching_costs.score,
    intangibleAssets: moatAssessment.intangible_assets.score,
    costAdvantages: moatAssessment.cost_advantages.score,
    efficientScale: moatAssessment.efficient_scale.score,
  } : (ticker ? (MOCK_MOAT_SCORES[ticker] || DEFAULT_SCORES) : DEFAULT_SCORES);

  // Get company name from ticker
  const companyName = ticker
    ? availableCompanies.find((c) => c.ticker === ticker)?.name || ticker
    : "";

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
    <div className="flex h-full flex-col gap-4">
      {/* Header Alert */}
      <div className="rounded-xl border p-3" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
        <h2 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--risk)" }}>
          {ticker ? `${companyName} Analysis` : "Select a company"}
        </h2>
      </div>

      {/* Main Content Stack */}
      <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2 scrollbar-hide">
        {/* Stock Chart */}
        <div className="flex flex-col gap-3 flex-shrink-0">
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Price Chart
          </h3>
          <div
            className="relative rounded-xl border p-3"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--background)",
              minHeight: "220px",
            }}
          >
            {isLoading && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div
                    className="mb-2 inline-block h-6 w-6 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"
                    style={{ color: "var(--accent)" }}
                  />
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    Loading...
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-xs font-semibold" style={{ color: "var(--risk)" }}>
                    Error loading chart
                  </p>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {error}
                  </p>
                </div>
              </div>
            )}

            {!isLoading && !error && chartData && (
              <StockChart data={chartData} showVolume={false} height={200} />
            )}

            {!isLoading && !error && !chartData && !ticker && (
              <div className="flex h-full items-center justify-center">
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Select a company
                </p>
              </div>
            )}
          </div>

          {chartData && (
            <div className="rounded-xl border p-2" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    Period Return
                  </span>
                  <p
                    className="text-base font-bold"
                    style={{
                      color: priceChange >= 0 ? "#10b981" : "#ef4444",
                    }}
                  >
                    {priceChange >= 0 ? "▲" : "▼"} {Math.abs(priceChange).toFixed(2)}%
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    Range
                  </span>
                  <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                    ${Math.min(...chartData.low).toFixed(2)} - $
                    {Math.max(...chartData.high).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Moat Radar */}
        <div className="flex flex-col gap-3 flex-shrink-0">
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Moat Analysis
          </h3>
          <div
            className="flex flex-col gap-3 rounded-xl border p-4"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--background)",
            }}
          >
            {/* Moat Rating Badge - only shown when we have a real assessment */}
            {moatAssessment && (
              <div className="flex items-center justify-between rounded-lg border p-2" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
                <div>
                  <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>
                    Rating
                  </span>
                  <p className="mt-0.5 text-base font-bold" style={{ 
                    color: moatAssessment.overall_rating === "Wide" ? "#10b981" : 
                           moatAssessment.overall_rating === "Narrow" ? "#eab308" : "#ef4444" 
                  }}>
                    {moatAssessment.overall_rating} Moat
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>
                    Confidence
                  </span>
                  <p className="mt-0.5 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                    {moatAssessment.overall_confidence}
                  </p>
                </div>
              </div>
            )}

            {ticker ? (
              <div className="flex flex-col items-center gap-3">
                <MoatRadar scores={moatScores} size={240} />
                
                {/* Hint when no assessment yet */}
                {!moatAssessment && (
                  <p className="text-center text-xs" style={{ color: "var(--text-tertiary)" }}>
                    Ask about moat analysis in chat
                  </p>
                )}
              </div>
            ) : (
              <div className="flex h-32 items-center justify-center">
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Select a company
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Explanation */}
      {chartData && (
        <div className="rounded-xl border p-3 flex-shrink-0" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Summary
          </h3>
          <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-primary)" }}>
            {ticker} {priceChange >= 0 ? "gained" : "declined"}{" "}
            <span className="font-semibold" style={{ color: priceChange >= 0 ? "#10b981" : "#ef4444" }}>
              {Math.abs(priceChange).toFixed(2)}%
            </span>{" "}
            from {new Date(chartData.start_date).toLocaleDateString()} to{" "}
            {new Date(chartData.end_date).toLocaleDateString()}, moving from $
            {chartData.close[0].toFixed(2)} to ${chartData.close[chartData.close.length - 1].toFixed(2)}.
          </p>
        </div>
      )}
    </div>
  );
}

