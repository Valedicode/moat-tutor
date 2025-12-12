import type { NextConfig } from "next";

const rawBackendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8000";

const backendUrl = rawBackendUrl.replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Proxy backend API through Next.js to avoid CORS during development.
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
      // Optional health/monitoring endpoints
      { source: "/health", destination: `${backendUrl}/health` },
      { source: "/metrics", destination: `${backendUrl}/metrics` },
      { source: "/ready", destination: `${backendUrl}/ready` },
      { source: "/live", destination: `${backendUrl}/live` },
    ];
  },
};

export default nextConfig;
