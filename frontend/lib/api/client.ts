import type { ErroOut } from "./types"

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly codigo: string,
    mensagem: string,
    readonly campos: Record<string, string> = {}
  ) {
    super(mensagem)
    this.name = "ApiError"
  }
}

type Metodo = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

type Opcoes = {
  metodo?: Metodo
  corpo?: unknown
  /** Base da API. No navegador é relativa (o Next reescreve para o backend). */
  base?: string
  headers?: HeadersInit
}

const ERRO_REDE = "Não foi possível falar com o servidor. Verifique a conexão e tente de novo."

export async function requisitar<T>(caminho: string, opcoes: Opcoes = {}): Promise<T> {
  const { metodo = "GET", corpo, base = "", headers } = opcoes
  let resposta: Response
  try {
    resposta = await fetch(`${base}/api/v1${caminho}`, {
      method: metodo,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(corpo !== undefined && { "Content-Type": "application/json" }),
        ...headers,
      },
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    })
  } catch {
    throw new ApiError(0, "rede", ERRO_REDE)
  }

  if (resposta.status === 204) return undefined as T
  const dados: unknown = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    const erro = (dados as ErroOut | null)?.erro
    throw new ApiError(
      resposta.status,
      erro?.codigo ?? `http_${resposta.status}`,
      erro?.mensagem ?? "Algo deu errado. Tente de novo.",
      erro?.campos ?? {}
    )
  }
  return dados as T
}
