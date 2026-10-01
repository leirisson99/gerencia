"use client"

import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { sair } from "@/lib/api/auth"
import { desativarPush } from "@/lib/push"

/** Encerra a sessão e volta para a tela de entrada. */
export function useSair() {
  const router = useRouter()
  return async function aoSair() {
    try {
      // Este aparelho para de receber o resumo desta conta (FR-008).
      await desativarPush()
    } catch {
      // Sem rede ou push desligado: sair continua valendo.
    }
    try {
      await sair()
    } catch {
      // Sessão já inválida: segue para a tela de entrada do mesmo jeito.
    }
    toast("Você saiu da sua conta.")
    router.replace("/entrar")
    router.refresh()
  }
}
