import type { ReactNode } from "react"

import { Logo } from "@/components/brand/logo"

type Props = {
  titulo: string
  subtitulo?: ReactNode
  children: ReactNode
  rodape?: ReactNode
}

/** Moldura das telas públicas: coluna única alinhada à esquerda, sem cartão. */
export function AuthShell({ titulo, subtitulo, children, rodape }: Props) {
  return (
    <div className="flex min-h-dvh flex-col px-4 py-8 sm:px-10 sm:py-10">
      <Logo className="self-start text-xl" href="/entrar" />
      <main className="flex w-full max-w-100 flex-1 flex-col justify-center py-12 sm:ml-[12vw]">
        <h1 className="text-display">{titulo}</h1>
        {subtitulo && <p className="mt-3 text-muted-foreground">{subtitulo}</p>}
        <div className="mt-10">{children}</div>
        {rodape && <div className="mt-8 border-t pt-6 text-sm text-muted-foreground">{rodape}</div>}
      </main>
    </div>
  )
}
