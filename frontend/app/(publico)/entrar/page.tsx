import type { Metadata } from "next"
import Link from "next/link"

import { AuthShell } from "@/components/layout/auth-shell"
import { FormEntrar } from "@/features/auth/form-entrar"

export const metadata: Metadata = { title: "Entrar" }

export default function EntrarPage() {
  return (
    <AuthShell
      titulo="Entrar"
      subtitulo="Veja quanto entrou, para onde foi e quanto sobrou."
      rodape={
        <>
          Ainda não tem conta?{" "}
          <Link href="/criar-conta" className="font-medium text-foreground underline underline-offset-4">
            Criar conta
          </Link>
        </>
      }
    >
      <FormEntrar />
    </AuthShell>
  )
}
