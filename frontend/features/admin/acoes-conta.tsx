"use client"

import { useState } from "react"
import { EllipsisIcon, KeyRoundIcon, UserCheckIcon, UserXIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { UsuarioAdmin } from "@/lib/api/types"
import { DialogSituacao } from "./alternar-situacao"
import { DialogResetarSenha } from "./resetar-senha"

/** Menu `⋯` de uma conta: resetar senha e desativar ou reativar, cada um com sua confirmação. */
export function AcoesConta({ usuario }: { usuario: UsuarioAdmin }) {
  const [dialogo, setDialogo] = useState<"senha" | "situacao" | null>(null)
  const fechar = (aberto: boolean) => !aberto && setDialogo(null)

  return (
    <>
      {/* Não modal: o menu fecha sem prender o foco, e o diálogo que ele abre assume. */}
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label={`Ações da conta de ${usuario.nome}`}>
            <EllipsisIcon aria-hidden />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onSelect={() => setDialogo("senha")}>
            <KeyRoundIcon aria-hidden />
            Resetar senha
          </DropdownMenuItem>
          {usuario.ativo ? (
            <DropdownMenuItem variant="destructive" onSelect={() => setDialogo("situacao")}>
              <UserXIcon aria-hidden />
              Desativar conta
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onSelect={() => setDialogo("situacao")}>
              <UserCheckIcon aria-hidden />
              Reativar conta
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <DialogResetarSenha usuario={usuario} aberto={dialogo === "senha"} aoMudarAberto={fechar} />
      <DialogSituacao usuario={usuario} aberto={dialogo === "situacao"} aoMudarAberto={fechar} />
    </>
  )
}
