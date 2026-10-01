import type { Metadata } from "next"
import Link from "next/link"
import { SearchIcon } from "lucide-react"
import { cn } from "cn"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ListaContas } from "@/features/admin/lista-contas"
import { listarUsuariosAdmin } from "@/lib/api/server"
import type { SituacaoConta, UsuarioAdmin } from "@/lib/api/types"

export const metadata: Metadata = { title: "Contas" }

const FILTROS: { id: SituacaoConta | null; titulo: string }[] = [
  { id: null, titulo: "Todas" },
  { id: "ativos", titulo: "Ativas" },
  { id: "desativados", titulo: "Desativadas" },
]

function lerSituacao(param: unknown): SituacaoConta | null {
  return param === "ativos" || param === "desativados" ? param : null
}

function naSituacao(usuario: UsuarioAdmin, situacao: SituacaoConta | null) {
  return situacao === null || usuario.ativo === (situacao === "ativos")
}

/** Link do filtro, mantendo a busca na URL. */
function hrefFiltro(busca: string, situacao: SituacaoConta | null) {
  const params = new URLSearchParams()
  if (busca) params.set("busca", busca)
  if (situacao) params.set("situacao", situacao)
  return params.size ? `/admin/contas?${params}` : "/admin/contas"
}

/** Contas de usuário: busca, filtro pela situação e as ações do administrador em cada uma. */
export default async function AdminContasPage({ searchParams }: PageProps<"/admin/contas">) {
  const { busca: paramBusca, situacao: paramSituacao } = await searchParams
  const busca = typeof paramBusca === "string" ? paramBusca.trim() : ""
  const situacao = lerSituacao(paramSituacao)
  // Sem o filtro na API: assim os contadores de cada situação respeitam a busca.
  const encontradas = await listarUsuariosAdmin(busca || undefined)
  const usuarios = encontradas.filter((u) => naSituacao(u, situacao))

  return (
    <>
      <PageHeader
        titulo="Contas"
        descricao="Resete a senha de quem pediu ajuda para entrar e desative ou reative o acesso. Dados financeiros não aparecem aqui."
      />

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

        <nav
          aria-label="Filtrar contas pela situação"
          className="-mx-4 flex gap-2 overflow-x-auto px-4 [scrollbar-width:none] md:mx-0 md:px-0"
        >
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
                  {encontradas.filter((u) => naSituacao(u, f.id)).length}
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
              <Link href="/admin/contas" className="underline underline-offset-4">
                Limpar filtros
              </Link>
            </>
          ) : (
            "Nenhuma conta cadastrada ainda."
          )}
        </p>
      ) : (
        <ListaContas usuarios={usuarios} />
      )}
    </>
  )
}
