"use client"

import { useState } from "react"
import { EyeIcon, EyeOffIcon } from "lucide-react"

import { Input } from "@/components/ui/input"
import { Campo, type CampoProps } from "./campo"

/** Campo de senha com botão para mostrar ou ocultar o texto digitado. */
export function CampoSenha(props: Omit<CampoProps, "type" | "renderInput">) {
  const [visivel, setVisivel] = useState(false)

  return (
    <Campo
      {...props}
      renderInput={(inputProps) => (
        <div className="relative">
          <Input {...inputProps} type={visivel ? "text" : "password"} className="pr-11" />
          <button
            type="button"
            onClick={() => setVisivel((v) => !v)}
            aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
            aria-pressed={visivel}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            {visivel ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
          </button>
        </div>
      )}
    />
  )
}
