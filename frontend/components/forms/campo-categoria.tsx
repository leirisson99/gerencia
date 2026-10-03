"use client"

import { useId, type ReactNode, type Ref } from "react"

import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Categoria, TipoLancamento } from "@/lib/api/types"
import { eDeRetirada, eSalario } from "@/lib/categorias"

type Props = {
  categorias: Categoria[]
  /** Id da categoria como texto; vazio quando nenhuma foi escolhida. */
  value: string
  onChange: (valor: string) => void
  onBlur?: () => void
  name?: string
  ref?: Ref<HTMLButtonElement>
  label?: string
  erro?: string
  descricao?: ReactNode
  disabled?: boolean
  /** Mostra só entradas ou só saídas. */
  tipo?: TipoLancamento
  /** Esconde "Salário" (ex.: recorrências, que não aceitam a categoria que abre ciclo). */
  semSalario?: boolean
}

const GRUPOS: { tipo: TipoLancamento; rotulo: string }[] = [
  { tipo: "entrada", rotulo: "Entradas" },
  { tipo: "saida", rotulo: "Saídas" },
]

/** Escolha de categoria agrupada em entradas e saídas, com rótulo, descrição e erro ligados. */
export function CampoCategoria({
  categorias,
  value,
  onChange,
  onBlur,
  name,
  ref,
  label = "Categoria",
  erro,
  descricao,
  disabled,
  tipo,
  semSalario,
}: Props) {
  const id = useId()
  // As categorias da retirada (PJ) só são usadas pela própria retirada.
  const visiveis = categorias.filter(
    (c) => (!tipo || c.tipo === tipo) && !(semSalario && eSalario(c)) && !eDeRetirada(c)
  )
  const descritoPor = [descricao && !erro && `${id}-descricao`, erro && `${id}-erro`]
    .filter(Boolean)
    .join(" ")

  return (
    <Field data-invalid={erro ? true : undefined} data-disabled={disabled || undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Select name={name} value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          id={id}
          ref={ref}
          onBlur={onBlur}
          aria-invalid={erro ? true : undefined}
          aria-describedby={descritoPor || undefined}
          className="w-full text-base data-[size=default]:h-10"
        >
          <SelectValue placeholder="Escolha uma categoria" />
        </SelectTrigger>
        <SelectContent position="popper">
          {GRUPOS.map((grupo) => {
            const itens = visiveis.filter((c) => c.tipo === grupo.tipo)
            if (itens.length === 0) return null
            return (
              <SelectGroup key={grupo.tipo}>
                <SelectLabel>{grupo.rotulo}</SelectLabel>
                {itens.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.nome}
                  </SelectItem>
                ))}
              </SelectGroup>
            )
          })}
        </SelectContent>
      </Select>
      {descricao && !erro && <FieldDescription id={`${id}-descricao`}>{descricao}</FieldDescription>}
      {erro && <FieldError id={`${id}-erro`}>{erro}</FieldError>}
    </Field>
  )
}
