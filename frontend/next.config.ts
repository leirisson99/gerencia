import type { NextConfig } from "next";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Gera .next/standalone com só o necessário para rodar: é o que vai na imagem Docker.
  output: "standalone",
  // A API fica na mesma origem do site: o cookie de sessão funciona sem CORS.
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${API_URL}/api/v1/:path*` }];
  },
};

export default nextConfig;
