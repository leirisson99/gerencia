"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"
import { listarEventosConta } from "@/lib/api/admin"
import { ApiError } from "@/lib/api/client"
import type { EventoUso, PaginaEventos } from "@/lib/api/types"
import { formatarDataDeInstante, formatarHoraDeInstante } from "@/lib/format"
import { INICIO_EVENTOS, ROTULOS_EVENTO } from "./rotulos-atividade"

/** Eventos agrupados pelo dia em São Paulo, mantendo a ordem do mais recente ao mais antigo. */
function porDia(eventos: EventoUso[]) {
  const dias: { dia: string; eventos: EventoUso[] }[] = []
  for (const evento of eventos) {
    const dia = formatarDataDeInstante(evento.ocorrido_em)
    if (dias.at(-1)?.dia !== dia) dias.push({ dia, eventos: [] })
    dias.at(-1)!.eventos.push(evento)
  }
  return dias
}

/** Linha do tempo de uso da conta: só o tipo da ação e a hora, nunca o conteúdo. */
export function LinhaTempo({ usuarioId, inicial }: { usuarioId: number; inicial: PaginaEventos }) {
  const [eventos, setEventos] = useState(inicial.itens)
  const [proximo, setProximo] = useState(inicial.proximo)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function carregarMais() {
    if (proximo === null) return
    setCarregando(true)
    setErro(null)
    try {
      const pagina = await listarEventosConta(usuarioId, proximo)
      setEventos((atuais) => [...atuais, ...pagina.itens])
      setProximo(pagina.proximo)
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível carregar mais.")
    } finally {
      setCarregando(false)
    }
  }

  if (eventos.length === 0) {
    return (
      <p className="text-muted-foreground">Sem atividade registrada desde {INICIO_EVENTOS}.</p>
    )
  }

  return (
    <div>
      <ol className="flex flex-col gap-5">
        {porDia(eventos).map(({ dia, eventos: doDia }) => (
          <li key={dia}>
            <h3 className="valor mb-2 text-sm font-medium text-muted-foreground">{dia}</h3>
            <ul className="flex flex-col border-l pl-4">
              {doDia.map((evento, i) => (
                <li key={`${evento.ocorrido_em}-${i}`} className="flex items-baseline gap-3 py-1.5">
                  <span className="valor w-12 shrink-0 text-sm text-muted-foreground">
                    {formatarHoraDeInstante(evento.ocorrido_em)}
                  </span>
                  <span>{ROTULOS_EVENTO[evento.tipo]}</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>

      {proximo !== null && (
        <div className="mt-6 flex flex-col items-start gap-2">
          <Button variant="outline" onClick={carregarMais} disabled={carregando}>
            {carregando ? "Carregando…" : "Carregar mais"}
          </Button>
          {erro && (
            <p role="alert" className="text-sm text-saida">
              {erro}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
