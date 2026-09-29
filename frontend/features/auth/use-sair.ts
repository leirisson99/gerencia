"use client"

import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { sair } from "@/lib/api/auth"

/** Encerra a sessão e volta para a tela de entrada. */
export function useSair() {
  const router = useRouter()
  return async function aoSair() {
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
