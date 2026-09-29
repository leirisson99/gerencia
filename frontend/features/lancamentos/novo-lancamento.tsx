"use client"

import { useState, type ComponentProps } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { Categoria } from "@/lib/api/types"
import { DialogLancamento } from "./dialog-lancamento"

type Props = Omit<ComponentProps<typeof Button>, "onClick"> & {
  categorias: Categoria[]
  sugestaoSalario: number | null
  categoriaInicial?: Categoria
}

/** Botão que abre o dialog de lançamento novo. */
export function NovoLancamento({
  categorias,
  sugestaoSalario,
  categoriaInicial,
  children = "Lançar",
  ...props
}: Props) {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      <Button onClick={() => setAberto(true)} {...props}>
        <PlusIcon aria-hidden />
        {children}
      </Button>
      <DialogLancamento
        aberto={aberto}
        aoMudar={setAberto}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        categoriaInicial={categoriaInicial}
      />
    </>
  )
}
