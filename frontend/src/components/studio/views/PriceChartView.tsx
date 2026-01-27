"use client";

import { useState, useEffect } from "react";
import { StockChart } from "@/components/charts";
import { getChartData, type ChartDataResponse } from "@/lib/moatTutorApi";

type PriceChartViewProps = {
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
};

export function PriceChartView({ ticker, startDate, endDate }: PriceChartViewProps) {
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div
            className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"
            style={{ color: "var(--accent)" }}
          />
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Loading chart data...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-sm font-semibold mb-2" style={{ color: "var(--risk)" }}>
            Error loading chart
          </p>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!chartData) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No chart data available
        </p>
      </div>
    );
  }

  const priceChange =
    ((chartData.close[chartData.close.length - 1] - chartData.close[0]) /
      chartData.close[0]) *
    100;

  return (
    <div className="space-y-4">
      <div
        className="rounded-lg border p-3"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--surface)",
        }}
      >
        <StockChart data={chartData} showVolume={true} height={300} />
      </div>

      <div
        className="rounded-lg border p-3"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--border-subtle)",
        }}
      >
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Period Return
            </span>
            <p
              className="text-lg font-bold mt-1"
              style={{
                color: priceChange >= 0 ? "#10b981" : "#ef4444",
              }}
            >
              {priceChange >= 0 ? "▲" : "▼"} {Math.abs(priceChange).toFixed(2)}%
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Price Range
            </span>
            <p className="text-sm font-semibold mt-1" style={{ color: "var(--text-primary)" }}>
              ${Math.min(...chartData.low).toFixed(2)} - $
              {Math.max(...chartData.high).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
