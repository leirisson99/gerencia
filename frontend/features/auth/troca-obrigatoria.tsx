"use client"

import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { FormTrocarSenha } from "./form-trocar-senha"

export function TrocaObrigatoria() {
  const router = useRouter()
  return (
    <FormTrocarSenha
      textoBotao="Trocar senha e continuar"
      aoTrocar={() => {
        toast.success("Senha trocada.")
        router.replace("/")
        router.refresh()
      }}
    />
  )
}
