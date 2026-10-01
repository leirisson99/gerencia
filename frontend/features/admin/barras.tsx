export type ItemBarra = { chave: string; rotulo: string; quantidade: number }

/**
 * Lista de barras horizontais com quantidade e porcentagem de `base`. A barra tem a largura da
 * porcentagem mostrada, para o comprimento nunca exagerar a diferença.
 */
export function Barras({ itens, base, vazio }: { itens: ItemBarra[]; base: number; vazio: string }) {
  if (base === 0 || itens.every((i) => i.quantidade === 0)) {
    return <p className="py-10 text-center text-sm text-muted-foreground">{vazio}</p>
  }

  return (
    <ol className="flex flex-col gap-4">
      {itens.map((item) => {
        const porcentagem = Math.round((item.quantidade / base) * 100)
        return (
          <li key={item.chave}>
            <div className="mb-1.5 flex items-baseline justify-between gap-2 text-sm">
              <span>{item.rotulo}</span>
              <span className="valor text-muted-foreground">
                {item.quantidade} · {porcentagem}%
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted" aria-hidden>
              <div className="h-full rounded-full bg-foreground" style={{ width: `${porcentagem}%` }} />
            </div>
          </li>
        )
      })}
    </ol>
  )
}
