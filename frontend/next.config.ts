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
      // Note: /api/v1/moat/overall is handled by a custom API route (app/api/v1/moat/overall/route.ts)
      // with extended timeout, so it's excluded from the proxy.
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
        // Custom routes take precedence over rewrites, so our API route will handle /api/v1/moat/overall
      },
      {
        source: "/api/audio/:path*",
        destination: `${backendUrl}/api/audio/:path*`,
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
