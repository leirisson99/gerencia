"use client"

import { useState } from "react"
import { cn } from "cn"
import { ArrowDownIcon, ArrowUpIcon } from "lucide-react"

import { DialogLancamento } from "@/features/lancamentos/dialog-lancamento"
import type { Categoria, TipoLancamento } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"

/** Total de entradas ou de saídas no cartão de saldo do celular; o toque abre o lançamento daquele tipo. */
export function Movimento({
  tipo,
  valor,
  categorias,
  sugestaoSalario,
}: {
  tipo: TipoLancamento
  valor: number
  categorias: Categoria[]
  sugestaoSalario: number | null
}) {
  const [lancando, setLancando] = useState(false)
  const saida = tipo === "saida"
  const Icone = saida ? ArrowUpIcon : ArrowDownIcon
  const titulo = saida ? "Saídas" : "Entradas"

  return (
    <>
      <button
        type="button"
        onClick={() => setLancando(true)}
        aria-label={`${titulo}: ${formatarCentavos(valor)}. Lançar ${saida ? "saída" : "entrada"}`}
        className="relative overflow-hidden rounded-2xl bg-primary-foreground/10 p-3 text-left transition-opacity active:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-foreground"
      >
        <Icone
          aria-hidden
          className="absolute -right-3 -bottom-3 size-16 opacity-10"
          strokeWidth={2.5}
        />
        <span
          aria-hidden
          className="flex size-7 items-center justify-center rounded-full bg-primary-foreground text-primary"
        >
          <Icone className="size-4" />
        </span>
        <span className="mt-3 block text-xs opacity-70">{titulo}</span>
        <span className={cn("valor block font-semibold", saida && "text-saida")}>
          {formatarCentavos(valor)}
        </span>
      </button>

      <DialogLancamento
        aberto={lancando}
        aoMudar={setLancando}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        tipo={tipo}
      />
    </>
  )
}
