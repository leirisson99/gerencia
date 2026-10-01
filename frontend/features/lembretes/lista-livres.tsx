"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { cn } from "cn"
import { CheckIcon, PlusIcon, Undo2Icon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { editarLembreteLivre } from "@/lib/api/lembretes"
import type { LembreteLivre } from "@/lib/api/types"
import { formatarDiaMes } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { DialogLembreteLivre } from "./dialog-lembrete-livre"

/** Lembretes livres: clicar abre a edição; "Concluir" e "Desfazer" ficam na própria linha. */
export function ListaLivres({ livres }: { livres: LembreteLivre[] }) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  // Continua preenchido enquanto o dialog fecha, para o conteúdo não trocar na animação.
  const [editando, setEditando] = useState<LembreteLivre | undefined>()

  async function marcar(lembrete: LembreteLivre, concluido: boolean) {
    try {
      await editarLembreteLivre(lembrete.id, { concluido })
      toast.success(concluido ? "Lembrete concluído." : "Lembrete reaberto.")
      router.refresh()
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    }
  }

  if (livres.length === 0) return null

  return (
    <>
      <ul className="border-t">
        {livres.map((l) => (
          <li key={l.id} className="flex items-center gap-2 border-b">
            <button
              type="button"
              onClick={() => {
                setEditando(l)
                setAberto(true)
              }}
              className="grid min-w-0 flex-1 grid-cols-[3.5rem_1fr] items-baseline gap-x-3 px-1 py-4 text-left transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-2 focus-visible:outline-ring"
            >
              <span className="valor text-sm text-muted-foreground">{formatarDiaMes(l.data)}</span>
              <span
                className={cn(
                  "min-w-0 truncate",
                  l.concluido && "text-muted-foreground line-through decoration-muted-foreground/50"
                )}
              >
                {l.texto}
              </span>
            </button>
            <Button
              variant={l.concluido ? "ghost" : "outline"}
              size="sm"
              onClick={() => marcar(l, !l.concluido)}
              aria-label={`${l.concluido ? "Reabrir" : "Concluir"} ${l.texto}`}
            >
              {l.concluido ? <Undo2Icon aria-hidden /> : <CheckIcon aria-hidden />}
              {l.concluido ? "Desfazer" : "Concluir"}
            </Button>
          </li>
        ))}
      </ul>
      <DialogLembreteLivre aberto={aberto} aoMudar={setAberto} lembrete={editando} />
    </>
  )
}

/** Botão "Novo lembrete" com o dialog de criação. */
export function NovoLembrete() {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      <Button onClick={() => setAberto(true)}>
        <PlusIcon aria-hidden />
        Novo lembrete
      </Button>
      <DialogLembreteLivre aberto={aberto} aoMudar={setAberto} />
    </>
  )
}
