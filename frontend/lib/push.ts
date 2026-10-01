import { ApiError } from "@/lib/api/client"
import { inscreverAparelho, obterChavePush, removerAparelho } from "@/lib/api/push"

// Notificações push no navegador (só cliente). O service worker fica em public/sw.js.

export type EstadoPush =
  | "sem_suporte"
  | "iphone_sem_instalar"
  | "bloqueado"
  | "inativo"
  | "ativo"

function ehIOS() {
  // iPadOS se apresenta como Mac; o toque denuncia.
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  )
}

function instalado() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function temSuporte() {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window
}

async function inscricaoAtual(): Promise<PushSubscription | null> {
  if (!temSuporte()) return null
  const registro = await navigator.serviceWorker.getRegistration("/")
  return (await registro?.pushManager.getSubscription()) ?? null
}

/** Chave base64url → bytes, no formato que o `pushManager.subscribe` espera. */
function chaveEmBytes(base64url: string) {
  const base64 = (base64url + "=".repeat((4 - (base64url.length % 4)) % 4))
    .replace(/-/g, "+")
    .replace(/_/g, "/")
  const binario = window.atob(base64)
  const bytes = new Uint8Array(new ArrayBuffer(binario.length))
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i)
  return bytes
}

export async function estadoPush(): Promise<EstadoPush> {
  // No iPhone o PushManager só existe com o app instalado na tela inicial (iOS 16.4+).
  if (ehIOS() && !instalado()) return "iphone_sem_instalar"
  if (!temSuporte()) return "sem_suporte"
  if (Notification.permission === "denied") return "bloqueado"
  return (await inscricaoAtual()) ? "ativo" : "inativo"
}

/**
 * Pede a permissão e inscreve este aparelho. Chame direto do clique: o Safari só mostra o
 * pedido de permissão se ele vier antes de qualquer espera de rede.
 */
export async function ativarPush(): Promise<"ativo" | "bloqueado"> {
  const permissao = await Notification.requestPermission()
  if (permissao !== "granted") return "bloqueado"

  const chave = await obterChavePush()
  await navigator.serviceWorker.register("/sw.js", { scope: "/", updateViaCache: "none" })
  const registro = await navigator.serviceWorker.ready
  // Uma inscrição antiga pode ter sido feita com outra chave do servidor.
  await (await registro.pushManager.getSubscription())?.unsubscribe()
  const inscricao = await registro.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: chaveEmBytes(chave),
  })
  await inscreverAparelho(inscricao.toJSON())
  return "ativo"
}

/** Desativa este aparelho na conta e no navegador. Sem inscrição, não faz nada. */
export async function desativarPush() {
  const inscricao = await inscricaoAtual()
  if (!inscricao) return
  try {
    await removerAparelho(inscricao.endpoint)
  } catch (erro) {
    // 404: o aparelho já não estava nesta conta; segue limpando o navegador.
    if (!(erro instanceof ApiError && erro.status === 404)) throw erro
  }
  await inscricao.unsubscribe()
}

/** Reenvia a inscrição local, se houver: mantém o aparelho ligado a esta conta. */
export async function sincronizarPush() {
  const inscricao = await inscricaoAtual()
  if (inscricao && Notification.permission === "granted") {
    await inscreverAparelho(inscricao.toJSON())
  }
}
