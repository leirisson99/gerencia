import { OctagonAlertIcon } from "lucide-react"

/** Mensagem geral de um formulário, anunciada ao aparecer. */
export function ErroForm({ mensagem }: { mensagem?: string | null }) {
  if (!mensagem) return null
  return (
    <p role="alert" className="flex items-start gap-2 text-sm text-destructive">
      <OctagonAlertIcon className="mt-0.5 size-4 shrink-0" aria-hidden />
      {mensagem}
    </p>
  )
}
