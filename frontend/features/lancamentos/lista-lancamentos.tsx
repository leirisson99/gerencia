"use client"

import { useState } from "react"
import Link from "next/link"
import { cn } from "cn"
import { ArrowDownIcon, ArrowUpIcon } from "lucide-react"

import { useTipoRenda } from "@/features/tipo-renda/contexto"
import type { Categoria, Lancamento } from "@/lib/api/types"
import { formatarCentavos, formatarDiaMes } from "@/lib/format"
import { temServicos } from "@/lib/tipo-renda"
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
  /** Esconde a coluna de data quando a lista já é de um único dia. */
  semData?: boolean
}

/** Lançamentos na ordem recebida. Clicar num item abre a edição; previstos têm confirmação rápida. */
export function ListaLancamentos({
  lancamentos,
  categorias,
  sugestaoSalario,
  vazio = "Nenhum lançamento neste ciclo.",
  rotuloConfirmar,
  semData = false,
}: Props) {
  const [aberto, setAberto] = useState(false)
  // Continua preenchido enquanto o dialog fecha, para o conteúdo não trocar na animação.
  const [editando, setEditando] = useState<Lancamento | null>(null)
  const nomes = new Map(categorias.map((c) => [c.id, c.nome]))
  const comServicos = temServicos(useTipoRenda())

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
            l.cartela_id != null && "cartela",
            l.servico_id != null && "serviço",
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
                className={cn(
                  "grid min-w-0 flex-1 grid-cols-[2.5rem_1fr_auto] items-center gap-x-3 px-1 py-3 text-left transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-2 focus-visible:outline-ring active:bg-muted/60 md:items-baseline md:py-4",
                  semData ? "md:grid-cols-[1fr_auto]" : "md:grid-cols-[3.5rem_1fr_auto]"
                )}
              >
                {/* Celular: ícone redondo no lugar da coluna de data, que desce para a linha de detalhes. */}
                <span
                  aria-hidden
                  className={cn(
                    "flex size-10 items-center justify-center rounded-full bg-muted md:hidden",
                    l.tipo === "saida" ? "text-saida" : "text-entrada",
                    previsto && "opacity-60"
                  )}
                >
                  {l.tipo === "saida" ? (
                    <ArrowUpIcon className="size-4" />
                  ) : (
                    <ArrowDownIcon className="size-4" />
                  )}
                </span>
                {!semData && (
                  <span className="valor hidden text-sm text-muted-foreground md:block">
                    {formatarDiaMes(l.data)}
                  </span>
                )}
                <span className="min-w-0">
                  <span className="block truncate max-md:font-medium">{categoria}</span>
                  {(detalhes.length > 0 || !semData) && (
                    <span className="block truncate text-sm text-muted-foreground">
                      {!semData && (
                        <span className="valor md:hidden">
                          {formatarDiaMes(l.data)}
                          {detalhes.length > 0 && " · "}
                        </span>
                      )}
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
          ) : editando.servico_id != null && comServicos ? (
            <p className="text-sm text-muted-foreground">
              Esta entrada é de um serviço. Para receber, desfazer ou excluir,{" "}
              <Link href="/servicos" className="underline underline-offset-4">
                use a tela de serviços
              </Link>
              .
            </p>
          ) : editando.cartela_id != null ? (
            <p className="text-sm text-muted-foreground">
              Para remover este depósito,{" "}
              <Link href={`/cartelas/${editando.cartela_id}`} className="underline underline-offset-4">
                desmarque a casa na cartela
              </Link>
              .
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
