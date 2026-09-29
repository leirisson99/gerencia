"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { LockIcon, PencilIcon, PlusIcon } from "lucide-react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { editarCategoria } from "@/lib/api/categorias"
import { ApiError } from "@/lib/api/client"
import type { Categoria, TipoLancamento } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { DialogCategoria } from "./dialog-categoria"

const COLUNAS: { tipo: TipoLancamento; titulo: string }[] = [
  { tipo: "entrada", titulo: "Entradas" },
  { tipo: "saida", titulo: "Saídas" },
]

type EstadoDialog = { aberto: boolean; categoria?: Categoria; tipo?: TipoLancamento }

/** Categorias em duas colunas (entradas e saídas); as inativas ficam por último, com reativar. */
export function ListaCategorias({ categorias }: { categorias: Categoria[] }) {
  const router = useRouter()
  const [dialog, setDialog] = useState<EstadoDialog>({ aberto: false })
  const [desativando, setDesativando] = useState<Categoria | null>(null)

  async function mudarAtiva(categoria: Categoria, ativa: boolean) {
    try {
      await editarCategoria(categoria.id, { ativa })
      toast.success(`"${categoria.nome}" ${ativa ? "reativada" : "desativada"}.`)
      router.refresh()
    } catch (e) {
      // `categoria_do_sistema` já explica que categorias do sistema não podem ser desativadas.
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    }
  }

  return (
    <>
      <div className="grid gap-10 lg:grid-cols-2">
        {COLUNAS.map(({ tipo, titulo }) => {
          const ativas = categorias.filter((c) => c.tipo === tipo && c.ativa)
          const inativas = categorias.filter((c) => c.tipo === tipo && !c.ativa)
          return (
            <section key={tipo} aria-labelledby={`categorias-${tipo}`}>
              <div className="mb-3 flex items-center justify-between gap-2">
                <h2 id={`categorias-${tipo}`} className="text-sm font-medium text-muted-foreground">
                  {titulo}
                </h2>
                <Button variant="ghost" size="sm" onClick={() => setDialog({ aberto: true, tipo })}>
                  <PlusIcon aria-hidden />
                  Nova
                </Button>
              </div>
              <ul className="border-t">
                {ativas.map((c) => (
                  <li key={c.id} className="flex min-h-14 items-center gap-2 border-b py-2">
                    <span className="min-w-0 flex-1">
                      <span className="block truncate">{c.nome}</span>
                      {c.limite !== null && (
                        <span className="valor block text-sm text-muted-foreground">
                          limite {formatarCentavos(c.limite)} por ciclo
                        </span>
                      )}
                    </span>
                    {c.sistema && (
                      <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <LockIcon className="size-3.5" aria-hidden />
                        Do sistema
                      </span>
                    )}
                    {/* Do sistema só edita o limite, e só quando é de saída. */}
                    {(!c.sistema || c.tipo === "saida") && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDialog({ aberto: true, categoria: c })}
                        aria-label={`Editar ${c.nome}`}
                      >
                        <PencilIcon aria-hidden />
                        <span className="hidden sm:inline">Editar</span>
                      </Button>
                    )}
                    {!c.sistema && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDesativando(c)}
                        aria-label={`Desativar ${c.nome}`}
                      >
                        Desativar
                      </Button>
                    )}
                  </li>
                ))}
              </ul>

              {inativas.length > 0 && (
                <details className="mt-6">
                  <summary className="cursor-pointer text-sm text-muted-foreground select-none">
                    {inativas.length} {inativas.length === 1 ? "inativa" : "inativas"}
                  </summary>
                  <ul className="mt-2 border-t">
                    {inativas.map((c) => (
                      <li key={c.id} className="flex min-h-14 items-center gap-2 border-b py-2">
                        <span className="min-w-0 flex-1 truncate text-muted-foreground">{c.nome}</span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => mudarAtiva(c, true)}
                          aria-label={`Reativar ${c.nome}`}
                        >
                          Reativar
                        </Button>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </section>
          )
        })}
      </div>

      <DialogCategoria
        aberto={dialog.aberto}
        aoMudar={(aberto) => setDialog((d) => ({ ...d, aberto }))}
        categoria={dialog.categoria}
        tipoInicial={dialog.tipo}
      />

      <AlertDialog open={desativando !== null} onOpenChange={(abrir) => !abrir && setDesativando(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Desativar &ldquo;{desativando?.nome}&rdquo;?</AlertDialogTitle>
            <AlertDialogDescription>
              Ela some das opções de novos lançamentos. Os lançamentos já feitos continuam com ela, e
              você pode reativá-la quando quiser.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={() => desativando && mudarAtiva(desativando, false)}>
              Desativar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
