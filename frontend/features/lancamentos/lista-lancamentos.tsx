"use client"

import { useState } from "react"
import { cn } from "cn"

import type { Categoria, Lancamento } from "@/lib/api/types"
import { formatarCentavos, formatarDiaMes } from "@/lib/format"
import { ConfirmarPrevisto } from "./confirmar-previsto"
import { DialogLancamento } from "./dialog-lancamento"
import { ExcluirLancamento } from "./excluir-lancamento"
import { rotuloLancamento } from "./rotulo"

type Props = {
  lancamentos: Lancamento[]
  categorias: Categoria[]
  sugestaoSalario: number | null
  /** Texto quando não há lançamentos. */
  vazio?: string
  /** Texto do botão que confirma um previsto (ex.: "Marcar paga" nas dívidas). Sem ele, "Paguei"/"Recebi". */
  rotuloConfirmar?: string
}

/** Lançamentos na ordem recebida. Clicar num item abre a edição; previstos têm confirmação rápida. */
export function ListaLancamentos({
  lancamentos,
  categorias,
  sugestaoSalario,
  vazio = "Nenhum lançamento neste ciclo.",
  rotuloConfirmar,
}: Props) {
  const [aberto, setAberto] = useState(false)
  // Continua preenchido enquanto o dialog fecha, para o conteúdo não trocar na animação.
  const [editando, setEditando] = useState<Lancamento | null>(null)
  const nomes = new Map(categorias.map((c) => [c.id, c.nome]))

  if (lancamentos.length === 0) {
    return <p className="border-t py-8 text-muted-foreground">{vazio}</p>
  }

  return (
    <>
      <ul className="border-t">
        {lancamentos.map((l) => {
          const categoria = nomes.get(l.categoria_id) ?? "Sem categoria"
          const previsto = l.status === "previsto"
          const detalhes = [
            l.descricao,
            l.abre_ciclo && "abre o ciclo",
            l.recorrencia_id != null && "fixo",
            l.parcela_num != null && `parcela ${l.parcela_num}`,
            previsto && "previsto",
          ].filter(Boolean)
          return (
            <li key={l.id} className="flex items-center gap-2 border-b">
              <button
                type="button"
                onClick={() => {
                  setEditando(l)
                  setAberto(true)
                }}
                className="grid min-w-0 flex-1 grid-cols-[3.5rem_1fr_auto] items-baseline gap-x-3 px-1 py-4 text-left transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-2 focus-visible:outline-ring"
              >
                <span className="valor text-sm text-muted-foreground">{formatarDiaMes(l.data)}</span>
                <span className="min-w-0">
                  <span className="block truncate">{categoria}</span>
                  {detalhes.length > 0 && (
                    <span className="block truncate text-sm text-muted-foreground">
                      {detalhes.join(" · ")}
                    </span>
                  )}
                </span>
                <span
                  className={cn(
                    "valor text-right",
                    l.tipo === "saida" ? "text-saida" : "text-entrada",
                    previsto && "opacity-60"
                  )}
                >
                  {l.tipo === "saida" ? "−" : "+"}
                  {formatarCentavos(l.valor)}
                </span>
              </button>
              {previsto && (
                <ConfirmarPrevisto
                  lancamento={l}
                  rotulo={rotuloConfirmar ?? (l.tipo === "saida" ? "Paguei" : "Recebi")}
                />
              )}
            </li>
          )
        })}
      </ul>

      <DialogLancamento
        aberto={aberto}
        aoMudar={setAberto}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        lancamento={editando ?? undefined}
        rodape={
          editando &&
          (editando.divida_id != null ? (
            <p className="text-sm text-muted-foreground">
              Parcelas são geradas pela dívida e não podem ser excluídas uma a uma.
            </p>
          ) : (
            <ExcluirLancamento
              lancamento={editando}
              rotulo={rotuloLancamento(editando, categorias)}
              aoExcluir={() => setAberto(false)}
            />
          ))
        }
      />
    </>
  )
}
