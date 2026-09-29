"use client"

import type { ComponentProps } from "react"

import { Input } from "@/components/ui/input"
import { centavosDeTexto, formatarCentavosCampo } from "@/lib/format"
import { Campo, type CampoProps } from "./campo"

type Props = Omit<CampoProps, "value" | "onChange" | "type" | "renderInput"> & {
  /** Centavos inteiros. */
  value: number
  onChange: (centavos: number) => void
}

/** Campo de dinheiro em reais. Guarda e devolve centavos inteiros; nunca float. */
export function CampoValor({ value, onChange, ...props }: Props) {
  return (
    <Campo
      {...props}
      inputMode="numeric"
      autoComplete="off"
      value={formatarCentavosCampo(value)}
      onChange={(e) => onChange(centavosDeTexto(e.target.value))}
      renderInput={(inputProps: ComponentProps<typeof Input>) => (
        <div className="relative">
          <span
            className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground"
            aria-hidden
          >
            R$
          </span>
          <Input {...inputProps} className="valor pl-10 text-right" />
        </div>
      )}
    />
  )
}
