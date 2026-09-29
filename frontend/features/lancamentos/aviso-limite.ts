import { toast } from "sonner"

import type { AvisoLimite } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"

const TEXTO = { ok: "dentro do limite", atencao: "em atenção", estourado: "estourou o limite" } as const

/** Aviso da API quando a categoria piora de situação. Nunca bloqueia: o lançamento já foi salvo. */
export function mostrarAvisoLimite(aviso: AvisoLimite | null) {
  if (!aviso) return
  toast.warning(`${aviso.nome} ${TEXTO[aviso.situacao]}`, {
    description: `${formatarCentavos(aviso.usado)} de ${formatarCentavos(aviso.limite)} neste ciclo.`,
  })
}
