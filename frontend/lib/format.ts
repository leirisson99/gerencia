const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })
const dataCurta = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" })

/** Dinheiro vem sempre em centavos inteiros; nunca use float para guardar valor. */
export function formatarCentavos(centavos: number): string {
  if (!Number.isInteger(centavos)) throw new Error("Valor em centavos deve ser inteiro.")
  return moeda.format(centavos / 100)
}

/** `11987654321` → `(11) 98765-4321` */
export function formatarTelefone(digitos: string): string {
  const d = digitos.replace(/\D/g, "")
  if (d.length === 11) return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
  if (d.length === 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`
  return digitos
}

/** Máscara progressiva para o campo de telefone. */
export function mascararTelefone(valor: string): string {
  const d = valor.replace(/\D/g, "").slice(0, 11)
  if (d.length <= 2) return d.length ? `(${d}` : ""
  const resto = d.slice(2)
  const corte = d.length === 11 ? 5 : 4
  if (resto.length <= corte) return `(${d.slice(0, 2)}) ${resto}`
  return `(${d.slice(0, 2)}) ${resto.slice(0, corte)}-${resto.slice(corte)}`
}

/** `1995-03-15` → `15/03/1995` */
export function formatarData(iso: string): string {
  return dataCurta.format(new Date(`${iso}T00:00:00Z`))
}

/** Limite da API: R$ 999.999.999,99 (backend/app/schemas/lancamento.py). */
export const VALOR_MAXIMO = 99_999_999_999
const DIGITOS_MAXIMOS = String(VALOR_MAXIMO).length

/**
 * Campo de valor: cada dígito digitado entra pela direita, como em app de banco
 * (`1`, `12`, `123` → 0,01 · 0,12 · 1,23). Trabalha só com inteiros.
 */
export function centavosDeTexto(texto: string): number {
  const digitos = texto.replace(/\D/g, "").replace(/^0+/, "").slice(0, DIGITOS_MAXIMOS)
  return digitos ? Number.parseInt(digitos, 10) : 0
}

/** `123456` → `1.234,56`, sem símbolo e sem passar por float. */
export function formatarCentavosCampo(centavos: number): string {
  if (!Number.isInteger(centavos)) throw new Error("Valor em centavos deve ser inteiro.")
  const texto = String(Math.abs(centavos)).padStart(3, "0")
  const reais = texto.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".")
  return `${reais},${texto.slice(-2)}`
}

/** `2026-10-05` → `05/10` */
export function formatarDiaMes(iso: string): string {
  const [, mes, dia] = iso.split("-")
  return `${dia}/${mes}`
}

/** Hoje em São Paulo, no formato ISO `YYYY-MM-DD`. */
export function hojeSaoPaulo(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo" }).format(new Date())
}

/** Dias corridos entre duas datas ISO (`fim` − `inicio`). */
export function diasEntre(inicio: string, fim: string): number {
  const utc = (iso: string) => {
    const [a, m, d] = iso.split("-").map(Number)
    return Date.UTC(a, m - 1, d)
  }
  return Math.round((utc(fim) - utc(inicio)) / 86_400_000)
}

const dataSaoPaulo = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo" })

/** Instante ISO (UTC) → data no fuso de São Paulo: `2026-09-29T02:00:00Z` → `28/09/2026`. */
export function formatarDataDeInstante(iso: string): string {
  return dataSaoPaulo.format(new Date(iso))
}

const nomeMes = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" })
const diaLongo = new Intl.DateTimeFormat("pt-BR", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "UTC",
})

/** `2026-10` → `outubro de 2026` */
export function formatarMes(mes: string): string {
  return nomeMes.format(new Date(`${mes}-01T00:00:00Z`))
}

/** `2026-10-15` → `quinta-feira, 15 de outubro` */
export function formatarDiaLongo(iso: string): string {
  return diaLongo.format(new Date(`${iso}T00:00:00Z`))
}

/** Valor sem centavos quando eles são zero: `1000` → `R$ 10`; `1050` → `R$ 10,50`. */
export function formatarCentavosCurto(centavos: number): string {
  if (!Number.isInteger(centavos)) throw new Error("Valor em centavos deve ser inteiro.")
  if (centavos % 100 !== 0) return formatarCentavos(centavos)
  return `R$ ${formatarCentavosCampo(centavos).slice(0, -3)}`
}

const moedaCompacta = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
})

/** Para eixo de gráfico: `123456` → `R$ 1,2 mil`. */
export function formatarCentavosCompacto(centavos: number): string {
  return moedaCompacta.format(centavos / 100)
}
