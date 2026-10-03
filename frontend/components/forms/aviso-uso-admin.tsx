import { InfoIcon } from "lucide-react"

/** Transparência exigida pela constituição 6.0.0: o administrador vê o uso, nunca o conteúdo. */
export function AvisoUsoAdmin() {
  return (
    <p className="flex gap-2 text-sm text-muted-foreground">
      <InfoIcon aria-hidden className="mt-0.5 size-4 shrink-0" />
      <span>
        O administrador vê quando você entra e quais recursos usa, mas nunca valores, descrições ou
        nomes do que você lança.
      </span>
    </p>
  )
}
