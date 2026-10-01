// Espelham os schemas do backend em app/schemas/usuario.py e app/schemas/erro.py.

/** Define a regra do ciclo (salário ou mês do calendário) e o acesso a Serviços. */
export type TipoRenda = "clt" | "prestador" | "clt_prestador"

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
  tipo_renda: TipoRenda
  criado_em: string
}

export type CadastroIn = {
  nome: string
  email: string
  telefone: string
  cargo: string
  senha: string
  data_nascimento?: string | null
  /** A API usa `clt` quando ausente. */
  tipo_renda?: TipoRenda
}

export type LoginIn = {
  email: string
  senha: string
}

export type PerfilIn = Partial<Pick<Usuario, "nome" | "telefone" | "cargo" | "data_nascimento" | "tipo_renda">>

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
  /** Gasto máximo por ciclo em centavos; só em saída. `null` sem limite. */
  limite: number | null
}

export type CategoriaIn = { nome: string; tipo: TipoLancamento; limite?: number | null }

/** Renomear, ativar/desativar e definir o limite. `limite: null` remove. O tipo não muda. */
export type CategoriaPatch = { nome?: string; ativa?: boolean; limite?: number | null }

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
  /** Depósito de cartela: só data e descrição mudam; desmarcar a casa remove o lançamento. */
  cartela_id: number | null
  /** Veio de extrato importado. */
  importado: boolean
  /** Entrada de um serviço: valor, status, categoria e data mudam só pelo serviço. */
  servico_id: number | null
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

export type SituacaoLimite = "ok" | "atencao" | "estourado"

export type TotalCategoria = {
  categoria_id: number
  nome: string
  /** Centavos */
  total: number
  /** Só em saídas com limite. */
  limite: number | null
  situacao: SituacaoLimite | null
}

/** Vem só na resposta de criar ou editar lançamento, quando a categoria piora de situação. */
export type AvisoLimite = {
  categoria_id: number
  nome: string
  usado: number
  limite: number
  situacao: SituacaoLimite
}

export type LancamentoComAviso = Lancamento & { aviso_limite: AvisoLimite | null }

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
  ativo: boolean
}

export type SenhaTemporaria = { senha_temporaria: string }

export type SituacaoConta = "ativos" | "desativados"

/** Espelha app/schemas/admin.py: só contagens globais, nunca valores nem usuários. */
export type Funcionalidade = "recorrencias" | "dividas" | "cartelas" | "servicos" | "importacao"

export type ResumoAdmin = {
  contas: { total: number; ativas: number; desativadas: number }
  lancamentos: {
    total: number
    realizados: number
    previstos: number
    /** Vieram de extrato de conta. */
    importados: number
    manuais: number
  }
  /** Últimos 12 meses, do mais antigo ao atual; `mes` em `AAAA-MM`. Só realizados. */
  por_mes: { mes: string; entradas: number; saidas: number }[]
  /** As quatro formas, da mais usada à menos. */
  dividas_por_forma: { forma: FormaPagamento; quantidade: number }[]
  /** Mesma janela de `por_mes`. */
  cadastros_por_mes: { mes: string; quantidade: number }[]
  /** Contas com acesso nos últimos 7/30 dias e com pelo menos um lançamento. */
  engajamento: { ativas_7_dias: number; ativas_30_dias: number; com_lancamento: number }
  /** Contas distintas que usam cada funcionalidade, em ordem fixa. */
  uso_funcionalidades: { funcionalidade: Funcionalidade; contas: number }[]
  por_tipo_renda: Record<TipoRenda, number>
}

// Espelham app/schemas/cartela.py.

export type Casa = {
  id: number
  ordem: number
  /** Centavos */
  valor: number
  /** Casa que fecha a meta com o resto. */
  is_ajuste: boolean
  /** ISO `YYYY-MM-DD`; `null` enquanto a casa está livre. */
  depositado_em: string | null
  lancamento_id: number | null
}

export type Cartela = {
  id: number
  nome: string
  meta: number
  valor_base: number
  guardado: number
  falta: number
  /** Inteiro, calculado pela API. */
  percentual: number
  maior_casa_livre: number | null
  casas: Casa[]
}

/** `valor_base` é opcional; a API usa R$ 1,00. */
export type CartelaIn = { nome: string; meta: number; valor_base?: number }

