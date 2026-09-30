import type { MetadataRoute } from "next";

// Torna o site instalável ("Adicionar à tela inicial") e abre sem a barra do navegador.
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Gerencia",
    short_name: "Gerencia",
    description: "Controle financeiro pessoal pelo ciclo do salário.",
    lang: "pt-BR",
    start_url: "/",
    scope: "/",
    display: "standalone",
    // Fundo do ícone: a tela de abertura no Android fica da mesma cor.
    background_color: "#0b1219",
    theme_color: "#000000",
    icons: [
      { src: "/icone-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icone-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      // Fundo cheio e margem de segurança: o Android recorta em círculo, gota etc.
      { src: "/icone-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
