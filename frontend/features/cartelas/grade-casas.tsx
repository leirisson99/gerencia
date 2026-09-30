"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { CheckIcon, Loader2Icon } from "lucide-react"
import { toast } from "sonner"
import { cn } from "cn"

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { depositar, desfazerDeposito } from "@/lib/api/cartelas"
import { ApiError } from "@/lib/api/client"
import type { Cartela, Casa } from "@/lib/api/types"
import { formatarCentavos, formatarCentavosCurto, formatarData } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"

function rotuloCasa(casa: Casa) {
  const nome = casa.is_ajuste ? "Casa de ajuste" : `Casa ${casa.ordem}`
  const estado = casa.depositado_em ? `depositada em ${formatarData(casa.depositado_em)}` : "livre"
  return `${nome}, ${formatarCentavos(casa.valor)}, ${estado}`
}

/**
 * Casas da cartela. Clicar numa livre deposita na hora (saída em "Poupança" com a data de hoje);
 * clicar numa depositada pede confirmação para desfazer.
 */
export function GradeCasas({ cartela }: { cartela: Cartela }) {
  const router = useRouter()
  const [ocupada, setOcupada] = useState<number | null>(null)
  const [atualizando, startTransition] = useTransition()
  const [desfazendo, setDesfazendo] = useState<Casa | null>(null)

  async function executar(casa: Casa, acao: typeof depositar, sucesso: string) {
    setOcupada(casa.id)
    try {
      await acao(cartela.id, casa.id)
      toast.success(sucesso)
    } catch (e) {
      // casa_depositada, casa_livre, salario_necessario, antes_do_primeiro_ciclo: a API explica.
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      // Mantém o indicador até os dados novos chegarem do servidor.
      startTransition(() => {
        router.refresh()
        setOcupada(null)
      })
    }
  }

  function aoClicar(casa: Casa) {
    if (casa.depositado_em) setDesfazendo(casa)
    else
      executar(
        casa,
        depositar,
        `${formatarCentavos(casa.valor)} guardados. A saída entrou em "Poupança" com a data de hoje.`
      )
  }

  const bloqueada = ocupada !== null || atualizando

  return (
    <>
      <ul className="grid grid-cols-[repeat(auto-fill,minmax(4.25rem,1fr))] gap-1.5 sm:grid-cols-[repeat(auto-fill,minmax(5rem,1fr))]">
        {cartela.casas.map((casa) => {
          const depositada = casa.depositado_em !== null
          return (
            <li key={casa.id}>
              <button
                type="button"
                onClick={() => aoClicar(casa)}
                disabled={bloqueada}
                aria-pressed={depositada}
                aria-label={rotuloCasa(casa)}
                title={rotuloCasa(casa)}
                className={cn(
                  "relative flex h-14 w-full items-center justify-center rounded-md border text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:cursor-wait sm:h-16",
                  depositada
                    ? "border-foreground bg-foreground text-background hover:bg-foreground/85"
                    : "border-foreground/15 hover:border-foreground/60",
                  casa.is_ajuste && !depositada && "border-dashed border-foreground/50"
                )}
              >
                {ocupada === casa.id ? (
                  <Loader2Icon className="size-4 animate-spin" aria-hidden />
                ) : (
                  <>
                    <span className="valor font-medium">{formatarCentavosCurto(casa.valor)}</span>
                    {depositada && (
                      <CheckIcon className="absolute top-1 right-1 size-3 opacity-70" aria-hidden />
                    )}
                    {casa.is_ajuste && (
                      <span className="absolute bottom-0.5 text-[10px] leading-none opacity-70">ajuste</span>
                    )}
                  </>
                )}
              </button>
            </li>
          )
        })}
      </ul>

      <AlertDialog open={desfazendo !== null} onOpenChange={(abrir) => !abrir && setDesfazendo(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Desfazer este depósito?</AlertDialogTitle>
            <AlertDialogDescription>
              {desfazendo && rotuloCasa(desfazendo)}. A casa volta a ficar livre e o lançamento em
              &ldquo;Poupança&rdquo; é removido do ciclo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <Button
              variant="destructive"
              onClick={() => {
                const casa = desfazendo
                setDesfazendo(null)
                if (casa) executar(casa, desfazerDeposito, "Depósito desfeito.")
              }}
            >
              Desfazer depósito
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
