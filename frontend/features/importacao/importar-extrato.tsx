"use client"

import { useState } from "react"

import type { Categoria, Previa } from "@/lib/api/types"
import { FormExtrato } from "./form-extrato"
import { PreviaExtrato } from "./previa-extrato"

/** Envia o extrato, mostra a prévia e confirma as linhas escolhidas. */
export function ImportarExtrato({ categorias }: { categorias: Categoria[] }) {
  const [previa, setPrevia] = useState<Previa | null>(null)

  if (previa === null) return <FormExtrato aoLer={(lida) => setPrevia(lida)} />
  return <PreviaExtrato previa={previa} categorias={categorias} aoVoltar={() => setPrevia(null)} />
}
