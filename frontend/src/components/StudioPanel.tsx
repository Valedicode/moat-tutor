"use client";

import { useState } from "react";
import { MoatAssessment } from "@/lib/moatTutorApi";
import { StudioCard } from "@/components/studio/StudioCard";
import { StudioCardExpanded } from "@/components/studio/StudioCardExpanded";
import { PriceChartView } from "@/components/studio/views/PriceChartView";
import { MoatRadarView } from "@/components/studio/views/MoatRadarView";
import { OverallMoatView } from "@/components/studio/views/OverallMoatView";

type StudioPanelProps = {
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  moatAssessment?: MoatAssessment | null;
  startYear?: number;
  endYear?: number;
};

type CardId = "price-chart" | "moat-radar" | "overall-moat" | "news-timeline";

export function StudioPanel({
  ticker,
  startDate,
  endDate,
  moatAssessment,
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

        {/* Moat Radar Card */}
        <StudioCard
          id="moat-radar"
          title="Moat Analysis"
          description="Competitive moat characteristics from recent conversation"
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2v20M2 12h20" />
              <path d="M6.34 6.34l11.32 11.32M17.66 6.34L6.34 17.66" />
            </svg>
          }
          available={!!moatAssessment}
          onClick={() => handleCardClick("moat-radar")}
          isExpanded={expandedCard === "moat-radar"}
          isLoading={loadingCard === "moat-radar"}
        />
        {expandedCard === "moat-radar" && (
          <StudioCardExpanded onCollapse={() => setExpandedCard(null)}>
            <MoatRadarView moatAssessment={moatAssessment} />
          </StudioCardExpanded>
        )}

        {/* News Timeline Card - Placeholder */}
        <StudioCard
          id="news-timeline"
          title="News Timeline"
          description="Key events and news correlation (coming soon)"
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
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
