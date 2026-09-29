"use client"

import type { ComponentProps } from "react"
import { Loader2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"

type Props = ComponentProps<typeof Button> & { enviando: boolean }

/** Botão de envio que fica desabilitado e mostra progresso enquanto o pedido está em andamento. */
export function BotaoEnviar({ enviando, children, disabled, ...props }: Props) {
  return (
    <Button type="submit" disabled={enviando || disabled} aria-busy={enviando} {...props}>
      {enviando && <Loader2Icon className="animate-spin" aria-hidden />}
      {children}
    </Button>
  )
}
