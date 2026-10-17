"use client"

import { useState } from "react"
import { PencilIcon, UserPlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { ContaDono, ParticipanteDono } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { DialogConvite } from "./dialog-convite"
import { DialogValor } from "./dialog-valor"
import { RemoverParticipante } from "./remover-participante"
import { STATUS_COTA, STATUS_PARTICIPANTE, textoDeBps } from "./rotulos"

const ATIVOS = new Set(["pendente", "aceito"])

function rotuloStatus(p: ParticipanteDono): string {
  if (p.expirado) return "Convite expirado"
  if (p.status === "aceito" && p.status_cota) return STATUS_COTA[p.status_cota]
  return STATUS_PARTICIPANTE[p.status]
}

function rotuloParte(conta: ContaDono, p: ParticipanteDono): string | null {
  if (p.cota !== null) return formatarCentavos(p.cota)
  if (p.valor === null) return null
  if (conta.modo === "percentual") return `${textoDeBps(p.valor)}%`
  if (conta.modo === "fixo") return formatarCentavos(p.valor)
  return null
}

/** Quem divide a conta, com a parte e o status de cada um; o dono convida, ajusta e remove. */
export function ListaParticipantes({ conta }: { conta: ContaDono }) {
  const [convidando, setConvidando] = useState(false)
  const [editando, setEditando] = useState<ParticipanteDono | null>(null)
  const visiveis = conta.participantes.filter((p) => ATIVOS.has(p.status))

  return (
    <section aria-labelledby="participantes-titulo" className="mt-12">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 id="participantes-titulo" className="text-sm font-medium text-muted-foreground">
          Quem divide
        </h2>
        <Button variant="outline" size="sm" onClick={() => setConvidando(true)}>
          <UserPlusIcon aria-hidden />
          Convidar
        </Button>
      </div>

      <ul className="divide-y rounded-lg border">
        {visiveis.map((p) => {
          const parte = rotuloParte(conta, p)
          return (
            <li key={p.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="truncate font-medium">
                  {p.nome ?? p.email_convite ?? "—"}
                  {p.eh_dono && <span className="font-normal text-muted-foreground"> · você</span>}
                </p>
                <p className="text-sm text-muted-foreground">{rotuloStatus(p)}</p>
              </div>
              <div className="flex items-center gap-2">
                {parte && <span className="valor text-sm">{parte}</span>}
                {conta.modo !== "igual" && (
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`Ajustar a parte de ${p.nome ?? p.email_convite}`}
                    onClick={() => setEditando(p)}
                  >
                    <PencilIcon aria-hidden />
                  </Button>
                )}
                {!p.eh_dono && <RemoverParticipante contaId={conta.id} participante={p} />}
              </div>
            </li>
          )
        })}
      </ul>

      <DialogConvite aberto={convidando} aoMudar={setConvidando} contaId={conta.id} modo={conta.modo} />
      {editando && conta.modo !== "igual" && (
        <DialogValor
          aberto
          aoMudar={(aberto) => !aberto && setEditando(null)}
          contaId={conta.id}
          modo={conta.modo}
          participante={editando}
        />
      )}
    </section>
  )
}
