"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeftIcon, CheckIcon } from "lucide-react"
import { toast } from "sonner"
import { cn } from "cn"

import { ErroForm } from "@/components/forms/erro-form"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ApiError } from "@/lib/api/client"
import { importarLinhas } from "@/lib/api/importacao"
import type { Categoria, LinhaPrevia, Previa, SituacaoLinha } from "@/lib/api/types"
import { formatarCentavos, formatarData } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"

const SITUACAO: Record<SituacaoLinha, { rotulo: string; ajuda: string }> = {
  nova: { rotulo: "Nova", ajuda: "" },
  ja_importada: {
    rotulo: "Já importada",
    ajuda: "Essa movimentação já foi importada antes.",
  },
  possivel_duplicada: {
    rotulo: "Possível duplicada",
    ajuda: "Há um lançamento com a mesma data, tipo e valor. Marque só se for outro gasto.",
  },
  antes_do_primeiro_ciclo: {
    rotulo: "Antes do 1º ciclo",
    ajuda: "A data é anterior ao seu primeiro salário. Só entra se o lote trouxer um salário antes.",
  },
  invalida: { rotulo: "Inválida", ajuda: "Movimentação sem valor." },
}

const BLOQUEADAS: SituacaoLinha[] = ["ja_importada", "invalida"]

type Escolha = { marcada: boolean; categoria: string }

type Props = {
  previa: Previa
  categorias: Categoria[]
  aoVoltar: () => void
}

/** Passo 2: conferir, escolher categorias e confirmar. Grava tudo ou nada. */
export function PreviaExtrato({ previa, categorias, aoVoltar }: Props) {
  const router = useRouter()
  const [escolhas, setEscolhas] = useState<Record<string, Escolha>>(() =>
    Object.fromEntries(
      previa.linhas.map((l) => [
        l.id_externo,
        {
          marcada: l.situacao === "nova",
          categoria: l.categoria_sugerida_id ? String(l.categoria_sugerida_id) : "",
        },
      ])
    )
  )
  const [errosLinha, setErrosLinha] = useState<Record<string, string>>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const marcadas = previa.linhas.filter((l) => escolhas[l.id_externo].marcada)
  const semCategoria = marcadas.filter((l) => !escolhas[l.id_externo].categoria)

  function mudar(id: string, parcial: Partial<Escolha>) {
    setEscolhas((atual) => ({ ...atual, [id]: { ...atual[id], ...parcial } }))
    setErrosLinha((atual) => {
      const resto = { ...atual }
      delete resto[id]
      return resto
    })
  }

  async function confirmar() {
    setErroGeral(null)
    setErrosLinha({})
    if (marcadas.length === 0) {
      setErroGeral("Marque ao menos uma linha para importar.")
      return
    }
    if (semCategoria.length > 0) {
      setErrosLinha(
        Object.fromEntries(semCategoria.map((l) => [l.id_externo, "Escolha uma categoria."]))
      )
      setErroGeral(`Faltam categorias em ${semCategoria.length} linha(s).`)
      return
    }
    setEnviando(true)
    try {
      const resultado = await importarLinhas(
        marcadas.map((l) => ({
          id_externo: l.id_externo,
          data: l.data,
          valor: l.valor,
          tipo: l.tipo,
          descricao: l.descricao,
          categoria_id: Number(escolhas[l.id_externo].categoria),
        }))
      )
      toast.success(
        resultado.ignoradas > 0
          ? `${resultado.criados} lançamento(s) importado(s); ${resultado.ignoradas} já existia(m).`
          : `${resultado.criados} lançamento(s) importado(s).`
      )
      router.push("/lancamentos")
      router.refresh()
    } catch (e) {
      if (e instanceof ApiError && Object.keys(e.campos).length > 0) {
        // Chaves `linhas.<i>.<campo>`: `i` é a posição entre as linhas enviadas.
        const porLinha: Record<string, string> = {}
        for (const [chave, mensagem] of Object.entries(e.campos)) {
          const indice = Number(chave.split(".")[1])
          const linha = marcadas[indice]
          if (linha) porLinha[linha.id_externo] = mensagem
        }
        setErrosLinha(porLinha)
        setErroGeral("Corrija as linhas marcadas e confirme de novo. Nada foi importado.")
      } else {
        setErroGeral(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
      }
    } finally {
      setEnviando(false)
    }
  }

  const { resumo } = previa
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          {previa.linhas.length} movimentação(ões): {resumo.nova} nova(s)
          {resumo.ja_importada > 0 && `, ${resumo.ja_importada} já importada(s)`}
          {resumo.possivel_duplicada > 0 && `, ${resumo.possivel_duplicada} possível(is) duplicada(s)`}
          {resumo.antes_do_primeiro_ciclo > 0 &&
            `, ${resumo.antes_do_primeiro_ciclo} antes do primeiro ciclo`}
          {resumo.invalida > 0 && `, ${resumo.invalida} inválida(s)`}.
        </p>
        <Button variant="ghost" onClick={aoVoltar}>
          <ArrowLeftIcon aria-hidden />
          Outro arquivo
        </Button>
      </div>

      {previa.linhas.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          O extrato não tem movimentações nesse período.
        </p>
      ) : (
        <ul className="border-t">
          {previa.linhas.map((linha) => (
            <LinhaDaPrevia
              key={linha.id_externo}
              linha={linha}
              escolha={escolhas[linha.id_externo]}
              erro={errosLinha[linha.id_externo]}
              categorias={categorias.filter((c) => c.tipo === linha.tipo)}
              aoMudar={(parcial) => mudar(linha.id_externo, parcial)}
            />
          ))}
        </ul>
      )}

      <div className="mt-6 grid gap-4">
        <ErroForm mensagem={erroGeral} />
        <div className="flex flex-wrap items-center gap-4">
          <Button onClick={confirmar} disabled={enviando || previa.linhas.length === 0}>
            <CheckIcon aria-hidden />
            {enviando ? "Importando…" : `Importar ${marcadas.length} lançamento(s)`}
          </Button>
          <span className="text-sm text-muted-foreground">
            Tudo ou nada: se alguma linha tiver problema, nada é gravado.
          </span>
        </div>
      </div>
    </div>
  )
}

