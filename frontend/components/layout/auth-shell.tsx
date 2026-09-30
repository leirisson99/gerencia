import type { ReactNode } from "react"

import { Logo } from "@/components/brand/logo"
import { formatarCentavos } from "@/lib/format"

type Props = {
  titulo: string
  subtitulo?: ReactNode
  children: ReactNode
  rodape?: ReactNode
}

/**
 * Moldura das telas públicas. No desktop: painel da marca (fundo invertido) à esquerda e
 * formulário à direita. No celular: a marca no topo e o formulário numa folha que sobe por cima.
 */
export function AuthShell({ titulo, subtitulo, children, rodape }: Props) {
  return (
    <div className="flex min-h-dvh flex-col bg-primary md:grid md:grid-cols-2 lg:grid-cols-[1.15fr_1fr]">
      <PainelMarca />

      <main className="relative z-10 -mt-8 flex flex-1 flex-col rounded-t-[2rem] bg-background px-6 pt-8 pb-[max(2rem,env(safe-area-inset-bottom))] md:mt-0 md:justify-center md:rounded-none md:px-12 md:py-12">
        <div className="mx-auto w-full max-w-100">
          <h1 className="text-title md:text-display">{titulo}</h1>
          {subtitulo && <p className="mt-2 text-muted-foreground md:mt-3">{subtitulo}</p>}
          {/* Campos e botão mais altos e arredondados que no resto do app: é a porta de entrada. */}
          <div className="mt-8 md:mt-10 [&_[data-slot=button]]:h-11 [&_[data-slot=button]]:rounded-xl [&_[data-slot=input]]:h-11 [&_[data-slot=input]]:rounded-xl">
            {children}
          </div>
          {rodape && (
            <div className="mt-8 border-t pt-6 text-center text-sm text-muted-foreground md:text-left">
              {rodape}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

/** Lado da marca: logo, a promessa do produto e, no desktop, uma prévia ilustrativa do dashboard. */
function PainelMarca() {
  return (
    <aside className="relative overflow-hidden px-6 pt-[calc(env(safe-area-inset-top)+1.75rem)] pb-16 text-primary-foreground md:flex md:flex-col md:p-12 lg:p-16">
      {/* Anéis decorativos ao fundo. */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-24 size-72 rounded-full border border-primary-foreground/10 md:-top-40 md:-right-40 md:size-[36rem]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-8 -right-8 size-40 rounded-full border border-primary-foreground/10 md:-top-16 md:-right-16 md:size-[22rem]"
      />

      <Logo className="relative text-xl md:text-2xl" href="/entrar" />

      <div className="relative mt-8 md:mt-auto">
        <p className="max-w-[16ch] text-[1.75rem] leading-[1.1] font-semibold tracking-tight md:text-5xl md:leading-[1.05]">
          Quanto entrou, para onde foi, quanto sobrou.
        </p>
        <p className="mt-3 max-w-[40ch] text-sm opacity-70 md:mt-4 md:text-base">
          Seu dinheiro organizado pelo ciclo do salário, com metas de poupança no seu ritmo.
        </p>
      </div>

      <Previa />

      <p className="relative mt-auto hidden pt-10 text-sm opacity-50 md:block">
        Cada ciclo começa no dia em que o salário entra.
      </p>
    </aside>
  )
}

const CATEGORIAS_EXEMPLO = [
  { nome: "Moradia", pct: 42 },
  { nome: "Mercado", pct: 23 },
  { nome: "Transporte", pct: 12 },
]

/** Prévia decorativa do dashboard, só no desktop. Valores de exemplo, escondidos de leitores de tela. */
function Previa() {
  return (
    <div aria-hidden className="relative mt-12 hidden max-w-md md:block">
      <div className="rounded-3xl border border-primary-foreground/15 bg-primary-foreground/5 p-6 backdrop-blur-sm">
        <p className="text-sm opacity-60">Saldo do ciclo</p>
        <p className="valor mt-1 text-4xl font-semibold tracking-tight">
          {formatarCentavos(234_000)}
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl bg-primary-foreground/10 p-3">
            <p className="opacity-60">Entradas</p>
            <p className="valor font-semibold">{formatarCentavos(520_000)}</p>
          </div>
          <div className="rounded-2xl bg-primary-foreground/10 p-3">
            <p className="opacity-60">Saídas</p>
            <p className="valor font-semibold text-saida">{formatarCentavos(286_000)}</p>
          </div>
        </div>

        <ul className="mt-5 grid gap-3 text-sm">
          {CATEGORIAS_EXEMPLO.map((c, i) => (
            <li key={c.nome}>
              <div className="flex justify-between">
                <span className="opacity-80">{c.nome}</span>
                <span className="valor opacity-60">{c.pct}%</span>
              </div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-primary-foreground/10">
                <div
                  className="h-full rounded-full bg-primary-foreground"
                  style={{ width: `${c.pct * 2}%`, opacity: 1 - i * 0.25 }}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Cartão flutuante de cartela, meio inclinado por cima da prévia. */}
      <div className="absolute -right-6 -bottom-8 w-44 rotate-3 rounded-2xl bg-background p-4 text-foreground shadow-2xl lg:-right-12">
        <p className="text-xs text-muted-foreground">Cartela · Viagem</p>
        <p className="valor mt-1 font-semibold">60%</p>
        <div className="mt-2 grid grid-cols-5 gap-1">
          {Array.from({ length: 10 }, (_, i) => (
            <span
              key={i}
              className={i < 6 ? "h-3 rounded-sm bg-foreground" : "h-3 rounded-sm border"}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
