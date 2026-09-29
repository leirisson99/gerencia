import type { Metadata } from "next";
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
