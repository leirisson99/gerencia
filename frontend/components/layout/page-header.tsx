import type { ReactNode } from "react"

/** Título de uma página da área logada. */
export function PageHeader({ titulo, descricao }: { titulo: string; descricao?: ReactNode }) {
  return (
    <div className="mb-6 md:mb-10">
      <h1 className="text-title">{titulo}</h1>
      {descricao && <p className="mt-2 text-sm text-muted-foreground md:text-base">{descricao}</p>}
    </div>
  )
}
