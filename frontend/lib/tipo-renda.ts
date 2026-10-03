import type { Carteira, TipoRenda } from "@/lib/api/types"

// Espelha backend/app/domain/ciclo.py: o prestador tem ciclo pelo mês do calendário; quem tem
// salário (clt, clt_prestador) tem ciclo aberto por cada salário lançado.

export const TIPOS_RENDA: { valor: TipoRenda; rotulo: string; descricao: string }[] = [
  { valor: "clt", rotulo: "CLT", descricao: "Recebo salário. O ciclo abre a cada salário lançado." },
  {
    valor: "prestador",
    rotulo: "Presto serviço",
    descricao: "Recebo por serviço. O ciclo é o mês do calendário.",
  },
  {
    valor: "clt_prestador",
    rotulo: "CLT e presto serviço",
    descricao: "Recebo salário e por serviço. O ciclo abre a cada salário lançado.",
  },
]

/** Ciclo pelo mês do calendário, sem depender de salário. */
export function ehPrestador(tipo: TipoRenda): boolean {
  return tipo === "prestador"
}

/** Acesso à tela de serviços a receber. */
export function temServicos(tipo: TipoRenda): boolean {
  return tipo === "prestador" || tipo === "clt_prestador"
}

/** Como o ciclo aparece nos textos: "ciclo" para quem tem salário, "mês" para o prestador. */
export function nomeCiclo(tipo: TipoRenda): "ciclo" | "mês" {
  return ehPrestador(tipo) ? "mês" : "ciclo"
}

/** Espelha ciclo_pelo_mes de backend/app/domain/usuario.py: a PJ conta sempre pelo mês. */
export function cicloPeloMes(tipo: TipoRenda, carteira: Carteira = "pf"): boolean {
  return carteira === "pj" || ehPrestador(tipo)
}

/** Quem pode ligar a carteira PJ ("Tenho CNPJ"). */
export function podeTerPj(tipo: TipoRenda): boolean {
  return temServicos(tipo)
}
