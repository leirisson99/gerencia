import { requisitar } from "./client"
import type { SenhaTemporaria } from "./types"

/** Gera uma senha temporária, encerra as sessões da pessoa e obriga a troca no próximo login. */
export function resetarSenha(usuarioId: number) {
  return requisitar<SenhaTemporaria>(`/admin/usuarios/${usuarioId}/reset-senha`, { metodo: "POST" })
}
