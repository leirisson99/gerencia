import { requisitar } from "./client"
import type {
  ContaCompartilhadaIn,
  ContaCompartilhadaPatch,
  ContaDono,
  ConviteIn,
} from "./types"

const BASE = "/contas-compartilhadas"

/** Cria a conta; o dono entra como primeiro participante. */
export function criarContaCompartilhada(dados: ContaCompartilhadaIn) {
  return requisitar<ContaDono>(BASE, { metodo: "POST", corpo: dados })
}

/** Só o dono. Não muda cobranças já geradas. */
export function editarContaCompartilhada(id: number, dados: ContaCompartilhadaPatch) {
  return requisitar<ContaDono>(`${BASE}/${id}`, { metodo: "PATCH", corpo: dados })
}

/** A resposta é a mesma exista conta para o e-mail ou não. */
export function convidarParticipante(contaId: number, dados: ConviteIn) {
  return requisitar<ContaDono>(`${BASE}/${contaId}/participantes`, {
    metodo: "POST",
    corpo: dados,
  })
}

/** Pontos-base no percentual, centavos no valor fixo. Vale também para o dono. */
export function editarValorDoParticipante(contaId: number, participanteId: number, valor: number | null) {
  return requisitar<ContaDono>(`${BASE}/${contaId}/participantes/${participanteId}`, {
    metodo: "PATCH",
    corpo: { valor },
  })
}

/** Vale da próxima cobrança: as cotas já geradas ficam como estão. */
export function removerParticipante(contaId: number, participanteId: number) {
  return requisitar<ContaDono>(`${BASE}/${contaId}/participantes/${participanteId}`, {
    metodo: "DELETE",
  })
}
