import type { Metadata } from "next"
import Link from "next/link"

import { AuthShell } from "@/components/layout/auth-shell"
import { FormCadastro } from "@/features/auth/form-cadastro"

export const metadata: Metadata = { title: "Criar conta" }

export default function CriarContaPage() {
  return (
    <AuthShell
      titulo="Criar conta"
      subtitulo="Seus dados ficam só com você."
      rodape={
        <>
          Já tem conta?{" "}
          <Link href="/entrar" className="font-medium text-foreground underline underline-offset-4">
            Entrar
          </Link>
        </>
      }
    >
      <FormCadastro />
    </AuthShell>
  )
}