type PropsLinha = {
  linha: LinhaPrevia
  escolha: Escolha
  erro?: string
  categorias: Categoria[]
  aoMudar: (parcial: Partial<Escolha>) => void
}

function LinhaDaPrevia({ linha, escolha, erro, categorias, aoMudar }: PropsLinha) {
  const bloqueada = BLOQUEADAS.includes(linha.situacao)
  const situacao = SITUACAO[linha.situacao]
  const descricao = linha.descricao ?? "Sem descrição"
  return (
    <li
      className={cn(
        "grid grid-cols-[auto_1fr_auto] items-start gap-x-3 gap-y-2 border-b px-1 py-4 sm:grid-cols-[auto_6rem_1fr_14rem_auto] sm:items-center",
        (bloqueada || !escolha.marcada) && "text-muted-foreground"
      )}
    >
      <Checkbox
        checked={escolha.marcada}
        disabled={bloqueada}
        onCheckedChange={(v) => aoMudar({ marcada: v === true })}
        aria-label={`Importar ${descricao} de ${formatarData(linha.data)}`}
        className="mt-1 sm:mt-0"
      />
      <span className="valor hidden text-sm sm:block">{formatarData(linha.data)}</span>
      <span className="min-w-0">
        <span className="block truncate" title={descricao}>
          {descricao}
        </span>
        <span className="block text-sm text-muted-foreground">
          <span className="sm:hidden">{formatarData(linha.data)} · </span>
          {linha.situacao === "nova" ? null : (
            <span title={situacao.ajuda} className="underline decoration-dotted">
              {situacao.rotulo}
            </span>
          )}
        </span>
        {erro && <span className="block text-sm text-destructive">{erro}</span>}
      </span>
      <div className="col-span-3 col-start-2 row-start-2 sm:col-span-1 sm:col-start-auto sm:row-start-auto">
        <Select
          value={escolha.categoria}
          onValueChange={(categoria) => aoMudar({ categoria, marcada: !bloqueada })}
          disabled={bloqueada}
        >
          <SelectTrigger
            aria-label={`Categoria de ${descricao}`}
            aria-invalid={erro ? true : undefined}
            className="w-full"
          >
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent position="popper">
            {categorias.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <span
        className={cn(
          "valor col-start-3 row-start-1 text-right sm:col-start-auto",
          linha.tipo === "saida" && !bloqueada && escolha.marcada && "text-saida"
        )}
      >
        {linha.tipo === "saida" ? "−" : "+"}
        {formatarCentavos(linha.valor)}
      </span>
    </li>
  )
}
