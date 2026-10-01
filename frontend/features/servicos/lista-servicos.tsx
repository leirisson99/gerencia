"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CheckIcon, PlusIcon, Undo2Icon } from "lucide-react"
import { toast } from "sonner"
import { cn } from "cn"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { desfazerRecebimento } from "@/lib/api/servicos"
import type { Categoria, Servico, SituacaoServico } from "@/lib/api/types"
import { formatarCentavos, formatarDiaMes } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { DialogRecebimento } from "./dialog-recebimento"
import { DialogServico } from "./dialog-servico"
import { ExcluirServico } from "./excluir-servico"
import { ROTULO_SITUACAO, detalheSituacao, rotuloServico } from "./situacao"

const FILTROS: { id: "todos" | SituacaoServico; titulo: string }[] = [
  { id: "todos", titulo: "Todos" },
  { id: "a_receber", titulo: "A receber" },
  { id: "atrasado", titulo: "Atrasados" },
  { id: "recebido", titulo: "Recebidos" },
]

type Props = {
  /** Por data prevista, como a API devolve. */
  servicos: Servico[]
  /** Todas, inclusive inativas, para mostrar o nome de qualquer categoria. */
  categorias: Categoria[]
}

/**
 * Serviços com totais pendentes e filtros por situação, aplicados no navegador. Clicar num serviço
 * não recebido abre a edição; recebido, só dá para desfazer o recebimento.
 */
export function ListaServicos({ servicos, categorias }: Props) {
  const router = useRouter()
  const [filtro, setFiltro] = useState<(typeof FILTROS)[number]["id"]>("todos")
  const [editando, setEditando] = useState<Servico | undefined>()
  const [editandoAberto, setEditandoAberto] = useState(false)
  // Continuam preenchidos enquanto o dialog fecha, para o conteúdo não trocar na animação.
  const [recebendo, setRecebendo] = useState<Servico | undefined>()
  const [recebendoAberto, setRecebendoAberto] = useState(false)
  const nomes = new Map(categorias.map((c) => [c.id, c.nome]))
  const ativasParaForm = categorias.filter((c) => c.ativa)

  const visiveis = filtro === "todos" ? servicos : servicos.filter((s) => s.situacao === filtro)
  const pendentes = servicos.filter((s) => s.situacao !== "recebido")
  const atrasados = servicos.filter((s) => s.situacao === "atrasado")
  const soma = (lista: Servico[]) => lista.reduce((total, s) => total + s.valor, 0)
  const linha =
    "grid min-w-0 flex-1 grid-cols-[3.5rem_1fr_auto] items-baseline gap-x-3 px-1 py-4 text-left transition-colors focus-visible:outline-2 focus-visible:outline-ring"

  function editar(servico?: Servico) {
    setEditando(servico)
    setEditandoAberto(true)
  }

  function receber(servico: Servico) {
    setRecebendo(servico)
    setRecebendoAberto(true)
  }

  async function desfazer(servico: Servico) {
    try {
      await desfazerRecebimento(servico.id)
      toast.success("Recebimento desfeito. A entrada voltou a prevista.")
      router.refresh()
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    }
  }

  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <dl className="valor flex flex-wrap gap-x-8 gap-y-2">
          <div>
            <dt className="text-sm text-muted-foreground">A receber</dt>
            <dd className="text-xl font-semibold">{formatarCentavos(soma(pendentes))}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted-foreground">Atrasado</dt>
            <dd className={cn("text-xl font-semibold", atrasados.length > 0 && "text-saida")}>
              {formatarCentavos(soma(atrasados))}
            </dd>
          </div>
        </dl>
        <Button onClick={() => editar()}>
          <PlusIcon aria-hidden />
          Novo serviço
        </Button>
      </div>

      <div
        role="group"
        aria-label="Filtrar serviços"
        className="-mx-4 mb-4 flex gap-2 overflow-x-auto px-4 [scrollbar-width:none] md:mx-0 md:px-0"
      >
        {FILTROS.map((f) => {
          const ativo = f.id === filtro
          const quantos =
            f.id === "todos" ? servicos.length : servicos.filter((s) => s.situacao === f.id).length
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

      {visiveis.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          {servicos.length === 0
            ? "Nenhum serviço. Cadastre o que um cliente vai pagar para ver quanto ainda tem a receber."
            : "Nenhum serviço neste filtro."}
        </p>
      ) : (
        <ul className="border-t">
          {visiveis.map((s) => {
            const recebido = s.situacao === "recebido"
            const data = recebido && s.data_recebimento ? s.data_recebimento : s.data_prevista
            const valor = recebido && s.valor_recebido != null ? s.valor_recebido : s.valor
            const detalhes = [
              s.descricao,
              nomes.get(s.categoria_id) ?? "Sem categoria",
              detalheSituacao(s),
            ].filter(Boolean)
            const conteudo = (
              <>
                <span className="valor text-sm text-muted-foreground">{formatarDiaMes(data)}</span>
                <span className="min-w-0">
                  <span className="block truncate">{s.cliente}</span>
                  <span className="block truncate text-sm text-muted-foreground">
                    {detalhes.join(" · ")}
                  </span>
                </span>
                <span className="text-right">
                  <span className={cn("valor block", recebido ? "text-entrada" : "opacity-60")}>
                    +{formatarCentavos(valor)}
                  </span>
                  <span
                    className={cn(
                      "block text-xs",
                      s.situacao === "atrasado" ? "font-medium text-saida" : "text-muted-foreground"
                    )}
                  >
                    {ROTULO_SITUACAO[s.situacao]}
                  </span>
                </span>
              </>
            )
            return (
              <li key={s.id} className="flex items-center gap-2 border-b">
                {recebido ? (
                  <div className={linha}>{conteudo}</div>
                ) : (
                  <button
                    type="button"
                    onClick={() => editar(s)}
                    className={cn(linha, "hover:bg-muted/60 focus-visible:bg-muted/60")}
                  >
                    {conteudo}
                  </button>
                )}
                {recebido ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => desfazer(s)}
                    aria-label={`Desfazer recebimento de ${rotuloServico(s)}`}
                  >
                    <Undo2Icon aria-hidden />
                    Desfazer
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => receber(s)}
                    aria-label={`Marcar recebimento de ${rotuloServico(s)}`}
                  >
                    <CheckIcon aria-hidden />
                    Recebi
                  </Button>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <DialogServico
        aberto={editandoAberto}
        aoMudar={setEditandoAberto}
        categorias={ativasParaForm}
        servico={editando}
        rodape={
          editando && <ExcluirServico servico={editando} aoExcluir={() => setEditandoAberto(false)} />
        }
      />
      <DialogRecebimento aberto={recebendoAberto} aoMudar={setRecebendoAberto} servico={recebendo} />
    </>
  )
}
