import { requisitar } from "./client"
import type {
  CobrancaIn,
  ContaCompartilhadaIn,
  ContaCompartilhadaPatch,
  ContaDono,
  ContaParticipante,
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

/** O convidado escolhe a categoria em que a sua parte vai cair e passa a ver a conta. */
export function aceitarConvite(conviteId: number, categoriaId: number) {
  return requisitar<ContaParticipante>(`${BASE}/convites/${conviteId}/aceitar`, {
    metodo: "POST",
    corpo: { categoria_id: categoriaId },
  })
}

export function recusarConvite(conviteId: number) {
  return requisitar<void>(`${BASE}/convites/${conviteId}/recusar`, { metodo: "POST" })
}

/** O participante sai. As cobranças já geradas continuam valendo para ele. */
export function sairDaConta(contaId: number) {
  return requisitar<void>(`${BASE}/${contaId}/sair`, { metodo: "POST" })
}

/** O dono fecha o mês: o total é dividido só entre quem aceitou até agora. */
export function gerarCobranca(contaId: number, dados: CobrancaIn) {
  return requisitar<ContaDono>(`${BASE}/${contaId}/cobrancas`, { metodo: "POST", corpo: dados })
}

/** O dono confirma que recebeu. Só marca a cota: não mexe no lançamento de ninguém. */
export function confirmarCota(cotaId: number) {
  return requisitar<ContaDono>(`${BASE}/cotas/${cotaId}/confirmar`, { metodo: "POST" })
}

export function desfazerConfirmacao(cotaId: number) {
  return requisitar<ContaDono>(`${BASE}/cotas/${cotaId}/desfazer-confirmacao`, { metodo: "POST" })
}
