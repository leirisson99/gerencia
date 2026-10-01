// Service worker do Gerencia: só recebe o resumo diário dos lembretes e abre o app ao tocar.
// Sem cache offline. O payload vem do backend (app/services/envio_lembrete.py) e só tem
// contagens: { titulo, corpo, url }.

self.addEventListener("install", () => {
  self.skipWaiting()
})

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("push", (event) => {
  let dados = {}
  try {
    dados = event.data ? event.data.json() : {}
  } catch {
    // Payload inesperado: mostra um aviso genérico em vez de nada.
  }
  const titulo = dados.titulo || "Gerencia"
  event.waitUntil(
    self.registration.showNotification(titulo, {
      body: dados.corpo || "Você tem lembretes para hoje.",
      icon: "/icone-192.png",
      badge: "/icone-192.png",
      // Mesma tag: o resumo novo substitui o anterior em vez de empilhar.
      tag: "lembretes",
      data: { url: dados.url || "/lembretes" },
    })
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const url = new URL(event.notification.data?.url || "/lembretes", self.location.origin).href
  event.waitUntil(
    (async () => {
      const janelas = await self.clients.matchAll({ type: "window", includeUncontrolled: true })
      const doApp = janelas.find((janela) => new URL(janela.url).origin === self.location.origin)
      if (doApp) {
        await doApp.focus()
        return doApp.navigate(url)
      }
      return self.clients.openWindow(url)
    })()
  )
})
