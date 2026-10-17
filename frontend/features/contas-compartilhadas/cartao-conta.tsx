import Link from "next/link"
import { AlertCircleIcon } from "lucide-react"

import type { ContaResumo } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { rotuloPendentes, rotuloPessoas } from "./rotulos"

/** Resumo de uma conta compartilhada na lista: total, quantas pessoas e a sua parte. */
export function CartaoConta({ conta }: { conta: ContaResumo }) {
  const pendentes = rotuloPendentes(conta.qtd_convidados_pendentes)
  return (
    <Link
      href={`/contas-compartilhadas/${conta.id}`}
      className="block rounded-lg border p-5 transition-colors hover:bg-muted/60"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{conta.descricao}</p>
          <p className="truncate text-sm text-muted-foreground">
            {conta.papel === "dono" ? "Você é o dono" : "Você participa"} · vence todo dia{" "}
            {conta.dia_vencimento}
          </p>
        </div>
        {!conta.ativa && <span className="shrink-0 text-sm text-muted-foreground">Desativada</span>}
      </div>

      <p className="valor mt-4 text-xl font-semibold">
        {conta.valor_total === null ? "Sem total no mês" : formatarCentavos(conta.valor_total)}
      </p>
      <div className="valor mt-2 flex flex-wrap justify-between gap-x-3 text-sm text-muted-foreground">
        <span>
          {rotuloPessoas(conta.qtd_pessoas)}
          {pendentes && ` · ${pendentes}`}
        </span>
        {conta.minha_cota && <span>sua parte {formatarCentavos(conta.minha_cota.valor)}</span>}
      </div>
      {conta.falta_informar_total && (
        <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
          <AlertCircleIcon className="size-4 shrink-0" aria-hidden />
          Falta informar o total deste mês.
        </p>
      )}
    </Link>
  )
}
