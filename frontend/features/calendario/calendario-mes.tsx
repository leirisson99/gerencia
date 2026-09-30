"use client"

import { useState } from "react"
import { CheckIcon } from "lucide-react"
import { cn } from "cn"

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import type { Categoria, Lancamento } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { semanasDoMes } from "./datas"

const DIAS_DA_SEMANA = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"]
const semanaLonga = new Intl.DateTimeFormat("pt-BR", { weekday: "long", timeZone: "UTC" })
const mesLongo = new Intl.DateTimeFormat("pt-BR", { month: "long", timeZone: "UTC" })

type Props = {
  /** `YYYY-MM` */
  mes: string
  /** Hoje em São Paulo, ISO. */
  hoje: string
  /** Saídas do mês (previstas e realizadas). */
  saidas: Lancamento[]
  categorias: Categoria[]
  sugestaoSalario: number | null
}

/** Estado de um dia: o que venceu sem pagar pesa mais que o que ainda vai vencer. */
type Estado = "vencido" | "a_vencer" | "pago"

type Dia = { data: string; aPagar: Lancamento[]; pagos: Lancamento[]; estado: Estado }

function somar(lancamentos: Lancamento[]) {
  return lancamentos.reduce((soma, l) => soma + l.valor, 0)
}

function utc(data: string) {
  return new Date(`${data}T00:00:00Z`)
}

/**
 * Pagamentos do mês. O vermelho marca só o que venceu sem pagar; o que vai vencer fica em preto e
 * o que já foi pago, em cinza. Clicar num dia (ou num item da agenda) abre o painel do dia.
 */
