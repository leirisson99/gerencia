Briefing — Controle Financeiro Pessoal
28 de set. de 2026 · @Leirisson Souza dos santos
Resumo
Um sistema pessoal de controle financeiro em que o salário é o centro: cada ciclo começa no dia do pagamento e responde quanto entrou, para onde foi e quanto sobrou. O que sobra alimenta uma cartela de poupança por metas, sem prazo. O desenvolvedor é o primeiro usuário, mas o sistema roda na web e é multiusuário: qualquer pessoa pode se cadastrar e cada uma vê só os próprios dados. Uso próprio e portfólio, sem intenção de venda.
Este MVP é um recorte do planejador pessoal (metas, hábitos, poupança, gastos): só controle financeiro + poupança. Metas com IA e hábitos ficam para depois.
Elemento
Situação
Problema
Definido: não sabe para onde o dinheiro vai
Cliente
Definido: o próprio desenvolvedor
Solução
Definida: lançamento manual + visão por categoria no ciclo do salário
Diferencial
Não se aplica (uso próprio); valor está no hábito de uso
Monetização
Não se aplica
MVP
Definido (P0 abaixo)
Validação
Pendente: usar por 2 ciclos de salário
Problema e persona
Problema: não saber para onde o dinheiro vai. Não é falta de dinheiro no fim do mês nem dificuldade de guardar; é falta de visibilidade.
Persona: desenvolvedor, salário único, dia do pagamento ainda não conhecido. Tem gastos fixos, gastos variáveis do dia a dia, fatura de cartão de crédito, compras parceladas e dinheiro que deve ou que devem a ele.
Como resolve hoje: não resolve. Não existe controle de gastos, dívidas nem poupança.
O que ele quer ver no fim do ciclo: quanto gastou em cada categoria (visão principal) e o saldo do ciclo (salário − saídas).
Solução e proposta de valor
Um sistema que me mostra, a cada salário, para onde meu dinheiro foi por categoria, quanto devo e quanto sobrou para guardar, com lançamento manual em poucos segundos.
A solução tem dois módulos que conversam:
1. Controle financeiro: entradas e saídas lançadas à mão, organizadas no ciclo do salário, com dívidas parceladas geradas automaticamente.
2. Poupança: cartelas de depósitos sequenciais por meta, sem prazo. O que sobra do ciclo é o combustível natural para marcar números da cartela.
Regras de negócio
Ciclo do salário
• O ciclo começa quando o salário é lançado manualmente, na categoria "Salário", e vai até a véspera do próximo salário lançado (ex.: 5/out a 4/nov). O ciclo mais recente fica aberto, sem data de fim.
• Não há configuração de dia de pagamento (nem dia fixo, nem dia útil, nem feriados): a data real do salário é a que vale.
• Só a categoria "Salário" abre ciclo. 13º, adiantamentos e outras entradas vão para outras categorias.
• Antes do primeiro salário, nenhum outro lançamento é aceito.
• Todo lançamento pertence ao ciclo em que sua data cai.
• Saldo do ciclo = entradas − saídas.
Lançamentos
• Tudo é lançado manualmente: valor, categoria, data e descrição opcional. Lançar um gasto deve levar menos de 10 segundos.
• Fixos: cadastrados uma vez (ex.: Internet, R$ 100, todo dia 10). O sistema gera o lançamento previsto em cada ciclo; o usuário confirma o pagamento.
• Variáveis: lançados quando acontecem (hambúrguer, mercado, Uber).
Cartão de crédito
• O cartão entra só como fatura total, lançada à mão como um gasto na data em que é paga. Não há cadastro de cartão nem de compras individuais no cartão.
• Regra obrigatória: compras feitas no cartão não são lançadas individualmente. Se o hambúrguer foi no cartão, ele já está dentro da fatura; lançar os dois conta o gasto duas vezes.
• Consequência: tudo que passa pelo cartão aparece numa única categoria, "Cartão de crédito". Ver o risco R1.
Dívidas
• Direção: eu devo (parcelamentos, empréstimos) ou me devem (dinheiro emprestado a alguém).
• Campos: descrição, pessoa/credor, valor total, número de parcelas, forma de pagamento (Pix, boleto, cartão, dinheiro), dia de vencimento.
• O cadastro gera todas as parcelas como lançamentos previstos. Cada uma é marcada como paga ou recebida.
• Pagamento fixo sem fim definido não é dívida: é um gasto fixo.
• Parcela paga no cartão: continua valendo a regra do cartão. A dívida serve para acompanhar "faltam 4 de 10", mas o dinheiro sai via fatura, então a parcela não entra no saldo por conta própria.
Cartela de poupança
• Parâmetros: meta (ex.: R$ 1.000) e valor base (padrão R$ 1). Os depósitos são 1×, 2×, 3×… o valor base.
• O sistema acha o maior N em que a soma não passa da meta:
\text{base} \cdot \frac{N(N+1)}{2} \le \text{meta}
• O resto (meta − soma) vira uma casa extra de ajuste, para a cartela fechar exatamente na meta.
• Depósitos são marcados em qualquer ordem, sem data. A cartela mostra total guardado, quanto falta, percentual e o maior número ainda livre.
Meta
Base
Depósitos
Soma
Casa de ajuste
R$ 1.378
R$ 1
1 a 52
R$ 1.378
nenhuma
R$ 1.000
R$ 1
1 a 44
R$ 990
R$ 10
R$ 5.000
R$ 1
1 a 99
R$ 4.950
R$ 50
R$ 5.000
R$ 5
5 a 220 (44 casas)
R$ 4.950
R$ 50
MVP
Hipótese que o MVP valida: se lançar gastos for rápido e o fim do ciclo mostrar o gasto por categoria, eu vou manter o uso por pelo menos 2 ciclos de salário.
P0: essencial
[ ] Cadastro (nome, e-mail, telefone, cargo obrigatórios; data de nascimento opcional), login com e-mail e senha e troca da própria senha
[ ] Painel do administrador (um único, criado no servidor) para resetar senha de usuários
[ ] Lançamento do salário abrindo o ciclo, ciclo atual e navegação entre ciclos
[ ] Categorias (lista inicial pronta, editável)
[ ] Lançamento manual de entrada e saída: valor, categoria, data, descrição opcional
[ ] Gastos fixos recorrentes gerados em cada ciclo, com confirmação de pagamento
[ ] Dívidas (eu devo / me devem) com geração de parcelas e marcação de paga/recebida
[ ] Tela do ciclo: gasto por categoria + saldo (entradas − saídas)
[ ] Cartela de poupança: criar meta, gerar casas com ajuste, marcar depósito, ver progresso
P1: importante, pode esperar
• Contas a pagar dos próximos dias (fixos e parcelas pendentes do ciclo)
• Cartão como entidade (fechamento, vencimento) e compras individuais categorizadas, com a fatura tratada como transferência
• Comparação com o ciclo anterior
• Resumo de dívidas: total devido, total a receber
P2: futuro
• Limite por categoria com aviso
• Projeção de fluxo de caixa para os próximos ciclos
• Importação de extrato (OFX/CSV)
• Assistente de IA para analisar gastos e sugerir quanto guardar
• Integração com os módulos de metas e hábitos do planejador
Fluxo principal
Tudo que entra (salário, previstos gerados de fixos e dívidas, lançamentos manuais) cai no ciclo pela data. A tela do ciclo mostra gasto por categoria e saldo. A sobra vira depósito na cartela, e cada depósito volta ao ciclo como uma saída na categoria "Poupança".
Modelo de dados e stack
O ciclo não é tabela: é derivado das datas dos salários lançados. Valores em centavos (inteiro), nunca float. Todas as tabelas financeiras têm dono (usuario_id).
Tabela
Campos principais
Observação
usuario
nome, email, senha_hash, telefone, cargo, data_nascimento?, papel (usuario / admin)
E-mail único; um único admin
categoria
nome, tipo (entrada / saida), ativa
Inclui "Salário" (de sistema, abre ciclo), "Cartão de crédito" e "Poupança"
recorrencia
descricao, valor, tipo, categoria_id, dia, ativa
Só gastos e rendas fixas; o salário é lançado à mão
divida
descricao, pessoa, direcao (devo / me_devem), valor_total, parcelas, forma_pagamento, dia_vencimento, data_inicio
Gera N lançamentos
lancamento
data, valor, tipo, categoria_id, descricao, status (previsto / realizado), forma_pagamento, recorrencia_id?, divida_id?, parcela_num?, conta_no_saldo
Tabela central
cartela
nome, meta, valor_base, criada_em
Sem data de fim
casa
cartela_id, valor, ordem, is_ajuste, depositado_em?
depositado_em nulo = casa livre
• conta_no_saldo = false para parcelas pagas no cartão: aparecem no acompanhamento da dívida, mas o dinheiro sai pela fatura.
• Proposta: marcar uma casa da cartela gera um lançamento de saída na categoria "Poupança", para o saldo do ciclo refletir o que foi guardado.
Stack sugerida (Python, como já decidido):
• Backend: FastAPI + SQLAlchemy + Alembic
• Banco: PostgreSQL desde o início (multiusuário na web)
• Frontend: React/Next.js responsivo, pensado para lançar gasto pelo celular
• Deploy: Docker
Sem IA no MVP: nenhuma regra acima precisa dela.
Hipóteses e riscos
Hipóteses (não comprovadas)
• H1: ver o gasto por categoria vai mudar o jeito que eu gasto.
• H2: vou manter o lançamento manual por mais de 2 ciclos.
• H3: a maior parte dos gastos variáveis sai por Pix/débito, não pelo cartão.
• H4: a lista inicial de categorias cobre 90% dos gastos sem precisar criar novas.
Riscos
#
Risco
Mitigação
R1
Se muito gasto passa pelo cartão, a categoria "Cartão de crédito" vira caixa-preta e o problema principal (não saber para onde vai) continua
Medir no 1º ciclo quanto do total foi fatura; se passar de ~40%, antecipar o cartão com compras categorizadas (P1)
R2
Parar de lançar por atrito: formulário longo, sistema só no computador
Formulário com valor + categoria; frontend pensado para celular
R3
Lançar a compra no cartão e a fatura, contando duas vezes
Regra clara na tela de lançamento; forma de pagamento "cartão" bloqueada para gastos avulsos
R4
Escopo crescer para ERP pessoal antes de usar
Não começar P1 antes de 2 ciclos de uso real
R5
Salário lançado com data errada distorce os ciclos
Ciclo derivado das datas dos salários, nunca gravado: corrigir a data recalcula os ciclos
Validação e próximos passos
Hipótese principal: se o lançamento for rápido e a tela do ciclo mostrar gasto por categoria, eu uso por 2 ciclos seguidos e descubro pelo menos uma categoria em que gasto mais do que imaginava.
Métrica
Meta
Dias com pelo menos 1 lançamento por semana
≥ 5
Ciclos seguidos em uso
≥ 2
Parte das saídas na categoria "Cartão de crédito"
< 40% (acima disso, ver R1)
Descobertas ("gasto mais com X do que achava")
≥ 1
Teste barato antes de codar (opcional, 1 semana): anotar todo gasto numa planilha com valor, categoria e forma de pagamento. Isso valida a lista de categorias (H4) e mostra quanto passa pelo cartão (H3/R1) antes de o modelo de dados ficar pronto.
Próximos passos
[ ] Definir a lista inicial de categorias (entrada e saída)
[ ] Criar o projeto FastAPI + PostgreSQL com as tabelas acima e migrações
[ ] Cadastro, login e painel do administrador
[ ] Implementar e testar o ciclo aberto pelo salário (primeiro ciclo, ciclo aberto, virada de ano, correção e exclusão de salário)
[ ] Implementar e testar a geração da cartela (N, casa de ajuste, soma = meta)
[ ] Endpoints de lançamento, recorrência e dívida com geração de parcelas
[ ] Tela de lançamento rápido (celular) e tela do ciclo (gasto por categoria + saldo)
[ ] Tela da cartela
[ ] Usar por 2 ciclos e revisar as métricas antes de começar qualquer item P1