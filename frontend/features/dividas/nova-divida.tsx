"use client"

import { useState } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { Categoria } from "@/lib/api/types"
import { DialogDivida } from "./dialog-divida"

/** Botão que abre o formulário de dívida nova. */
export function NovaDivida({ categorias }: { categorias: Categoria[] }) {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      <Button onClick={() => setAberto(true)}>
        <PlusIcon aria-hidden />
        Nova dívida
      </Button>
      <DialogDivida aberto={aberto} aoMudar={setAberto} categorias={categorias} />
    </>
  )
}
