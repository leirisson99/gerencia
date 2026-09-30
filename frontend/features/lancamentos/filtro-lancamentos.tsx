"use client"

import { useState } from "react"
import { cn } from "cn"

import type { Categoria, Lancamento } from "@/lib/api/types"
import { ListaLancamentos } from "./lista-lancamentos"

const FILTROS = [
  { id: "todos", titulo: "Todos", aceita: () => true },
  { id: "saidas", titulo: "Saídas", aceita: (l: Lancamento) => l.tipo === "saida" },
  { id: "entradas", titulo: "Entradas", aceita: (l: Lancamento) => l.tipo === "entrada" },
  { id: "previstos", titulo: "Previstos", aceita: (l: Lancamento) => l.status === "previsto" },
] as const

type Props = {
  lancamentos: Lancamento[]
  categorias: Categoria[]
  sugestaoSalario: number | null
}

/** Lista de lançamentos com filtros em pílulas (tipo e previstos), aplicados no navegador. */
export function FiltroLancamentos({ lancamentos, categorias, sugestaoSalario }: Props) {
  const [filtro, setFiltro] = useState<(typeof FILTROS)[number]["id"]>("todos")
  const atual = FILTROS.find((f) => f.id === filtro) ?? FILTROS[0]
  const visiveis = lancamentos.filter(atual.aceita)

  return (
    <>
      <div
        role="group"
        aria-label="Filtrar lançamentos"
        className="-mx-4 mb-4 flex gap-2 overflow-x-auto px-4 [scrollbar-width:none] md:mx-0 md:px-0"
      >
        {FILTROS.map((f) => {
          const ativo = f.id === filtro
          const quantos = lancamentos.filter(f.aceita).length
          return (
            <button
              key={f.id}
              type="button"
              aria-pressed={ativo}
              onClick={() => setFiltro(f.id)}
              className={cn(
                "flex h-9 shrink-0 items-center gap-1.5 rounded-full border px-4 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                ativo
                  ? "border-primary bg-primary text-primary-foreground"
                  : "bg-background text-muted-foreground hover:text-foreground"
              )}
            >
              {f.titulo}
              <span className={cn("valor text-xs", ativo ? "opacity-70" : "opacity-60")}>
                {quantos}
              </span>
            </button>
          )
        })}
      </div>
      <ListaLancamentos
        lancamentos={visiveis}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        vazio={filtro === "todos" ? undefined : "Nenhum lançamento neste filtro."}
      />
    </>
  )
}
