import { cn } from "cn"

import type { UsuarioAdmin } from "@/lib/api/types"
import { formatarDataDeInstante } from "@/lib/format"
import { AcoesConta } from "./acoes-conta"

function Situacao({ ativo }: { ativo: boolean }) {
  return ativo ? (
    <span className="text-sm text-muted-foreground">Ativa</span>
  ) : (
    <span className="text-sm font-medium text-saida">Desativada</span>
  )
}

/** Contas em tabela no desktop e em cartões no celular, cada uma com o menu de ações. */
export function ListaContas({ usuarios }: { usuarios: UsuarioAdmin[] }) {
  return (
    <>
      <table className="w-full text-left max-md:hidden">
        <caption className="sr-only">Contas de usuário</caption>
        <thead className="text-sm text-muted-foreground">
          <tr className="border-b">
            <th scope="col" className="py-3 pr-4 font-medium">Nome</th>
            <th scope="col" className="py-3 pr-4 font-medium">E-mail</th>
            <th scope="col" className="py-3 pr-4 font-medium">Criada em</th>
            <th scope="col" className="py-3 pr-4 font-medium">Situação</th>
            <th scope="col" className="w-10 py-3 font-medium">
              <span className="sr-only">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id} className="border-b">
              <td className={cn("py-3 pr-4", !u.ativo && "text-muted-foreground")}>{u.nome}</td>
              <td className="py-3 pr-4 text-muted-foreground">{u.email}</td>
              <td className="valor py-3 pr-4 text-muted-foreground">{formatarDataDeInstante(u.criado_em)}</td>
              <td className="py-3 pr-4">
                <Situacao ativo={u.ativo} />
              </td>
              <td className="py-2 text-right">
                <AcoesConta usuario={u} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ul className="flex flex-col gap-3 md:hidden" aria-label="Contas de usuário">
        {usuarios.map((u) => (
          <li key={u.id} className="flex items-start gap-3 rounded-2xl border p-4">
            <div className="min-w-0 flex-1">
              <p className={cn("truncate font-medium", !u.ativo && "text-muted-foreground")}>{u.nome}</p>
              <p className="truncate text-sm text-muted-foreground">{u.email}</p>
              <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <span className="valor">Criada em {formatarDataDeInstante(u.criado_em)}</span>
                <span aria-hidden>·</span>
                <Situacao ativo={u.ativo} />
              </p>
            </div>
            <AcoesConta usuario={u} />
          </li>
        ))}
      </ul>
    </>
  )
}
