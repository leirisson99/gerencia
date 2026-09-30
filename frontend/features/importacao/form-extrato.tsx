"use client"

import { useEffect, useId, useState } from "react"
import { FileUpIcon } from "lucide-react"

import { Campo } from "@/components/forms/campo"
import { ErroForm } from "@/components/forms/erro-form"
import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ApiError } from "@/lib/api/client"
import { lerExtrato, listarBancos } from "@/lib/api/importacao"
import type { Banco, FormatoExtrato, MapeamentoCsv, Previa, PreviaIn } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

// Espelha backend/app/schemas/importacao.py.
const MAX_BYTES = 2 * 1024 * 1024

const ROTULO_FORMATO: Record<FormatoExtrato, string> = {
  ofx: "OFX",
  csv: "CSV",
  pdf: "PDF",
  csv_generico: "CSV (informar colunas)",
}

const ACEITA: Record<FormatoExtrato, string> = {
  ofx: ".ofx,.OFX",
  csv: ".csv,.txt",
  pdf: ".pdf,application/pdf",
  csv_generico: ".csv,.txt",
}

const MAPEAMENTO_PADRAO: MapeamentoCsv = {
  separador: ";",
  pular_linhas: 0,
  tem_cabecalho: true,
  coluna_data: 0,
  formato_data: "dd/mm/aaaa",
  coluna_descricao: 1,
  coluna_valor: 2,
  coluna_credito: null,
  coluna_debito: null,
  separador_decimal: ",",
}

function paraBase64(arquivo: File): Promise<string> {
  return new Promise((resolver, rejeitar) => {
    const leitor = new FileReader()
    leitor.onload = () => resolver(String(leitor.result).split(",", 2)[1] ?? "")
    leitor.onerror = () => rejeitar(leitor.error)
    leitor.readAsDataURL(arquivo)
  })
}

type Props = {
  aoLer: (previa: Previa, pedido: Omit<PreviaIn, "arquivo_base64">) => void
}