export function CalendarioMes({ mes, hoje, saidas, categorias, sugestaoSalario }: Props) {
  const [aberto, setAberto] = useState(false)
  // Continua preenchido enquanto o painel fecha, para o conteúdo não sumir na animação.
  const [selecionado, setSelecionado] = useState<string | null>(null)
  const nomes = new Map(categorias.map((c) => [c.id, c.nome]))
  const titulo = (l: Lancamento) => l.descricao || nomes.get(l.categoria_id) || "Pagamento"

  const dias = new Map<string, Dia>()
  for (const l of saidas) {
    const dia = dias.get(l.data) ?? { data: l.data, aPagar: [], pagos: [], estado: "pago" as Estado }
    if (l.status === "previsto") dia.aPagar.push(l)
    else dia.pagos.push(l)
    dias.set(l.data, dia)
  }
  for (const dia of dias.values()) {
    if (dia.aPagar.length > 0) dia.estado = dia.data < hoje ? "vencido" : "a_vencer"
  }

  const ordenados = [...dias.values()].sort((a, b) => a.data.localeCompare(b.data))
  const vencidos = ordenados.filter((d) => d.estado === "vencido")
  const aVencer = ordenados.filter((d) => d.estado === "a_vencer")
  const totalVencido = vencidos.reduce((s, d) => s + somar(d.aPagar), 0)
  const totalAVencer = aVencer.reduce((s, d) => s + somar(d.aPagar), 0)
  const totalPago = ordenados.reduce((s, d) => s + somar(d.pagos), 0)

  function abrir(data: string) {
    setSelecionado(data)
    setAberto(true)
  }

  const doDia = selecionado ? dias.get(selecionado) : undefined

  return (
    <>
      <dl className="mb-8 grid grid-cols-3 gap-4 sm:max-w-2xl">
        <Resumo rotulo="Vencido" valor={totalVencido} destaque={totalVencido > 0} />
        <Resumo rotulo="A vencer" valor={totalAVencer} />
        <Resumo rotulo="Pago" valor={totalPago} discreto />
      </dl>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_20rem]">
        {/* Grade: linhas finas pelo fundo cinza aparecendo entre as células. */}
        <div className="overflow-hidden rounded-lg border bg-border">
          <div className="grid grid-cols-7 gap-px">
            {DIAS_DA_SEMANA.map((d) => (
              <div key={d} className="bg-background px-2 py-2 text-xs text-muted-foreground" aria-hidden>
                {d}
              </div>
            ))}
            {semanasDoMes(mes)
              .flat()
              .map((data, i) => {
                if (!data) return <div key={`vazio-${i}`} className="bg-muted" />
                const dia = dias.get(data)
                return (
                  <Celula
                    key={data}
                    data={data}
                    hoje={hoje}
                    dia={dia}
                    titulo={titulo}
                    aoAbrir={() => abrir(data)}
                  />
                )
              })}
          </div>
        </div>

        <aside aria-label="Agenda do mês" className="grid content-start gap-8">
          <Grupo titulo="Vencidos" dias={vencidos} estado="vencido" nomeDe={titulo} aoAbrir={abrir} />
          <Grupo titulo="A vencer" dias={aVencer} estado="a_vencer" nomeDe={titulo} aoAbrir={abrir} />
          {ordenados.length === 0 && (
            <p className="text-muted-foreground">
              Nenhum pagamento neste mês. Contas fixas e parcelas aparecem aqui quando o ciclo delas abre.
            </p>
          )}
          {vencidos.length === 0 && aVencer.length === 0 && ordenados.length > 0 && (
            <p className="flex items-center gap-2 text-muted-foreground">
              <CheckIcon className="size-4" aria-hidden />
              Tudo pago neste mês.
            </p>
          )}
        </aside>
      </div>

      <Sheet open={aberto} onOpenChange={setAberto}>
        <SheetContent
          side="right"
          className="w-full gap-0 overflow-y-auto data-[side=right]:w-full data-[side=right]:sm:max-w-md"
        >
          <SheetHeader className="gap-1 border-b px-6 pt-6 pb-5">
            <SheetTitle className="flex items-baseline gap-3">
              <span className="valor text-display font-semibold">
                {selecionado && Number(selecionado.slice(8))}
              </span>
              <span className="grid text-base leading-tight font-normal">
                <span>de {selecionado && mesLongo.format(utc(selecionado))}</span>
                <span className="text-muted-foreground">
                  {selecionado && semanaLonga.format(utc(selecionado))}
                </span>
              </span>
            </SheetTitle>
            <SheetDescription className={cn(doDia?.estado === "vencido" && "text-saida")}>
              {!doDia && "Nenhum pagamento neste dia."}
              {doDia?.estado === "vencido" && `Venceu sem pagamento: ${formatarCentavos(somar(doDia.aPagar))}.`}
              {doDia?.estado === "a_vencer" && `Vence neste dia: ${formatarCentavos(somar(doDia.aPagar))}.`}
              {doDia?.estado === "pago" && `Tudo pago: ${formatarCentavos(somar(doDia.pagos))}.`}
            </SheetDescription>
          </SheetHeader>
          {doDia && (
            <div className="grid gap-8 px-6 py-6">
              {doDia.aPagar.length > 0 && (
                <section>
                  <h3 className="mb-2 text-sm font-medium">A pagar</h3>
                  <ListaLancamentos
                    lancamentos={doDia.aPagar}
                    categorias={categorias}
                    sugestaoSalario={sugestaoSalario}
                    semData
                  />
                </section>
              )}
              {doDia.pagos.length > 0 && (
                <section>
                  <h3 className="mb-2 text-sm font-medium text-muted-foreground">Pago</h3>
                  <ListaLancamentos
                    lancamentos={doDia.pagos}
                    categorias={categorias}
                    sugestaoSalario={sugestaoSalario}
                    semData
                  />
                </section>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  )
}

function Resumo({
  rotulo,
  valor,
  destaque = false,
  discreto = false,
}: {
  rotulo: string
  valor: number
  destaque?: boolean
  discreto?: boolean
}) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{rotulo}</dt>
      <dd
        className={cn(
          "valor mt-1 text-lg font-semibold sm:text-title",
          destaque && "text-saida",
          discreto && "text-muted-foreground"
        )}
      >
        {formatarCentavos(valor)}
      </dd>
    </div>
  )
}

function Celula({
  data,
  hoje,
  dia,
  titulo,
  aoAbrir,
}: {
  data: string
  hoje: string
  dia: Dia | undefined
  titulo: (l: Lancamento) => string
  aoAbrir: () => void
}) {
  const passado = data < hoje
  const estado = dia?.estado
  const pendente = estado === "vencido" || estado === "a_vencer"
  const valor = dia ? somar(pendente ? dia.aPagar : dia.pagos) : 0
  const itens = dia ? (pendente ? dia.aPagar : dia.pagos) : []

  const rotulo = [
    `${semanaLonga.format(utc(data))}, ${Number(data.slice(8))} de ${mesLongo.format(utc(data))}`,
    estado === "vencido" && `${formatarCentavos(valor)} vencido`,
    estado === "a_vencer" && `${formatarCentavos(valor)} a vencer`,
    estado === "pago" && `${formatarCentavos(valor)} pago`,
    !dia && "sem pagamentos",
  ]
    .filter(Boolean)
    .join(", ")

  return (
    <button
      type="button"
      onClick={aoAbrir}
      aria-label={rotulo}
      className={cn(
        "relative flex min-h-16 flex-col bg-background p-1.5 text-left transition-colors hover:bg-muted/50 focus-visible:z-10 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring md:min-h-30 md:p-2.5",
        // Filete no topo: vermelho quando venceu, preto quando vai vencer.
        estado === "vencido" && "shadow-[inset_0_2px_0_var(--destructive)]",
        estado === "a_vencer" && "shadow-[inset_0_2px_0_var(--foreground)]"
      )}
    >
      <span className="flex items-center justify-between gap-1">
        <span
          className={cn(
            "valor flex size-7 items-center justify-center rounded-full text-sm",
            data === hoje && "bg-foreground font-semibold text-background",
            data !== hoje && passado && !pendente && "text-muted-foreground/60"
          )}
        >
          {Number(data.slice(8))}
        </span>
        {estado === "vencido" && (
          <span className="hidden text-xs font-medium text-saida md:inline">vencido</span>
        )}
      </span>

      {dia && (
        <span className="mt-auto hidden min-w-0 md:block">
          <span
            className={cn(
              "valor flex items-center gap-1 font-semibold",
              estado === "vencido" && "text-saida",
              estado === "pago" && "text-sm font-normal text-muted-foreground"
            )}
          >
            {estado === "pago" && <CheckIcon className="size-3.5" aria-hidden />}
            {formatarCentavos(valor)}
          </span>
          {pendente && (
            <span className="block truncate text-xs text-muted-foreground">
              {titulo(itens[0])}
              {itens.length > 1 && ` +${itens.length - 1}`}
            </span>
          )}
        </span>
      )}

      {/* No celular, só a marca do estado; a agenda abaixo traz os detalhes. */}
      {pendente && (
        <span
          className={cn(
            "mt-auto h-1 w-4 rounded-full md:hidden",
            estado === "vencido" ? "bg-saida" : "bg-foreground"
          )}
          aria-hidden
        />
      )}
      {estado === "pago" && (
        <CheckIcon className="mt-auto size-3 text-muted-foreground md:hidden" aria-hidden />
      )}
    </button>
  )
}

function Grupo({
  titulo,
  dias,
  estado,
  nomeDe,
  aoAbrir,
}: {
  titulo: string
  dias: Dia[]
  estado: Estado
  nomeDe: (l: Lancamento) => string
  aoAbrir: (data: string) => void
}) {
  if (dias.length === 0) return null
  const itens = dias.flatMap((d) => d.aPagar)
  return (
    <section>
      <h2
        className={cn(
          "mb-2 flex items-baseline justify-between text-sm font-medium",
          estado === "vencido" && "text-saida"
        )}
      >
        {titulo}
        <span className="valor font-normal">{formatarCentavos(somar(itens))}</span>
      </h2>
      <ul className="border-t">
        {itens.map((l) => {
          const data = utc(l.data)
          return (
            <li key={l.id} className="border-b">
              <button
                type="button"
                onClick={() => aoAbrir(l.data)}
                className="grid w-full grid-cols-[2.5rem_1fr_auto] items-center gap-3 py-3 text-left transition-colors hover:bg-muted/60 focus-visible:outline-2 focus-visible:outline-ring"
              >
                <span className="text-center leading-none">
                  <span className="valor block text-lg font-semibold">{Number(l.data.slice(8))}</span>
                  <span className="text-xs text-muted-foreground">
                    {DIAS_DA_SEMANA[data.getUTCDay()]}
                  </span>
                </span>
                <span className="min-w-0 truncate">{nomeDe(l)}</span>
                <span className={cn("valor text-sm font-medium", estado === "vencido" && "text-saida")}>
                  {formatarCentavos(l.valor)}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
