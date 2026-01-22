"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import type { ChartDataResponse } from "@/lib/moatTutorApi";
import { availableCompanies } from "@/constants/companies";

interface StockChartProps {
  data: ChartDataResponse;
  showVolume?: boolean;
  height?: number;
  className?: string;
}

export function StockChart({
  data,
  showVolume = true,
  height = 300,
  className = "",
}: StockChartProps) {
  // Get company name from ticker
  const companyName = useMemo(() => {
    const company = availableCompanies.find((c) => c.ticker === data.ticker);
    return company?.name || data.ticker;
  }, [data.ticker]);

  // Transform API data to Recharts format
  const chartData = useMemo(() => {
    return data.dates.map((date, i) => ({
      date: new Date(date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: data.interval === "ME" ? "numeric" : undefined,
      }),
      fullDate: date,
      open: data.open[i],
      high: data.high[i],
      low: data.low[i],
      close: data.close[i],
      volume: data.volume[i],
      adjClose: data.adj_close?.[i],
    }));
  }, [data]);

  // Calculate price range for better Y-axis scaling
  const priceRange = useMemo(() => {
    const allPrices = [...data.high, ...data.low];
    const min = Math.min(...allPrices);
    const max = Math.max(...allPrices);
    const padding = (max - min) * 0.1; // 10% padding
    return {
      min: Math.floor(min - padding),
      max: Math.ceil(max + padding),
    };
  }, [data]);

  // Calculate volume range
  const volumeRange = useMemo(() => {
    const max = Math.max(...data.volume);
    return {
      min: 0,
      max: max * 2, // Double max for better visualization
    };
  }, [data]);

  const formatVolume = (value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toString();
  };

  const formatPrice = (value: number) => `$${value.toFixed(2)}`;

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor="var(--risk)"
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor="var(--risk)"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border)"
            opacity={0.3}
          />

          <XAxis
            dataKey="date"
            stroke="var(--text-tertiary)"
            style={{ fontSize: "12px" }}
            tickLine={false}
          />

          <YAxis
            yAxisId="price"
            domain={[priceRange.min, priceRange.max]}
            stroke="var(--text-tertiary)"
            style={{ fontSize: "12px" }}
            tickFormatter={formatPrice}
            tickLine={false}
          />

          {showVolume && (
            <YAxis
              yAxisId="volume"
              orientation="right"
              domain={[volumeRange.min, volumeRange.max]}
              stroke="var(--text-tertiary)"
              style={{ fontSize: "12px" }}
              tickFormatter={formatVolume}
              tickLine={false}
            />
          )}

          <Tooltip
            contentStyle={{
              backgroundColor: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "12px",
            }}
            labelStyle={{ color: "var(--text-primary)", fontWeight: 600 }}
            itemStyle={{ color: "var(--text-secondary)", fontSize: "13px" }}
            formatter={(value: number, name: string) => {
              if (name === "volume") return [formatVolume(value), "Volume"];
              return [formatPrice(value), name.charAt(0).toUpperCase() + name.slice(1)];
            }}
          />

          <Legend
            wrapperStyle={{
              paddingTop: "20px",
              fontSize: "13px",
            }}
            iconType="line"
          />

          {showVolume && (
            <Bar
              yAxisId="volume"
              dataKey="volume"
              fill="var(--accent)"
              opacity={0.3}
              radius={[4, 4, 0, 0]}
            />
          )}

          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke="var(--risk)"
            strokeWidth={2}
            dot={false}
            name="Close"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Chart Info */}
      <div className="mt-3 flex items-center justify-between text-xs" style={{ color: "var(--text-tertiary)" }}>
        <div>
          {companyName} ({data.ticker}) • {data.interval_display} • {data.data_points} points
        </div>
        <div>
          {new Date(data.start_date).toLocaleDateString()} -{" "}
          {new Date(data.end_date).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}

