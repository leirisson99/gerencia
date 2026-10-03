import type { Carteira } from "./api/types"

/** Grava no navegador a carteira aberta no seletor PF | PJ (lida pelo servidor em `lib/carteira`). */
export function gravarCarteira(valor: Carteira) {
  document.cookie = `carteira=${valor}; path=/; max-age=31536000; samesite=lax`
}
