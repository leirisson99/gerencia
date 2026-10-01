import { requisitar } from "./client"
import type { SenhaTemporaria, UsuarioAdmin } from "./types"

/** Gera uma senha temporária, encerra as sessões da pessoa e obriga a troca no próximo login. */
export function resetarSenha(usuarioId: number) {
  return requisitar<SenhaTemporaria>(`/admin/usuarios/${usuarioId}/reset-senha`, { metodo: "POST" })
}

/** Encerra as sessões e recusa o login; os dados ficam guardados. */
export function desativarConta(usuarioId: number) {
  return requisitar<UsuarioAdmin>(`/admin/usuarios/${usuarioId}/desativar`, { metodo: "POST" })
}

export function reativarConta(usuarioId: number) {
  return requisitar<UsuarioAdmin>(`/admin/usuarios/${usuarioId}/reativar`, { metodo: "POST" })
}
