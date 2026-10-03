"use client"

import { useTransition } from "react"
import { useRouter } from "next/navigation"
import { cn } from "cn"

import { useCarteira } from "@/features/carteira/contexto"
import type { Carteira } from "@/lib/api/types"
import { gravarCarteira } from "@/lib/carteira-cookie"

const OPCOES: { valor: Carteira; rotulo: string; titulo: string }[] = [
  { valor: "pf", rotulo: "PF", titulo: "Pessoa física: o seu dinheiro" },
  { valor: "pj", rotulo: "PJ", titulo: "Pessoa jurídica: o dinheiro da empresa" },
]

/** Troca entre a carteira pessoal e a da empresa. Só aparece para quem ligou a PJ. */
export function SeletorCarteira({ className }: { className?: string }) {
  const { carteira, temPj } = useCarteira()
  const router = useRouter()
  const [trocando, iniciar] = useTransition()
  if (!temPj) return null

  function escolher(valor: Carteira) {
    if (valor === carteira) return
    gravarCarteira(valor)
    iniciar(() => router.refresh())
  }

  return (
    <div
      role="group"
      aria-label="Carteira"
      className={cn(
        "inline-flex h-9 shrink-0 items-center rounded-full border bg-background p-0.5",
        trocando && "opacity-60",
        className
      )}
    >
      {OPCOES.map((opcao) => {
        const ativa = opcao.valor === carteira
        return (
          <button
            key={opcao.valor}
            type="button"
            title={opcao.titulo}
            aria-pressed={ativa}
            disabled={trocando}
            onClick={() => escolher(opcao.valor)}
            className={cn(
              "h-full rounded-full px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
              ativa ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            )}
          >
            {opcao.rotulo}
          </button>
        )
      })}
    </div>
  )
}
