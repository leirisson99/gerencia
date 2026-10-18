"use client"

import { useState } from "react"
import { ReceiptTextIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { ContaDono } from "@/lib/api/types"
import { DialogCobranca } from "./dialog-cobranca"

/** Botão do dono que abre o fechamento do mês; desativado enquanto a conta está desativada. */
export function GerarCobranca({ conta }: { conta: ContaDono }) {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      <Button size="sm" variant="outline" disabled={!conta.ativa} onClick={() => setAberto(true)}>
        <ReceiptTextIcon aria-hidden />
        Gerar cobrança
      </Button>
      <DialogCobranca aberto={aberto} aoMudar={setAberto} conta={conta} />
    </>
  )
}
