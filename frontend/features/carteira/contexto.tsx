"use client"

import { createContext, useContext, type ReactNode } from "react"

import type { Carteira } from "@/lib/api/types"

type Valor = { carteira: Carteira; temPj: boolean }

const Contexto = createContext<Valor>({ carteira: "pf", temPj: false })

/** Leva a carteira aberta (PF ou PJ) aos componentes cliente da área logada. */
export function CarteiraProvider({ valor, children }: { valor: Valor; children: ReactNode }) {
  return <Contexto value={valor}>{children}</Contexto>
}

export function useCarteira(): Valor {
  return useContext(Contexto)
}
