import Link from "next/link"

import { cn } from "@/lib/utils"

/** Marca do produto. O traço vermelho no fim é o dinheiro que sai: o assunto do sistema. */
export function Logo({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link
      href={href}
      className={cn("inline-flex items-baseline font-semibold tracking-tight", className)}
    >
      gerencia
      <span aria-hidden className="ml-[0.08em] inline-block h-[0.12em] w-[0.45em] bg-saida" />
    </Link>
  )
}
