import type { Metadata } from "next"
import Link from "next/link"
import { SearchIcon } from "lucide-react"
import { cn } from "cn"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AlternarSituacao } from "@/features/admin/alternar-situacao"
import { FormasPagamento } from "@/features/admin/formas-pagamento"
import { GraficoMovimentacoes } from "@/features/admin/grafico-movimentacoes"
import { ResetarSenha } from "@/features/admin/resetar-senha"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { FORMAS } from "@/features/dividas/rotulos"
import { listarUsuariosAdmin, obterResumoAdmin } from "@/lib/api/server"
import type { SituacaoConta } from "@/lib/api/types"
import { formatarDataDeInstante } from "@/lib/format"

export const metadata: Metadata = { title: "Administração" }

const FILTROS: { id: SituacaoConta | null; titulo: string }[] = [
  { id: null, titulo: "Todas" },
  { id: "ativos", titulo: "Ativas" },
  { id: "desativados", titulo: "Desativadas" },
]

const numero = new Intl.NumberFormat("pt-BR")

function lerSituacao(param: unknown): SituacaoConta | null {
  return param === "ativos" || param === "desativados" ? param : null
}

/** Link do filtro, mantendo a busca na URL. */
function hrefFiltro(busca: string, situacao: SituacaoConta | null) {
  const params = new URLSearchParams()
  if (busca) params.set("busca", busca)
  if (situacao) params.set("situacao", situacao)
  return params.size ? `/admin?${params}` : "/admin"
}

/**
 * Painel do administrador: contagens globais de uso (sem valores nem dados por conta) e as contas,
 * com reset de senha e desativação (constituição 5.0.0, papel admin).
 */
export default async function AdminPage({ searchParams }: PageProps<"/admin">) {
  const { busca: paramBusca, situacao: paramSituacao } = await searchParams
  const busca = typeof paramBusca === "string" ? paramBusca.trim() : ""
  const situacao = lerSituacao(paramSituacao)
  const [resumo, usuarios] = await Promise.all([
    obterResumoAdmin(),
    listarUsuariosAdmin(busca || undefined, situacao ?? undefined),
  ])
  const { contas, lancamentos, dividas_por_forma: formas } = resumo
  const dividas = formas.reduce((soma, f) => soma + f.quantidade, 0)
  const quantasPorFiltro = (id: SituacaoConta | null) =>
    id === "ativos" ? contas.ativas : id === "desativados" ? contas.desativadas : contas.total

  return (
    <>
      <PageHeader
        titulo="Administração"
        descricao="Uso do sistema somado entre todas as contas, sem valores em reais. Abaixo, as contas: resete senhas e desative ou reative o acesso."
      />

      <div className="mb-4 grid gap-4 sm:grid-cols-3">
        <Bloco titulo="Contas">
          <Indicador
            valor={numero.format(contas.total)}
            legenda={`${numero.format(contas.ativas)} ativas · ${numero.format(contas.desativadas)} desativadas`}
          />
        </Bloco>
        <Bloco titulo="Lançamentos">
          <Indicador
            valor={numero.format(lancamentos.total)}
            legenda={`${numero.format(lancamentos.realizados)} realizados · ${numero.format(lancamentos.previstos)} previstos`}
          />
        </Bloco>
        <Bloco titulo="Dívidas">
          <Indicador
            valor={numero.format(dividas)}
            legenda={dividas ? `Mais usada: ${FORMAS[formas[0].forma]}` : "Nenhuma ainda"}
          />
        </Bloco>
      </div>

      <div className="mb-10 grid gap-4 lg:grid-cols-3">
        <Bloco titulo="Movimentações realizadas por mês" className="lg:col-span-2">
          <GraficoMovimentacoes meses={resumo.por_mes} />
        </Bloco>
        <Bloco titulo="Formas de pagamento das dívidas">
          <FormasPagamento formas={formas} />
        </Bloco>
      </div>

      <h2 className="mb-4 text-xl">Contas</h2>

      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {/* Formulário GET: a busca fica na URL e funciona sem JavaScript. */}
        <form role="search" className="flex w-full max-w-xl gap-2">
          {situacao && <input type="hidden" name="situacao" value={situacao} />}
          <label htmlFor="busca" className="sr-only">
            Buscar por nome ou e-mail
          </label>
          <Input
            id="busca"
            name="busca"
            type="search"
            defaultValue={busca}
            placeholder="Buscar por nome ou e-mail"
            autoComplete="off"
          />
          <Button type="submit" variant="outline">
            <SearchIcon aria-hidden />
            Buscar
          </Button>
        </form>

        <nav aria-label="Filtrar contas pela situação" className="flex gap-2">
          {FILTROS.map((f) => {
            const ativo = f.id === situacao
            return (
              <Link
                key={f.titulo}
                href={hrefFiltro(busca, f.id)}
                aria-current={ativo ? "page" : undefined}
                className={cn(
                  "flex h-9 shrink-0 items-center gap-1.5 rounded-full border px-4 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                  ativo
                    ? "border-primary bg-primary text-primary-foreground"
                    : "bg-background text-muted-foreground hover:text-foreground"
                )}
              >
                {f.titulo}
                <span className={cn("valor text-xs", ativo ? "opacity-70" : "opacity-60")}>
                  {quantasPorFiltro(f.id)}
                </span>
              </Link>
            )
          })}
        </nav>
      </div>

      {usuarios.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          {busca || situacao ? (
            <>
              Nenhuma conta encontrada{busca && <> para &ldquo;{busca}&rdquo;</>}.{" "}
              <Link href="/admin" className="underline underline-offset-4">
                Limpar filtros
              </Link>
            </>
          ) : (
            "Nenhuma conta cadastrada ainda."
          )}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-left">
            <caption className="sr-only">Contas de usuário</caption>
            <thead className="text-sm text-muted-foreground">
              <tr className="border-b">
                <th scope="col" className="py-3 pr-4 font-medium">Nome</th>
                <th scope="col" className="py-3 pr-4 font-medium">E-mail</th>
                <th scope="col" className="py-3 pr-4 font-medium">Criada em</th>
                <th scope="col" className="py-3 pr-4 font-medium">Situação</th>
                <th scope="col" className="py-3 font-medium">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} className="border-b">
                  <td className={cn("py-3 pr-4", !u.ativo && "text-muted-foreground")}>{u.nome}</td>
                  <td className="py-3 pr-4 text-muted-foreground">{u.email}</td>
                  <td className="valor py-3 pr-4 text-muted-foreground">
                    {formatarDataDeInstante(u.criado_em)}
                  </td>
                  <td className="py-3 pr-4 text-sm">
                    {u.ativo ? "Ativa" : <span className="font-medium text-saida">Desativada</span>}
                  </td>
                  <td className="py-3">
                    <div className="flex justify-end gap-2">
                      <ResetarSenha usuario={u} />
                      <AlternarSituacao usuario={u} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
