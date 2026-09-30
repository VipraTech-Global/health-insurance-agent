import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A directly proxied Django API needs its trailing slash preserved.
  // The existing nginx-backed runtime retains its default redirect behavior.
  skipTrailingSlashRedirect: Boolean(process.env.COVERGUIDE_BACKEND_URL),
  async rewrites() {
    const backend = process.env.COVERGUIDE_BACKEND_URL ?? "http://127.0.0.1:8018";
    const suffix = process.env.COVERGUIDE_BACKEND_URL ? "/" : "";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*${suffix}` }];
  },
};

export default nextConfig;
