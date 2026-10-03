import "server-only"

import { cookies } from "next/headers"

import { obterUsuarioSessao } from "./api/server"
import type { Carteira } from "./api/types"

/** Cookie com a carteira aberta no seletor PF | PJ. Conveniência por navegador. */
export const COOKIE_CARTEIRA = "carteira"

/** Carteira aberta: a PJ só vale para quem a ligou; sem cookie ou sem PJ, a PF. */
export async function obterCarteira(): Promise<Carteira> {
  const [jar, { usuario }] = await Promise.all([cookies(), obterUsuarioSessao()])
  return usuario?.tem_pj && jar.get(COOKIE_CARTEIRA)?.value === "pj" ? "pj" : "pf"
}
