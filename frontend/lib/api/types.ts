// Espelham os schemas do backend em app/schemas/usuario.py e app/schemas/erro.py.

export type Usuario = {
  id: number
  nome: string
  email: string
  telefone: string
  cargo: string
  /** ISO `YYYY-MM-DD` */
  data_nascimento: string | null
  troca_senha_obrigatoria: boolean
  /** Só o do próprio usuário. O administrador tem área própria e não vê dados financeiros. */
  papel: "usuario" | "admin"
  criado_em: string
}

export type CadastroIn = {
  nome: string
  email: string
  telefone: string
  cargo: string
  senha: string
  data_nascimento?: string | null
}

export type LoginIn = {
  email: string
  senha: string
}

export type PerfilIn = Partial<Pick<Usuario, "nome" | "telefone" | "cargo" | "data_nascimento">>

export type TrocaSenhaIn = {
  senha_atual: string
  nova_senha: string
}

export type ErroOut = {
  erro: {
    codigo: string
    mensagem: string
    campos: Record<string, string> | null
  }
}

// Espelham app/schemas/categoria.py, lancamento.py e ciclo.py. Valores sempre em centavos inteiros.

export type TipoLancamento = "entrada" | "saida"
export type StatusLancamento = "previsto" | "realizado"

export type Categoria = {
  id: number
  nome: string
  tipo: TipoLancamento
  /** "Salário" é a única categoria de sistema e a única que abre ciclo. */
  sistema: boolean
  ativa: boolean
}

export type CategoriaIn = { nome: string; tipo: TipoLancamento }

/** Renomear e/ou ativar/desativar. O tipo não muda. */
export type CategoriaPatch = { nome?: string; ativa?: boolean }

export type Lancamento = {
  id: number
  /** Centavos */
  valor: number
  tipo: TipoLancamento
  categoria_id: number
  /** ISO `YYYY-MM-DD` */
  data: string
  descricao: string | null
  status: StatusLancamento
  conta_no_saldo: boolean
  abre_ciclo: boolean
  /** Previsto gerado por uma recorrência. */
  recorrencia_id: number | null
  /** Parcela de dívida: categoria fixa e sem exclusão avulsa. */
  divida_id: number | null
  parcela_num: number | null
  criado_em: string
}

/** Só valor, categoria e data são obrigatórios; o tipo vem da categoria. */
export type LancamentoIn = {
  valor: number
  categoria_id: number
  data: string
  descricao?: string | null
  status?: StatusLancamento
}

export type LancamentoPatch = Partial<LancamentoIn>

export type Ciclo = {
  /** ISO `YYYY-MM-DD` */
  inicio: string
  /** `null` no ciclo aberto */
  fim: string | null
  aberto: boolean
  /** Início do ciclo anterior, se houver */
  anterior: string | null
  /** Início do próximo ciclo, se houver */
  proximo: string | null
}

export type SugestaoSalario = {
  valor: number | null
}

// Espelham app/schemas/resumo.py, recorrencia.py, divida.py e admin.py.

export type TotalCategoria = {
  categoria_id: number
  nome: string
  /** Centavos */
  total: number
}

/** Só lançamentos realizados que contam no saldo. Listas por total decrescente. */
export type ResumoCiclo = {
  ciclo: Ciclo
  entradas: number
  saidas: number
  saldo: number
  saidas_por_categoria: TotalCategoria[]
  entradas_por_categoria: TotalCategoria[]
}

export type Recorrencia = {
  id: number
  descricao: string
  /** Centavos */
  valor: number
  tipo: TipoLancamento
  categoria_id: number
  /** Dia do mês, 1 a 31 */
  dia: number
  ativa: boolean
}

/** O tipo vem da categoria; "Salário" não é aceita. */
export type RecorrenciaIn = Pick<Recorrencia, "descricao" | "valor" | "categoria_id" | "dia">

/** Vale para os próximos ciclos. */
export type RecorrenciaPatch = Partial<RecorrenciaIn & Pick<Recorrencia, "ativa">>

export type Direcao = "devo" | "me_devem"
export type FormaPagamento = "pix" | "boleto" | "cartao" | "dinheiro"

export type DividaIn = {
  descricao: string
  pessoa: string
  direcao: Direcao
  /** Centavos */
  valor_total: number
  parcelas: number
  forma_pagamento: FormaPagamento
  dia_vencimento: number
  /** ISO `YYYY-MM-DD` */
  data_inicio: string
  categoria_id: number
}

export type Divida = DividaIn & {
  id: number
  parcelas_pagas: number
  valor_pago: number
  valor_restante: number
  quitada: boolean
  /** Parcelas, geradas como lançamentos previstos. */
  lancamentos: Lancamento[]
}

export type UsuarioAdmin = {
  id: number
  nome: string
  email: string
  criado_em: string
}

export type SenhaTemporaria = { senha_temporaria: string }
