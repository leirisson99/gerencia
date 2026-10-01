"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2Icon } from "lucide-react"
import { toast } from "sonner"

import { ErroForm } from "@/components/forms/erro-form"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { desativarConta, reativarConta } from "@/lib/api/admin"
import { ApiError } from "@/lib/api/client"
import type { UsuarioAdmin } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/** Confirma desativar ou reativar a conta e recarrega a lista. Quem abre é o menu de ações. */
export function DialogSituacao({
  usuario,
  aberto,
  aoMudarAberto,
}: {
  usuario: UsuarioAdmin
  aberto: boolean
  aoMudarAberto: (aberto: boolean) => void
}) {
  const router = useRouter()
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const desativar = usuario.ativo

  async function confirmar() {
    setErro(null)
    setEnviando(true)
    try {
      await (desativar ? desativarConta(usuario.id) : reativarConta(usuario.id))
      aoMudarAberto(false)
      toast.success(desativar ? `Conta de ${usuario.nome} desativada.` : `Conta de ${usuario.nome} reativada.`)
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <AlertDialog
      open={aberto}
      onOpenChange={(abrir) => {
        aoMudarAberto(abrir)
        if (!abrir) setErro(null)
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {desativar ? "Desativar" : "Reativar"} a conta de {usuario.nome}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            {desativar
              ? `${usuario.email} sai de todas as sessões e não consegue mais entrar. Nenhum dado é apagado, e você pode reativar a conta depois.`
              : `${usuario.email} volta a entrar com a mesma senha e encontra os mesmos dados.`}{" "}
            A ação fica registrada.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ErroForm mensagem={erro} />
        <AlertDialogFooter>
          <AlertDialogCancel disabled={enviando}>Cancelar</AlertDialogCancel>
          {/* Botão comum: a ação da Radix fecharia o dialog antes da resposta da API. */}
          <Button
            variant={desativar ? "destructive" : "default"}
            onClick={confirmar}
            disabled={enviando}
            aria-busy={enviando}
          >
            {enviando && <Loader2Icon className="animate-spin" aria-hidden />}
            {desativar ? "Desativar conta" : "Reativar conta"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
