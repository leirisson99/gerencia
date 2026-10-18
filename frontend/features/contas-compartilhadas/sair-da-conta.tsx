"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2Icon, LogOutIcon } from "lucide-react"
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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { sairDaConta } from "@/lib/api/contas-compartilhadas"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/** O participante deixa a conta, depois de confirmar. */
export function SairDaConta({ contaId, descricao }: { contaId: number; descricao: string }) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  const [saindo, setSaindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function confirmar() {
    setErro(null)
    setSaindo(true)
    try {
      await sairDaConta(contaId)
      setAberto(false)
      toast.success("Você saiu da conta.")
      router.push("/contas-compartilhadas")
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setSaindo(false)
    }
  }

  return (
    <AlertDialog
      open={aberto}
      onOpenChange={(abrir) => {
        setAberto(abrir)
        if (!abrir) setErro(null)
      }}
    >
      <AlertDialogTrigger asChild>
        <Button variant="ghost" className="text-destructive hover:text-destructive">
          <LogOutIcon aria-hidden />
          Sair da conta
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sair de {descricao}?</AlertDialogTitle>
          <AlertDialogDescription>
            Você deixa de ver a conta e sai da divisão a partir da próxima cobrança. O que já foi
            cobrado continua nos seus lançamentos.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ErroForm mensagem={erro} />
        <AlertDialogFooter>
          <AlertDialogCancel disabled={saindo}>Cancelar</AlertDialogCancel>
          <Button variant="destructive" onClick={confirmar} disabled={saindo} aria-busy={saindo}>
            {saindo && <Loader2Icon className="animate-spin" aria-hidden />}
            Sair
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
