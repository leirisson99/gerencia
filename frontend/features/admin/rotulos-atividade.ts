import type { AcaoAdmin, ContagensConta, TipoEvento } from "@/lib/api/types"

/** Dia em que a linha do tempo começou a ser gravada (spec 018); antes disso não há eventos. */
export const INICIO_EVENTOS = "02/10/2026"

export const ROTULOS_EVENTO: Record<TipoEvento, string> = {
  conta_criada: "Criou a conta",
  login: "Entrou no sistema",
  senha_trocada: "Trocou a senha",
  perfil_atualizado: "Atualizou o perfil",
  lancamento_criado: "Lançou",
  lancamento_editado: "Editou lançamento",
  lancamento_excluido: "Excluiu lançamento",
  extrato_importado: "Importou extrato",
  categoria_criada: "Criou categoria",
  categoria_editada: "Editou categoria",
  recorrencia_criada: "Criou recorrência",
  recorrencia_editada: "Editou recorrência",
  divida_criada: "Criou dívida",
  cartela_criada: "Criou cartela",
  deposito_feito: "Depositou em cartela",
  deposito_desfeito: "Desfez depósito",
  servico_criado: "Criou serviço",
  servico_editado: "Editou serviço",
  servico_excluido: "Excluiu serviço",
  servico_recebido: "Marcou serviço recebido",
  recebimento_desfeito: "Desfez recebimento",
  lembrete_criado: "Criou lembrete",
  lembrete_editado: "Editou lembrete",
  lembrete_concluido: "Concluiu lembrete",
  lembrete_excluido: "Excluiu lembrete",
  push_ativado: "Ativou notificações",
  push_removido: "Desativou notificações",
}

export const ROTULOS_ACAO_ADMIN: Record<AcaoAdmin["acao"], string> = {
  reset_senha: "Resetou a senha",
  desativar_conta: "Desativou a conta",
  reativar_conta: "Reativou a conta",
  ver_atividade: "Viu a atividade",
}

/** Ordem e rótulo da grade de contagens no detalhe da conta. */
export const ROTULOS_CONTAGEM: [keyof ContagensConta, string][] = [
  ["lancamentos_manuais", "Lançamentos digitados"],
  ["lancamentos_importados", "Lançamentos importados"],
  ["lancamentos_gerados", "Lançamentos automáticos"],
  ["importacoes", "Importações de extrato"],
  ["recorrencias", "Recorrências"],
  ["dividas", "Dívidas"],
  ["cartelas", "Cartelas de poupança"],
  ["depositos", "Depósitos em cartela"],
  ["servicos", "Serviços a receber"],
  ["lembretes", "Lembretes"],
  ["aparelhos_push", "Aparelhos com notificação"],
]
