"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"
import { cn } from "cn"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { editarRecorrencia } from "@/lib/api/recorrencias"
import type { Categoria, Recorrencia } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { DialogRecorrencia } from "./dialog-recorrencia"

type Props = {
  recorrencias: Recorrencia[]
  /** Todas, inclusive inativas, para mostrar o nome de qualquer recorrência. */
  categorias: Categoria[]
}

/** Recorrências por dia do mês; clicar abre a edição. As inativas ficam por último. */
export function ListaRecorrencias({ recorrencias, categorias }: Props) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  // Continua preenchido enquanto o dialog fecha, para o conteúdo não trocar na animação.
  const [editando, setEditando] = useState<Recorrencia | undefined>()
  const nomes = new Map(categorias.map((c) => [c.id, c.nome]))
  const ativasParaForm = categorias.filter((c) => c.ativa)
  const ativas = recorrencias.filter((r) => r.ativa)
  const inativas = recorrencias.filter((r) => !r.ativa)

  function abrir(recorrencia?: Recorrencia) {
    setEditando(recorrencia)
    setAberto(true)
  }

  async function mudarAtiva(recorrencia: Recorrencia, ativa: boolean) {
    try {
      await editarRecorrencia(recorrencia.id, { ativa })
      toast.success(
        ativa
          ? `"${recorrencia.descricao}" reativada. Volta a gerar previstos.`
          : `"${recorrencia.descricao}" desativada. Não gera mais previstos.`
      )
      router.refresh()
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    }
  }

  function linhas(lista: Recorrencia[]) {
    return (
      <ul className="border-t">
        {lista.map((r) => (
          <li key={r.id} className="flex items-center gap-2 border-b">
            <button
              type="button"
              onClick={() => abrir(r)}
              className={cn(
                "grid min-w-0 flex-1 grid-cols-[4.5rem_1fr_auto] items-baseline gap-x-3 px-1 py-4 text-left transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-2 focus-visible:outline-ring",
                !r.ativa && "text-muted-foreground"
              )}
            >
              <span className="valor text-sm text-muted-foreground">todo dia {r.dia}</span>
              <span className="min-w-0">
                <span className="block truncate">{r.descricao}</span>
                <span className="block truncate text-sm text-muted-foreground">
                  {nomes.get(r.categoria_id) ?? "Sem categoria"}
                </span>
              </span>
              <span className={cn("valor text-right", r.ativa && r.tipo === "saida" && "text-saida")}>
                {r.tipo === "saida" ? "−" : "+"}
                {formatarCentavos(r.valor)}
              </span>
            </button>
            <Button
              variant={r.ativa ? "ghost" : "outline"}
              size="sm"
              onClick={() => mudarAtiva(r, !r.ativa)}
              aria-label={`${r.ativa ? "Desativar" : "Reativar"} ${r.descricao}`}
            >
              {r.ativa ? "Desativar" : "Reativar"}
            </Button>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <>
      <div className="mb-4 flex justify-end">
        <Button onClick={() => abrir()}>
          <PlusIcon aria-hidden />
          Nova recorrência
        </Button>
      </div>

      {ativas.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          Nenhuma recorrência ativa. Cadastre aluguel, internet e outras contas fixas para cada ciclo já
          começar com elas previstas.
        </p>
      ) : (
        linhas(ativas)
      )}

      {inativas.length > 0 && (
        <details className="mt-8">
          <summary className="cursor-pointer text-sm text-muted-foreground select-none">
            {inativas.length} {inativas.length === 1 ? "inativa" : "inativas"}
          </summary>
          <div className="mt-2">{linhas(inativas)}</div>
        </details>
      )}

      <DialogRecorrencia
        aberto={aberto}
        aoMudar={setAberto}
        categorias={ativasParaForm}
        recorrencia={editando}
      />
    </>
  )
}