/** Passo 1: banco, formato e arquivo. Nada é gravado aqui. */
export function FormExtrato({ aoLer }: Props) {
  const [bancos, setBancos] = useState<Banco[]>([])
  const [codigo, setCodigo] = useState("")
  const [formato, setFormato] = useState<FormatoExtrato | "">("")
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [mapeamento, setMapeamento] = useState<MapeamentoCsv>(MAPEAMENTO_PADRAO)
  const [lendo, setLendo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const arquivoId = useId()

  useEffect(() => {
    listarBancos()
      .then(setBancos)
      .catch(() => setErro("Não foi possível carregar a lista de bancos."))
  }, [])

  const banco = bancos.find((b) => b.codigo === codigo)

  function escolherBanco(novo: string) {
    setCodigo(novo)
    const formatos = bancos.find((b) => b.codigo === novo)?.formatos ?? []
    // Com um formato só, já deixa escolhido.
    setFormato(formatos.length === 1 ? formatos[0] : "")
    setArquivo(null)
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    setErro(null)
    if (!banco || !formato || !arquivo) {
      setErro("Escolha o banco, o formato e o arquivo do extrato.")
      return
    }
    if (arquivo.size > MAX_BYTES) {
      setErro("O arquivo passa de 2 MB. Baixe um período menor no seu banco.")
      return
    }
    setLendo(true)
    try {
      const pedido: Omit<PreviaIn, "arquivo_base64"> = {
        banco: banco.codigo,
        formato,
        mapeamento: formato === "csv_generico" ? mapeamento : null,
      }
      const previa = await lerExtrato({ ...pedido, arquivo_base64: await paraBase64(arquivo) })
      aoLer(previa, pedido)
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setLendo(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate className="max-w-xl">
      <FieldGroup>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field>
            <FieldLabel htmlFor={`${arquivoId}-banco`}>Banco</FieldLabel>
            <Select value={codigo} onValueChange={escolherBanco}>
              <SelectTrigger id={`${arquivoId}-banco`} className="w-full text-base data-[size=default]:h-10">
                <SelectValue placeholder="Escolha o banco" />
              </SelectTrigger>
              <SelectContent position="popper">
                {bancos.map((b) => (
                  <SelectItem key={b.codigo} value={b.codigo}>
                    {b.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field data-disabled={!banco || undefined}>
            <FieldLabel htmlFor={`${arquivoId}-formato`}>Formato do arquivo</FieldLabel>
            <Select
              value={formato}
              onValueChange={(valor) => setFormato(valor as FormatoExtrato)}
              disabled={!banco}
            >
              <SelectTrigger
                id={`${arquivoId}-formato`}
                className="w-full text-base data-[size=default]:h-10"
              >
                <SelectValue placeholder="Escolha o formato" />
              </SelectTrigger>
              <SelectContent position="popper">
                {banco?.formatos.map((f) => (
                  <SelectItem key={f} value={f}>
                    {ROTULO_FORMATO[f]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
        </div>

        <Field>
          <FieldLabel htmlFor={arquivoId}>Arquivo do extrato</FieldLabel>
          <input
            id={arquivoId}
            type="file"
            accept={formato ? ACEITA[formato] : undefined}
            disabled={!formato}
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
            className="block w-full text-sm file:mr-4 file:border file:border-input file:bg-background file:px-3 file:py-2 file:text-sm disabled:opacity-50"
          />
          <FieldDescription>
            Baixe o extrato da <strong>conta</strong> no app ou site do banco. Extrato de fatura do
            cartão não é aceito: a fatura entra como um gasto único em &quot;Cartão de
            crédito&quot;.
          </FieldDescription>
        </Field>

        {formato === "csv_generico" && (
          <CamposMapeamento mapeamento={mapeamento} aoMudar={setMapeamento} />
        )}

        <ErroForm mensagem={erro} />
        <div>
          <Button type="submit" disabled={lendo}>
            <FileUpIcon aria-hidden />
            {lendo ? "Lendo extrato…" : "Ler extrato"}
          </Button>
        </div>
      </FieldGroup>
    </form>
  )
}

type PropsMapeamento = {
  mapeamento: MapeamentoCsv
  aoMudar: (mapeamento: MapeamentoCsv) => void
}

/** Colunas do CSV genérico. Na tela contam a partir de 1; na API, de 0. */
function CamposMapeamento({ mapeamento, aoMudar }: PropsMapeamento) {
  const creditoDebito = mapeamento.coluna_valor === null
  const id = useId()

  function coluna(campo: keyof MapeamentoCsv, rotulo: string) {
    const valor = mapeamento[campo] as number | null
    return (
      <Campo
        label={rotulo}
        type="number"
        min={1}
        max={100}
        inputMode="numeric"
        value={valor === null ? "" : valor + 1}
        onChange={(e) =>
          aoMudar({ ...mapeamento, [campo]: Math.max(0, Number(e.target.value || 1) - 1) })
        }
      />
    )
  }

  function escolha<T extends string>(
    rotulo: string,
    valor: T,
    opcoes: [T, string][],
    aoEscolher: (valor: T) => void
  ) {
    return (
      <Field>
        <FieldLabel htmlFor={`${id}-${rotulo}`}>{rotulo}</FieldLabel>
        <Select value={valor} onValueChange={(v) => aoEscolher(v as T)}>
          <SelectTrigger id={`${id}-${rotulo}`} className="w-full text-base data-[size=default]:h-10">
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper">
            {opcoes.map(([opcao, texto]) => (
              <SelectItem key={opcao} value={opcao}>
                {texto}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Field>
    )
  }

  return (
    <fieldset className="grid gap-5 border-t pt-5">
      <legend className="sr-only">Colunas do CSV</legend>
      <p className="text-sm text-muted-foreground">
        Diga onde está cada informação no arquivo. A primeira coluna é a 1.
      </p>
      <div className="grid gap-5 sm:grid-cols-3">
        {escolha(
          "Separador",
          mapeamento.separador,
          [
            [";", "Ponto e vírgula (;)"],
            [",", "Vírgula (,)"],
            ["\t", "Tabulação"],
          ],
          (separador) => aoMudar({ ...mapeamento, separador })
        )}
        {escolha(
          "Formato da data",
          mapeamento.formato_data,
          [
            ["dd/mm/aaaa", "31/12/2026"],
            ["dd-mm-aaaa", "31-12-2026"],
            ["aaaa-mm-dd", "2026-12-31"],
            ["mm/dd/aaaa", "12/31/2026"],
          ],
          (formato_data) => aoMudar({ ...mapeamento, formato_data })
        )}
        {escolha(
          "Casas decimais",
          mapeamento.separador_decimal,
          [
            [",", "1.234,56"],
            [".", "1,234.56"],
          ],
          (separador_decimal) => aoMudar({ ...mapeamento, separador_decimal })
        )}
      </div>
      <div className="grid gap-5 sm:grid-cols-3">
        <Campo
          label="Linhas a pular no início"
          type="number"
          min={0}
          max={50}
          value={mapeamento.pular_linhas}
          onChange={(e) =>
            aoMudar({ ...mapeamento, pular_linhas: Math.max(0, Number(e.target.value || 0)) })
          }
        />
        {coluna("coluna_data", "Coluna da data")}
        {coluna("coluna_descricao", "Coluna da descrição")}
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={mapeamento.tem_cabecalho}
          onChange={(e) => aoMudar({ ...mapeamento, tem_cabecalho: e.target.checked })}
        />
        A primeira linha (depois das puladas) é o cabeçalho
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={creditoDebito}
          onChange={(e) =>
            aoMudar(
              e.target.checked
                ? { ...mapeamento, coluna_valor: null, coluna_credito: 2, coluna_debito: 3 }
                : { ...mapeamento, coluna_valor: 2, coluna_credito: null, coluna_debito: null }
            )
          }
        />
        Entradas e saídas ficam em colunas separadas (crédito e débito)
      </label>
      <div className="grid gap-5 sm:grid-cols-3">
        {creditoDebito ? (
          <>
            {coluna("coluna_credito", "Coluna de crédito")}
            {coluna("coluna_debito", "Coluna de débito")}
          </>
        ) : (
          coluna("coluna_valor", "Coluna do valor")
        )}
      </div>
    </fieldset>
  )
}
