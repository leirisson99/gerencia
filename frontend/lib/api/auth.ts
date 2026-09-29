import { requisitar } from "./client"
import type { CadastroIn, LoginIn, PerfilIn, TrocaSenhaIn, Usuario } from "./types"

export function cadastrar(dados: CadastroIn) {
  return requisitar<Usuario>("/auth/cadastro", { metodo: "POST", corpo: dados })
}

export function entrar(dados: LoginIn) {
  return requisitar<Usuario>("/auth/login", { metodo: "POST", corpo: dados })
}

export function sair() {
  return requisitar<void>("/auth/logout", { metodo: "POST" })
}

export function obterMe() {
  return requisitar<Usuario>("/me")
}

export function editarMe(dados: PerfilIn) {
  return requisitar<Usuario>("/me", { metodo: "PATCH", corpo: dados })
}

export function trocarSenha(dados: TrocaSenhaIn) {
  return requisitar<void>("/me/senha", { metodo: "PUT", corpo: dados })
}
