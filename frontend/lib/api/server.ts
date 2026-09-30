import "server-only"

import { cookies } from "next/headers"

import { ApiError, requisitar } from "./client"
import type {
  Cartela,
  Categoria,
  Ciclo,
  Divida,
  Lancamento,
  Recorrencia,
  ResumoCiclo,
  SugestaoSalario,
  Usuario,
  UsuarioAdmin,
} from "./types"

const API_URL = process.env.API_URL ?? "http://localhost:8000"

/** GET na API a partir do servidor, repassando o cookie do navegador. */
async function buscar<T>(caminho: string): Promise<T> {
  const jar = await cookies()
  return requisitar<T>(caminho, { base: API_URL, headers: { cookie: jar.toString() } })
}

/**
 * Busca o usuário da sessão no servidor, repassando o cookie do navegador.
 * Devolve `null` quando não há sessão válida.
 */
export async function obterUsuarioSessao(): Promise<
  { usuario: Usuario; trocaObrigatoria: false } | { usuario: null; trocaObrigatoria: boolean }
> {
  const jar = await cookies()
  if (!jar.toString()) return { usuario: null, trocaObrigatoria: false }

  try {
    const usuario = await buscar<Usuario>("/me")
    return { usuario, trocaObrigatoria: false }
  } catch (erro) {
    if (erro instanceof ApiError && erro.codigo === "troca_senha_obrigatoria") {
      return { usuario: null, trocaObrigatoria: true }
    }
    if (erro instanceof ApiError && erro.status === 401) {
      return { usuario: null, trocaObrigatoria: false }
    }
    throw erro
  }
}

/**
 * Ciclo que contém a data, ou o atual (aberto) sem data.
 * Devolve `null` quando não há ciclo: nenhum salário lançado ou data anterior ao primeiro.
 */
export async function obterCiclo(data?: string): Promise<Ciclo | null> {
  try {
    return await buscar<Ciclo>(`/ciclos/${data ?? "atual"}`)
  } catch (erro) {
    if (erro instanceof ApiError && (erro.codigo === "sem_ciclo" || erro.status === 422)) {
      return null
    }
    throw erro
  }
}

/** Lançamentos do ciclo que começa em `inicio`, ordenados por data. */
export function listarLancamentosDoCiclo(inicio: string) {
  return buscar<Lancamento[]>(`/ciclos/${inicio}/lancamentos`)
}

/** Entradas, saídas, saldo e totais por categoria do ciclo que começa em `inicio`. */
export function obterResumo(inicio: string) {
  return buscar<ResumoCiclo>(`/ciclos/${inicio}/resumo`)
}

/** Só as ativas, a menos que peça as inativas (tela de categorias). */
export function listarCategorias({ incluirInativas = false } = {}) {
  return buscar<Categoria[]>(`/categorias${incluirInativas ? "?incluir_inativas=true" : ""}`)
}

export async function obterSugestaoSalario() {
  return (await buscar<SugestaoSalario>("/salarios/sugestao")).valor
}

/** Todas as recorrências, ativas e inativas, por dia e descrição. */
export function listarRecorrencias() {
  return buscar<Recorrencia[]>("/recorrencias")
}

export function listarDividas() {
  return buscar<Divida[]>("/dividas")
}

/** Devolve `null` se a dívida não existe ou é de outro usuário. */
export async function obterDivida(id: number): Promise<Divida | null> {
  try {
    return await buscar<Divida>(`/dividas/${id}`)
  } catch (erro) {
    if (erro instanceof ApiError && erro.status === 404) return null
    throw erro
  }
}

/** Contas de usuário comum em ordem alfabética; `busca` filtra nome ou e-mail. Só para o admin. */
export function listarUsuariosAdmin(busca?: string) {
  const query = busca ? `?busca=${encodeURIComponent(busca)}` : ""
  return buscar<UsuarioAdmin[]>(`/admin/usuarios${query}`)
}

export function listarCartelas() {
  return buscar<Cartela[]>("/cartelas")
}

/** Devolve `null` se a cartela não existe ou é de outro usuário. */
export async function obterCartela(id: number): Promise<Cartela | null> {
  try {
    return await buscar<Cartela>(`/cartelas/${id}`)
  } catch (erro) {
    if (erro instanceof ApiError && erro.status === 404) return null
    throw erro
  }
}

/**
 * Lançamentos com data entre `inicio` e `fim` (ISO, inclusive), juntando os ciclos que cobrem o
 * período. Antes do primeiro salário não há ciclo nem lançamento.
 */
export async function listarLancamentosDoPeriodo(inicio: string, fim: string): Promise<Lancamento[]> {
  let ciclo = (await obterCiclo(inicio)) ?? (await obterCiclo(fim))
  const lancamentos: Lancamento[] = []
  while (ciclo) {
    lancamentos.push(...(await listarLancamentosDoCiclo(ciclo.inicio)))
    ciclo = ciclo.proximo && ciclo.proximo <= fim ? await obterCiclo(ciclo.proximo) : null
  }
  return lancamentos.filter((l) => l.data >= inicio && l.data <= fim)
}
