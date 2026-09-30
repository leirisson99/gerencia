import Image from "next/image"
import Link from "next/link"

import { cn } from "@/lib/utils"

/** Símbolo do produto (o "G" com barras e seta de crescimento), sem o nome. */
export function Marca({ className }: { className?: string }) {
  return (
    <Image
      src="/marca.png"
      alt=""
      width={256}
      height={256}
      priority
      className={cn("size-[1.4em] shrink-0", className)}
    />
  )
}

/** Marca do produto: símbolo + nome. */
export function Logo({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link
      href={href}
      className={cn("inline-flex items-center gap-[0.4em] font-semibold tracking-tight", className)}
    >
      <Marca />
      Gerencia
    </Link>
  )
}
