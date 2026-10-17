"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { CampoCategoria } from "@/components/forms/campo-categoria"
import { ErroForm } from "@/components/forms/erro-form"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ApiError } from "@/lib/api/client"
import { aceitarConvite, recusarConvite } from "@/lib/api/contas-compartilhadas"
import type { Categoria, Convite } from "@/lib/api/types"
import { formatarDataDeInstante } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/** Convites pendentes no topo da lista: aceitar escolhe a categoria da sua parte. */
export function ListaConvites({
  convites,
  categorias,
}: {
  convites: Convite[]
  /** Só as ativas. */
  categorias: Categoria[]
}) {
  if (convites.length === 0) return null
  return (
    <section aria-labelledby="convites-titulo" className="mb-10">
      <h2 id="convites-titulo" className="mb-3 text-sm font-medium text-muted-foreground">
        Convites para você
      </h2>
      <ul className="divide-y rounded-lg border">
        {convites.map((c) => (
          <ItemConvite key={c.id} convite={c} categorias={categorias} />
        ))}
      </ul>
    </section>
  )
}

function ItemConvite({ convite, categorias }: { convite: Convite; categorias: Categoria[] }) {
  const router = useRouter()
  const [aceitando, setAceitando] = useState(false)
  const [recusando, setRecusando] = useState(false)

  async function recusar() {
    setRecusando(true)
    try {
      await recusarConvite(convite.id)
      toast.success("Convite recusado.")
      router.refresh()
    } catch (erro) {
      toast.error(erro instanceof ApiError ? erro.message : MENSAGEM_GENERICA)
    } finally {
      setRecusando(false)
    }
  }

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 p-4">
      <div className="min-w-0">
        <p className="font-medium">
          {convite.nome_do_dono} convidou você para dividir {convite.descricao_conta}
        </p>
        <p className="text-sm text-muted-foreground">
          Convite de {formatarDataDeInstante(convite.convidado_em)}
        </p>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" onClick={recusar} disabled={recusando} aria-busy={recusando}>
          Recusar
        </Button>
        <Button onClick={() => setAceitando(true)}>Aceitar</Button>
      </div>
      <DialogAceite
        aberto={aceitando}
        aoMudar={setAceitando}
        convite={convite}
        categorias={categorias}
      />
    </li>
  )
}

function DialogAceite({
  aberto,
  aoMudar,
  convite,
  categorias,
}: {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  convite: Convite
  categorias: Categoria[]
}) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Aceitar convite</DialogTitle>
          <DialogDescription>
            A sua parte de {convite.descricao_conta} vira um lançamento previsto no seu ciclo, na
            categoria que você escolher.
          </DialogDescription>
        </DialogHeader>
        {aberto && <FormAceite convite={convite} categorias={categorias} aoConcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormAceite({
  convite,
  categorias,
  aoConcluir,
}: {
  convite: Convite
  categorias: Categoria[]
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [categoria, setCategoria] = useState("")
  const [erroCampo, setErroCampo] = useState<string | undefined>()
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    setErro(null)
    setErroCampo(undefined)
    if (!categoria) return setErroCampo("Escolha uma categoria.")
    setEnviando(true)
    try {
      const conta = await aceitarConvite(convite.id, Number(categoria))
      toast.success("Convite aceito.")
      aoConcluir()
      router.push(`/contas-compartilhadas/${conta.id}`)
      router.refresh()
    } catch (e) {
      if (e instanceof ApiError && e.campos.categoria_id) setErroCampo(e.campos.categoria_id)
      else setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5">
        <CampoCategoria
          categorias={categorias}
          tipo="saida"
          semSalario
          value={categoria}
          onChange={setCategoria}
          erro={erroCampo}
        />
        <ErroForm mensagem={erro} />
        <div>
          <BotaoEnviar enviando={enviando}>Aceitar convite</BotaoEnviar>
        </div>
      </div>
    </form>
  )
}
