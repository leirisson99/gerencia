import { cn } from "cn"

import { Bloco, Indicador } from "@/features/dashboard/bloco"
import type { DetalheConta, PaginaEventos } from "@/lib/api/types"
import { formatarDataDeInstante, formatarDataHoraDeInstante } from "@/lib/format"
import { AcoesConta } from "./acoes-conta"
import { LinhaTempo } from "./linha-tempo"
import { ROTULOS_ACAO_ADMIN, ROTULOS_CONTAGEM } from "./rotulos-atividade"

const numero = new Intl.NumberFormat("pt-BR")

/** O uso de uma conta, sem conteúdo: acesso, contagens, linha do tempo e ações do administrador. */
export function DetalheContaAdmin({
  detalhe,
  eventos,
}: {
  detalhe: DetalheConta
  eventos: PaginaEventos
}) {
  const { conta, contagens } = detalhe

  return (
    <>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h1 id="conta-titulo" className={cn("text-title", !conta.ativo && "text-muted-foreground")}>
            {conta.nome}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {conta.email} · <span className="valor">criada em {formatarDataDeInstante(conta.criado_em)}</span>{" "}
            ·{" "}
            {conta.ativo ? (
              "Ativa"
            ) : (
              <span className="font-medium text-saida">Desativada</span>
            )}
          </p>
        </div>
        <AcoesConta usuario={conta} />
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Bloco titulo="Último acesso">
          <Indicador
            valor={detalhe.ultimo_acesso_em ? formatarDataDeInstante(detalhe.ultimo_acesso_em) : "Nunca"}
            legenda="Registrado uma vez por dia"
          />
        </Bloco>
        <Bloco titulo="Sessões abertas">
          <Indicador
            valor={numero.format(detalhe.sessoes_abertas)}
            legenda={detalhe.sessoes_abertas === 1 ? "aparelho conectado" : "aparelhos conectados"}
          />
        </Bloco>
      </div>

      <Bloco titulo="Uso por funcionalidade" className="mt-4">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-4">
          {ROTULOS_CONTAGEM.map(([chave, rotulo]) => (
            <div key={chave}>
              <dt className="text-sm text-muted-foreground">{rotulo}</dt>
              <dd className={cn("valor text-xl", contagens[chave] === 0 && "text-muted-foreground")}>
                {numero.format(contagens[chave])}
              </dd>
            </div>
          ))}
        </dl>
      </Bloco>

      <div className="mt-4 grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Bloco titulo="Linha do tempo">
          <LinhaTempo key={conta.id} usuarioId={conta.id} inicial={eventos} />
        </Bloco>

        <Bloco titulo="Ações do administrador">
          {detalhe.acoes_admin.length === 0 ? (
            <p className="text-muted-foreground">Nenhuma ação registrada.</p>
          ) : (
            <ul className="flex flex-col divide-y">
              {detalhe.acoes_admin.map((acao, i) => (
                <li key={`${acao.ocorrida_em}-${i}`} className="py-2 first:pt-0 last:pb-0">
                  <p>{ROTULOS_ACAO_ADMIN[acao.acao]}</p>
                  <p className="valor text-sm text-muted-foreground">
                    {acao.admin_nome} · {formatarDataHoraDeInstante(acao.ocorrida_em)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Bloco>
      </div>
    </>
  )
}
