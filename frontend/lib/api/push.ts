import { requisitar } from "./client"

/** Chave pública VAPID. 503 `push_indisponivel` quando o servidor não tem as chaves. */
export async function obterChavePush() {
  return (await requisitar<{ chave_publica: string }>("/push/chave")).chave_publica
}

/** Ativa este aparelho; chamar de novo só atualiza as chaves (e o passa para esta conta). */
export function inscreverAparelho(inscricao: PushSubscriptionJSON) {
  return requisitar<void>("/push/inscricao", { metodo: "PUT", corpo: inscricao })
}

/** 404 se o aparelho não está ativo nesta conta. */
export function removerAparelho(endpoint: string) {
  return requisitar<void>("/push/inscricao", { metodo: "DELETE", corpo: { endpoint } })
}
