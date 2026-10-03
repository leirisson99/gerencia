"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { ErroForm } from "@/components/forms/erro-form"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { editarMe } from "@/lib/api/auth"
import { ApiError } from "@/lib/api/client"
import type { Usuario } from "@/lib/api/types"
import { gravarCarteira } from "@/lib/carteira-cookie"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { podeTerPj } from "@/lib/tipo-renda"

/** "Tenho CNPJ": liga a carteira PJ, que separa o dinheiro da empresa do seu. */
export function SecaoCarteiraPj({ usuario }: { usuario: Usuario }) {
  const router = useRouter()
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const disponivel = podeTerPj(usuario.tipo_renda)

  async function alternar(ligar: boolean) {
    setErro(null)
    setSalvando(true)
    try {
      await editarMe({ tem_pj: ligar })
      if (!ligar) gravarCarteira("pf")
      toast.success(ligar ? "Carteira PJ ligada. Use o seletor PF | PJ no topo." : "Carteira PJ desligada.")
      router.refresh()
    } catch (e) {
      // `pj_com_dados` e `categoria_conflitante` já dizem o que fazer antes.
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setSalvando(false)
    }
  }

  if (!disponivel && !usuario.tem_pj) {
    return (
      <p className="text-sm text-muted-foreground">
        A carteira PJ é para quem presta serviço. Para usar, mude o tipo de renda acima para
        &ldquo;Presto serviço&rdquo; ou &ldquo;CLT e presto serviço&rdquo;.
      </p>
    )
  }

  return (
    <div className="grid gap-3">
      <div className="flex items-start gap-3">
        <Checkbox
          id="tem-pj"
          checked={usuario.tem_pj}
          disabled={salvando}
          onCheckedChange={(valor) => alternar(valor === true)}
          className="mt-0.5"
        />
        <div className="grid gap-1">
          <Label htmlFor="tem-pj">Tenho CNPJ (carteira PJ)</Label>
          <p className="text-sm text-muted-foreground">
            Separa o dinheiro da empresa do seu. A PJ conta pelo mês do calendário e não precisa de
            salário; para levar dinheiro à PF, use &ldquo;Retirar para PF&rdquo;.
          </p>
        </div>
      </div>
      <ErroForm mensagem={erro} />
    </div>
  )
}
