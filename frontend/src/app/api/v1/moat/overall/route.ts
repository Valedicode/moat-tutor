/**
 * Custom API route for overall moat score with extended timeout.
 * 
 * The comprehensive moat analysis can take 30-60+ seconds due to:
 * - LLM agent processing 20+ years of data
 * - Multiple data sources (ROIC, news, price)
 * - Complex reasoning and synthesis
 * 
 * This route bypasses the default Next.js proxy timeout.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';

// Extended timeout for long-running LLM analysis (2 minutes)
const TIMEOUT_MS = 120000;

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const ticker = searchParams.get('ticker');
    
    if (!ticker) {
      return NextResponse.json(
        { detail: 'Ticker parameter is required' },
        { status: 400 }
      );
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      // Forward request to backend with extended timeout
      const backendUrl = new URL(`${BACKEND_URL}/api/v1/moat/overall`);
      backendUrl.searchParams.set('ticker', ticker);
      
      const response = await fetch(backendUrl.toString(), {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorDetail = `Backend error: ${response.status}`;
        
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorJson.message || errorDetail;
        } catch {
          // If not JSON, use the raw text
          if (errorText) {
            errorDetail = errorText;
          }
        }
        
        return NextResponse.json(
          { detail: errorDetail },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return NextResponse.json(
            { 
              detail: `Analysis timeout after ${TIMEOUT_MS / 1000}s. The comprehensive moat analysis is taking longer than expected. Please try again.` 
            },
            { status: 504 }
          );
        }
        
        return NextResponse.json(
          { detail: `Request failed: ${error.message}` },
          { status: 500 }
        );
      }
      
      throw error;
    }
  } catch (error) {
    console.error('Overall moat API error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}

// Set route segment config for extended timeout
export const maxDuration = 120; // 2 minutes (Vercel function timeout)
