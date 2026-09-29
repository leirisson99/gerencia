"use client"

import { Logo } from "@/components/brand/logo"
import { Button } from "@/components/ui/button"

/**
 * Falha ao carregar uma página (ex.: API fora do ar). O erro já é registrado no servidor;
 * em produção a mensagem original nem chega aqui.
 */
export default function ErroPagina({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <div className="flex min-h-dvh flex-col px-4 py-8 sm:px-10 sm:py-10">
      <Logo className="self-start text-xl" href="/" />
      <main className="flex w-full max-w-100 flex-1 flex-col justify-center py-12 sm:ml-[12vw]">
        <h1 className="text-title">Não foi possível carregar esta página</h1>
        <p className="mt-3 text-muted-foreground">
          O servidor não respondeu. Tente de novo em alguns instantes.
        </p>
        <div className="mt-8">
          <Button onClick={() => retry()}>Tentar de novo</Button>
        </div>
      </main>
    </div>
  )
}
