"use client"

import { useId, type ComponentProps, type ReactNode } from "react"

import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"

type InputProps = ComponentProps<typeof Input>

export type CampoProps = InputProps & {
  label: string
  erro?: string
  descricao?: ReactNode
  /** Substitui o `<Input>` padrão (ex.: campo de senha). Recebe id e atributos de acessibilidade. */
  renderInput?: (props: InputProps) => ReactNode
}

/** Rótulo + input + descrição + erro, com ids ligados para leitores de tela. */
export function Campo({ label, erro, descricao, renderInput, id, ...inputProps }: CampoProps) {
  const gerado = useId()
  const campoId = id ?? gerado
  const descricaoId = `${campoId}-descricao`
  const erroId = `${campoId}-erro`
  const descritoPor = [descricao && !erro && descricaoId, erro && erroId].filter(Boolean).join(" ")

  const props: InputProps = {
    ...inputProps,
    id: campoId,
    "aria-invalid": erro ? true : undefined,
    "aria-describedby": descritoPor || undefined,
  }

  return (
    <Field data-invalid={erro ? true : undefined}>
      <FieldLabel htmlFor={campoId}>{label}</FieldLabel>
      {renderInput ? renderInput(props) : <Input {...props} />}
      {descricao && !erro && <FieldDescription id={descricaoId}>{descricao}</FieldDescription>}
      {erro && <FieldError id={erroId}>{erro}</FieldError>}
    </Field>
  )
}
