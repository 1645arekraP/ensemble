import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This ensures all paths are treated as if they have a trailing slash,
  // making it compatible with Django.
  trailingSlash: true,

  async rewrites() {
    return [
     {
        source: '/api/:path*/',
        destination: 'http://127.0.0.1:8000/api/:path*/',
      },
      // Fallback for paths that DO NOT end in a slash
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
