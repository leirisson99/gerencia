import { requisitar } from "./client"
import type { Banco, LinhaImportacao, Previa, PreviaIn, ResultadoImportacao } from "./types"

export function listarBancos() {
  return requisitar<Banco[]>("/importacoes/bancos")
}

/** Lê o extrato e classifica as linhas. Nada é gravado. */
export function lerExtrato(dados: PreviaIn) {
  return requisitar<Previa>("/importacoes/previa", { metodo: "POST", corpo: dados })
}

/** Grava as linhas confirmadas: todas ou nenhuma. */
export function importarLinhas(linhas: LinhaImportacao[]) {
  return requisitar<ResultadoImportacao>("/importacoes", { metodo: "POST", corpo: { linhas } })
}
