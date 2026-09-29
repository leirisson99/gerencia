"use client"

import { toast } from "sonner"

import { FormTrocarSenha } from "@/features/auth/form-trocar-senha"

export function SecaoSenha() {
  return (
    <FormTrocarSenha
      aoTrocar={() => toast.success("Senha trocada. Outras sessões foram encerradas.")}
    />
  )
}