// Espelham app/schemas/importacao.py. Valores em centavos inteiros e sempre positivos; o sinal
// está em `tipo`.

export type FormatoExtrato = "ofx" | "csv" | "pdf" | "csv_generico"

export type Banco = {
  codigo: string
  nome: string
  formatos: FormatoExtrato[]
}

/** Colunas a partir de 0. Use `coluna_valor` ou o par `coluna_credito` e `coluna_debito`. */
export type MapeamentoCsv = {
  separador: ";" | "," | "	"
  pular_linhas: number
  tem_cabecalho: boolean
  coluna_data: number
  formato_data: "dd/mm/aaaa" | "dd-mm-aaaa" | "aaaa-mm-dd" | "mm/dd/aaaa"
  coluna_descricao: number
  coluna_valor: number | null
  coluna_credito: number | null
  coluna_debito: number | null
  separador_decimal: "," | "."
}

export type PreviaIn = {
  banco: string
  formato: FormatoExtrato
  arquivo_base64: string
  mapeamento: MapeamentoCsv | null
}

export type SituacaoLinha =
  | "nova"
  | "ja_importada"
  | "possivel_duplicada"
  | "antes_do_primeiro_ciclo"
  | "invalida"

export type LinhaPrevia = {
  id_externo: string
  /** ISO `YYYY-MM-DD` */
  data: string
  valor: number
  tipo: TipoLancamento
  descricao: string | null
  categoria_sugerida_id: number | null
  situacao: SituacaoLinha
}

export type Previa = {
  linhas: LinhaPrevia[]
  resumo: Record<SituacaoLinha, number>
}

export type LinhaImportacao = Omit<LinhaPrevia, "categoria_sugerida_id" | "situacao"> & {
  categoria_id: number
}

export type ResultadoImportacao = {
  criados: number
  /** Já importadas antes ou repetidas no lote. */
  ignoradas: number
  lancamento_ids: number[]
}

// Espelham app/schemas/servico.py. Valores em centavos inteiros.

/** Derivada pela API: `recebido` se o lançamento está realizado; senão pela data prevista. */
export type SituacaoServico = "a_receber" | "atrasado" | "recebido"

export type Servico = {
  id: number
  cliente: string
  descricao: string | null
  /** Centavos, o combinado. */
  valor: number
  /** ISO `YYYY-MM-DD` */
  data_prevista: string
  categoria_id: number
  lancamento_id: number
  situacao: SituacaoServico
  /** Só quando recebido. */
  data_recebimento: string | null
  valor_recebido: number | null
  criado_em: string
}

/** A categoria é de entrada e não pode ser "Salário". */
export type ServicoIn = {
  cliente: string
  descricao?: string | null
  valor: number
  data_prevista: string
  categoria_id: number
}

/** Só enquanto não recebido. `descricao: null` remove a descrição. */
export type ServicoPatch = Partial<ServicoIn>

/** `valor` ausente: recebeu o valor combinado. A data não pode ser futura. */
export type RecebimentoIn = { data: string; valor?: number }

// Espelham app/schemas/lembrete.py. Contas e valores vêm dos lançamentos previstos, na hora.

/** Conta a pagar (saída prevista), valor a receber (entrada prevista) ou lembrete livre. */
export type OrigemLembrete = "conta" | "valor" | "livre"
/** Atrasado: antes de hoje. A vencer: de hoje até hoje + 3 dias. */
export type SituacaoLembrete = "atrasado" | "a_vencer"

export type LembreteLivre = {
  id: number
  texto: string
  /** ISO `YYYY-MM-DD` */
  data: string
  concluido: boolean
  concluido_em: string | null
  criado_em: string
}

export type ItemLembrete = {
  origem: OrigemLembrete
  situacao: SituacaoLembrete
  /** ISO `YYYY-MM-DD` */
  data: string
  /** Em "conta" e "valor". */
  lancamento: Lancamento | null
  /** Em "livre". */
  lembrete: LembreteLivre | null
}

export type LembretesOut = {
  hoje: string
  /** Último dia da janela "a vencer", inclusive. */
  limite: string
  atrasados: ItemLembrete[]
  a_vencer: ItemLembrete[]
}
