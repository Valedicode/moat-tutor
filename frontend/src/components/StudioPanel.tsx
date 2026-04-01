"use client";

import { useState } from "react";
import { StudioCard } from "@/components/studio/StudioCard";
import { StudioCardExpanded } from "@/components/studio/StudioCardExpanded";
import { PriceChartView } from "@/components/studio/views/PriceChartView";
import { OverallMoatView } from "@/components/studio/views/OverallMoatView";

type StudioPanelProps = {
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  startYear?: number;
  endYear?: number;
};

type CardId = "price-chart" | "overall-moat";

export function StudioPanel({
  ticker,
  startDate,
  endDate,
  startYear,
  endYear,
}: StudioPanelProps) {
  const [expandedCard, setExpandedCard] = useState<CardId | null>(null);
  const [loadingCard, setLoadingCard] = useState<CardId | null>(null);

  const handleCardClick = (cardId: CardId) => {
    if (expandedCard === cardId) {
      setExpandedCard(null);
    } else {
      setLoadingCard(cardId);
      setExpandedCard(cardId);
      // Clear loading after a short delay (actual loading handled by child components)
      setTimeout(() => setLoadingCard(null), 300);
    }
  };

  // Check if dates represent the full 2000-2025 range
  const isFullRange =
    startYear === 2000 && endYear === 2025;

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto pr-2 scrollbar-hide space-y-3">
        {/* Overall Moat Score Card - Always first */}
        {ticker && (
          <>
            <StudioCard
              id="overall-moat"
              title="Overall Moat Score"
              description="Comprehensive moat analysis across full historical range (2000-2025)"
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
              }
              available={!!ticker}
              onClick={() => handleCardClick("overall-moat")}
              isExpanded={expandedCard === "overall-moat"}
              isLoading={loadingCard === "overall-moat"}
            />
            {expandedCard === "overall-moat" && (
              <StudioCardExpanded onCollapse={() => setExpandedCard(null)}>
                <OverallMoatView
                  ticker={ticker}
                  startDate={startDate}
                  endDate={endDate}
                  useFullRange={isFullRange}
                  isExpanded={expandedCard === "overall-moat"}
                />
              </StudioCardExpanded>
            )}
          </>
        )}

        {/* Price Chart Card */}
        <StudioCard
          id="price-chart"
          title="Price Chart"
          description="Interactive price and volume analysis for selected period"
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3v18h18" />
              <path d="M18 17l-5-5-4 4-3-3" />
            </svg>
          }
          available={!!ticker}
          onClick={() => handleCardClick("price-chart")}
          isExpanded={expandedCard === "price-chart"}
          isLoading={loadingCard === "price-chart"}
        />
        {expandedCard === "price-chart" && (
          <StudioCardExpanded onCollapse={() => setExpandedCard(null)}>
            <PriceChartView ticker={ticker} startDate={startDate} endDate={endDate} />
          </StudioCardExpanded>
        )}

        {/* Index Cards — placeholder */}
        <StudioCard
          id="index-cards"
          title="Index Cards"
          description="Benchmark and ETF index context beside your company view. Coming soon."
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
          }
          available={false}
          onClick={() => {}}
          isExpanded={false}
          isLoading={false}
        />

        {/* Milestone tracking — placeholder */}
        <StudioCard
          id="milestone-tracking"
          title="Milestone Tracking"
          description="Moat-relevant events and milestones over your selected period. Next feature."
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="22" x2="5" y2="4" />
              <path d="M5 4h14l-4 5 4 5H5V4z" strokeLinejoin="round" />
            </svg>
          }
          available={false}
          onClick={() => {}}
          isExpanded={false}
          isLoading={false}
        />
      </div>
    </div>
  );
}
