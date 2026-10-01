"use client"

import { createContext, useContext, type ReactNode } from "react"

import type { TipoRenda } from "@/lib/api/types"

const Contexto = createContext<TipoRenda>("clt")

/** Leva o tipo de renda da sessão aos componentes cliente da área logada. */
export function TipoRendaProvider({ tipo, children }: { tipo: TipoRenda; children: ReactNode }) {
  return <Contexto value={tipo}>{children}</Contexto>
}

export function useTipoRenda(): TipoRenda {
  return useContext(Contexto)
}
