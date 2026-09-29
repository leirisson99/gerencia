"use client"

import { useState } from "react"
import { CheckIcon, CopyIcon, KeyRoundIcon, Loader2Icon } from "lucide-react"

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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { resetarSenha } from "@/lib/api/admin"
import { ApiError } from "@/lib/api/client"
import type { UsuarioAdmin } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/**
 * Confirma o reset e mostra a senha temporária uma única vez.
 * A senha só existe no estado deste componente e é apagada ao fechar.
 */
export function ResetarSenha({ usuario }: { usuario: Pick<UsuarioAdmin, "id" | "nome" | "email"> }) {
  const [confirmando, setConfirmando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [senha, setSenha] = useState<string | null>(null)
  const [copiada, setCopiada] = useState(false)

  async function confirmar() {
    setErro(null)
    setEnviando(true)
    try {
      const { senha_temporaria } = await resetarSenha(usuario.id)
      setConfirmando(false)
      setSenha(senha_temporaria)
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  async function copiar() {
    if (!senha) return
    try {
      await navigator.clipboard.writeText(senha)
      setCopiada(true)
    } catch {
      // Sem permissão de área de transferência: a senha continua visível para copiar à mão.
    }
  }

  function fecharSenha() {
    setSenha(null)
    setCopiada(false)
  }

  return (
    <>
      <AlertDialog
        open={confirmando}
        onOpenChange={(abrir) => {
          setConfirmando(abrir)
          if (!abrir) setErro(null)
        }}
      >
        <AlertDialogTrigger asChild>
          <Button variant="outline" size="sm" aria-label={`Resetar senha de ${usuario.nome}`}>
            <KeyRoundIcon aria-hidden />
            Resetar senha
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Resetar a senha de {usuario.nome}?</AlertDialogTitle>
            <AlertDialogDescription>
              {usuario.email} sai de todas as sessões e, no próximo login, entra com uma senha
              temporária e escolhe uma nova. A ação fica registrada.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <ErroForm mensagem={erro} />
          <AlertDialogFooter>
            <AlertDialogCancel disabled={enviando}>Cancelar</AlertDialogCancel>
            {/* Botão comum: a ação da Radix fecharia o dialog antes da resposta da API. */}
            <Button variant="destructive" onClick={confirmar} disabled={enviando} aria-busy={enviando}>
              {enviando && <Loader2Icon className="animate-spin" aria-hidden />}
              Resetar senha
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={senha !== null} onOpenChange={(abrir) => !abrir && fecharSenha()}>
        <DialogContent className="p-6 sm:max-w-md" onInteractOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="text-xl">Senha temporária de {usuario.nome}</DialogTitle>
            <DialogDescription>
              Passe esta senha para a pessoa por um canal seguro. Ela{" "}
              <strong className="font-medium text-foreground">não será mostrada de novo</strong>.
            </DialogDescription>
          </DialogHeader>
          <p className="valor my-2 rounded-lg border bg-muted px-4 py-3 text-center font-mono text-xl tracking-wider select-all">
            {senha}
          </p>
          <DialogFooter className="-mx-6 -mb-6">
            <Button variant="outline" onClick={copiar}>
              {copiada ? <CheckIcon aria-hidden /> : <CopyIcon aria-hidden />}
              {copiada ? "Copiada" : "Copiar"}
            </Button>
            <Button onClick={fecharSenha}>Já anotei</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
