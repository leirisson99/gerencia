import type { Metadata, Viewport } from "next";
import { Inter_Tight } from "next/font/google";

import { Providers } from "@/components/providers/providers";
import "./globals.css";

const interTight = Inter_Tight({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: { default: "Gerencia", template: "%s | Gerencia" },
  description: "Controle financeiro pessoal pelo ciclo do salário.",
  // No iOS, instalado pela tela inicial, abre em tela cheia com este nome.
  appleWebApp: { capable: true, title: "Gerencia", statusBarStyle: "default" },
};

// viewport-fit=cover libera env(safe-area-inset-*) para a barra inferior no celular.
export const viewport: Viewport = {
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${interTight.variable} h-full antialiased`}>
      {/* Extensões do navegador (ex.: ColorZilla) injetam atributos no body antes da hidratação.
          Só ignora atributos deste elemento; divergências nos filhos continuam aparecendo. */}
      <body className="min-h-full" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
