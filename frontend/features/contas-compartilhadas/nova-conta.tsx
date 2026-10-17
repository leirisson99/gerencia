"use client"

import { useState } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { Categoria } from "@/lib/api/types"
import { DialogConta } from "./dialog-conta"

/** Botão que abre o formulário de conta compartilhada nova. */
export function NovaConta({ categorias }: { categorias: Categoria[] }) {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      <Button onClick={() => setAberto(true)}>
        <PlusIcon aria-hidden />
        Nova conta
      </Button>
      <DialogConta aberto={aberto} aoMudar={setAberto} categorias={categorias} />
    </>
  )
}
