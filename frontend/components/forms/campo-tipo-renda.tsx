"use client"

import { useId, type Ref } from "react"

import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { TipoRenda } from "@/lib/api/types"
import { TIPOS_RENDA } from "@/lib/tipo-renda"

type Props = {
  value: TipoRenda
  onChange: (valor: TipoRenda) => void
  onBlur?: () => void
  name?: string
  ref?: Ref<HTMLButtonElement>
  erro?: string
}

/** Escolha do tipo de renda, com a regra do ciclo de cada um na descrição. */
export function CampoTipoRenda({ value, onChange, onBlur, name, ref, erro }: Props) {
  const id = useId()
  const descricao = TIPOS_RENDA.find((t) => t.valor === value)?.descricao
  const descritoPor = [descricao && !erro && `${id}-descricao`, erro && `${id}-erro`]
    .filter(Boolean)
    .join(" ")

  return (
    <Field data-invalid={erro ? true : undefined}>
      <FieldLabel htmlFor={id}>Como você recebe</FieldLabel>
      <Select name={name} value={value} onValueChange={(v) => onChange(v as TipoRenda)}>
        <SelectTrigger
          id={id}
          ref={ref}
          onBlur={onBlur}
          aria-invalid={erro ? true : undefined}
          aria-describedby={descritoPor || undefined}
          className="w-full text-base data-[size=default]:h-10"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent position="popper">
          {TIPOS_RENDA.map((t) => (
            <SelectItem key={t.valor} value={t.valor}>
              {t.rotulo}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {descricao && !erro && <FieldDescription id={`${id}-descricao`}>{descricao}</FieldDescription>}
      {erro && <FieldError id={`${id}-erro`}>{erro}</FieldError>}
    </Field>
  )
}
