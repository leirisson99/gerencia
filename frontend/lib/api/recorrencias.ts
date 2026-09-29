import { requisitar } from "./client"
import type { Recorrencia, RecorrenciaIn, RecorrenciaPatch } from "./types"

/** Com um ciclo aberto, a API já gera o previsto dele. */
export function criarRecorrencia(dados: RecorrenciaIn) {
  return requisitar<Recorrencia>("/recorrencias", { metodo: "POST", corpo: dados })
}

/** Vale para os próximos ciclos; previstos já gerados não mudam. */
export function editarRecorrencia(id: number, dados: RecorrenciaPatch) {
  return requisitar<Recorrencia>(`/recorrencias/${id}`, { metodo: "PATCH", corpo: dados })
}
