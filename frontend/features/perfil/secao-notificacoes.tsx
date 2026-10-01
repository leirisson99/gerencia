"use client"

import { useEffect, useState } from "react"
import { BellIcon, BellOffIcon, Loader2Icon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { obterChavePush } from "@/lib/api/push"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import {
  ativarPush,
  desativarPush,
  estadoPush,
  sincronizarPush,
  type EstadoPush,
} from "@/lib/push"

type Estado = EstadoPush | "carregando" | "indisponivel"

const TEXTOS: Record<Exclude<Estado, "carregando">, string> = {
  ativo:
    "Ativadas neste aparelho. Todo dia, por volta das 8h, você recebe um resumo do que vence nos próximos 3 dias, só com contagens, sem valores.",
  inativo:
    "Receba às 8h um resumo do que vence nos próximos 3 dias. A notificação só traz contagens; os detalhes ficam em Lembretes.",
  bloqueado:
    "As notificações estão bloqueadas para este site. Libere nas configurações do navegador (no cadeado ao lado do endereço) e volte aqui.",
  iphone_sem_instalar:
    "No iPhone, as notificações só funcionam com o app instalado: toque em Compartilhar, depois em \"Adicionar à Tela de Início\", abra o Gerencia por lá e ative aqui.",
  sem_suporte:
    "Este navegador não recebe notificações. Use o Chrome, o Edge, o Firefox ou o Safari atualizados.",
  indisponivel: "As notificações não estão disponíveis no momento.",
}

/** Ativa ou desativa o resumo diário por push neste aparelho. */
export function SecaoNotificacoes() {
  const [estado, setEstado] = useState<Estado>("carregando")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let ativo = true
    async function carregar() {
      let atual: Estado = await estadoPush()
      if (atual === "ativo") {
        // Mantém o aparelho ligado a esta conta (outra pessoa pode ter ativado nele antes).
        await sincronizarPush().catch(() => {})
      } else if (atual === "inativo") {
        try {
          await obterChavePush()
        } catch (erro) {
          if (erro instanceof ApiError && erro.codigo === "push_indisponivel") {
            atual = "indisponivel"
          }
        }
      }
      if (ativo) setEstado(atual)
    }
    carregar()
    return () => {
      ativo = false
    }
  }, [])

  async function ativar() {
    setEnviando(true)
    try {
      const resultado = await ativarPush()
      setEstado(resultado)
      if (resultado === "ativo") toast.success("Notificações ativadas neste aparelho.")
    } catch (erro) {
      if (erro instanceof ApiError && erro.codigo === "push_indisponivel") setEstado("indisponivel")
      toast.error(erro instanceof ApiError ? erro.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  async function desativar() {
    setEnviando(true)
    try {
      await desativarPush()
      setEstado("inativo")
      toast.success("Notificações desativadas neste aparelho.")
    } catch (erro) {
      toast.error(erro instanceof ApiError ? erro.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  if (estado === "carregando") {
    return <p className="text-muted-foreground">Verificando este aparelho…</p>
  }

  return (
    <div className="grid gap-4">
      <p className="text-muted-foreground" aria-live="polite">
        {TEXTOS[estado]}
      </p>
      {estado === "inativo" && (
        <div>
          <Button onClick={ativar} disabled={enviando} aria-busy={enviando}>
            {enviando ? <Loader2Icon className="animate-spin" aria-hidden /> : <BellIcon aria-hidden />}
            Ativar notificações
          </Button>
        </div>
      )}
      {estado === "ativo" && (
        <div>
          <Button variant="outline" onClick={desativar} disabled={enviando} aria-busy={enviando}>
            {enviando ? <Loader2Icon className="animate-spin" aria-hidden /> : <BellOffIcon aria-hidden />}
            Desativar neste aparelho
          </Button>
        </div>
      )}
    </div>
  )
}
