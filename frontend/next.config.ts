import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lets devices on the LAN (and any Cloudflare Tunnel hostname) load dev-mode JS chunks/HMR,
  // which Next.js 16 blocks cross-origin by default. Only matters for `next dev` - add your own
  // machine's LAN IP here (`hostname -I`) if you use LAN access while running dev mode.
  allowedDevOrigins: ["*.trycloudflare.com"],
  async rewrites() {
    // The browser only ever talks to this Next.js server. It proxies /api/* to the backend,
    // which stays bound to localhost only - never directly reachable from the LAN or internet.
    return [{ source: "/api/:path*", destination: "http://localhost:8001/api/:path*" }];
  },
};

export default nextConfig;
