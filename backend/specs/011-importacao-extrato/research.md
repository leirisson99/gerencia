# Research: Importação de Extrato

Decisões técnicas da feature 011. Os layouts foram levantados nos extratos reais do usuário
(`extratos/`, fora do versionamento), lendo só a estrutura, com números e nomes mascarados. Não há
NEEDS CLARIFICATION pendente.

## R1. Formatos por banco

| Banco | OFX | CSV | PDF | Observação |
| --- | --- | --- | --- | --- |
| Nubank | ✅ `FITID` (uuid) | ✅ `Data,Valor,Identificador,Descrição`, valor `-12.34` | ✅ agrupado por dia | O `Identificador` do CSV **não** é igual ao `FITID` do OFX |
| Inter | ✅ `FITID` numérico, `TRNTYPE` `CREDIT`/`PAYMENT` | ✅ `;`, 5 linhas de preâmbulo, `Data Lançamento;Histórico;Descrição;Valor;Saldo`, valor `-1.234,56` | ✅ agrupado por dia (`dd de <mês> de aaaa`), `-R$ 99,99` | |
| Itaú | — | — | ✅ `dd/mm/aaaa DESCRIÇÃO -1.234,56`, com linhas `SALDO DO DIA` | Várias páginas |
| Mercado Pago | — | — | ✅ `dd-mm-aaaa`, coluna "ID da operação", `R$ -99,99 R$ saldo` | Descrição quebrada em linhas **acima e abaixo** da linha da data |
| Neon | — | — | ✅ `desc dd/mm/aaaa hh?mm [?]R$ 999,99 R$ saldo -` | O PDF troca `:` e o sinal de menos por `\x00`: `\x00R$` = valor negativo |
| Outro banco | ✅ genérico | ✅ genérico (mapeamento de colunas) | — | |

Os formatos que faltam em cada banco (ex.: OFX do Itaú) entram quando houver arquivo de exemplo:
um leitor novo mais uma entrada no registro de bancos (R6).

## R2. OFX: parser próprio, sem dependência

- **Decision**: ler o OFX (SGML 1.x ou XML 2.x) com um parser próprio em
  `app/domain/extrato/ofx.py`: recorta cada bloco `<STMTTRN>…</STMTTRN>`, lê `TRNAMT`, `DTPOSTED`
  (8 primeiros dígitos, ignorando hora e fuso como `[-3:BRT]`), `FITID`, `MEMO` e `NAME`. O sinal
  vem de `TRNAMT` (os dois bancos usam valor negativo para saída), não de `TRNTYPE`. A descrição é
  `MEMO`, ou `NAME` quando `MEMO` falta.
- **Rationale**: só usamos 5 tags. `ofxtools` é estrito com cabeçalhos SGML e fusos no formato
  dos bancos brasileiros, e seria uma dependência a mais para pouco ganho. Regex por bloco é
  função pura e fácil de testar.
- **Alternatives considered**: `ofxtools`, `ofxparse` (sem manutenção).

## R3. PDF: `pdfplumber` só na borda; leitores por banco puros

- **Decision**: nova dependência `pdfplumber` (MIT), usada **só** em `app/services/pdf.py`, que
  transforma o arquivo em `LinhaPdf(pagina, topo, texto)`: as palavras de cada página agrupadas por
  linha visual, com a posição vertical. Os leitores por banco (`app/domain/extrato/pdf_*.py`) são
  funções puras que recebem essa lista, então os testes usam fixtures sintéticas em texto, sem PDF
  real.
- **Rationale**: o Princípio III exige domínio puro; separar a extração de texto do layout de cada
  banco deixa a parte frágil (o layout) 100% testável. `pdfplumber` dá as coordenadas de cada
  palavra, necessárias para o Mercado Pago (R4). O PDF sem texto (escaneado) sai com lista vazia e
  vira erro `pdf_sem_texto`.
- **Alternatives considered**: `pypdf` (texto sem coordenadas confiáveis); OCR (fora de escopo,
  pesado e impreciso para dinheiro).

## R4. Descrições em várias linhas no PDF

- **Decision**: cada leitor define uma **linha âncora** (a que tem data e/ou valor). As demais
  linhas de texto da página, que não são ruído (cabeçalho, rodapé, saldo, totais), são anexadas à
  âncora **verticalmente mais próxima** na mesma página, e o texto final é a junção em ordem de
  `topo`. Isso cobre o Mercado Pago (descrição acima e abaixo da data) e o Nubank (continuação
  abaixo).
- **Rationale**: em ambos os layouts, a descrição fica centrada na linha da data; a proximidade
  vertical resolve o caso "linha de baixo de um lançamento vs. linha de cima do próximo" sem regra
  específica.

## R5. Dinheiro e datas a partir de texto

- **Decision**: `centavos(texto) -> int` em `app/domain/extrato/valores.py` aceita `1.234,56`,
  `1234.56`, `-R$ 1.234,56`, `R$ -1.234,56`, `+ 999,99` e `12.34`. O separador decimal é o último
  `,` ou `.` seguido de exatamente 2 dígitos; os demais separadores são de milhar. Só dígitos e
  sinal entram na conta, em `int`. Nunca `float` nem `Decimal` (Princípio I). Datas:
  `dd/mm/aaaa`, `dd-mm-aaaa`, `aaaammdd` e `dd de <mês por extenso ou abreviado> de aaaa`.
- **Decision**: texto de OFX e CSV é decodificado como UTF-8, com `latin-1` de reserva; BOM é
  removido.

## R6. Registro de bancos e formatos

- **Decision**: `app/domain/extrato/bancos.py` tem um dicionário `codigo → Banco(nome, leitores)`
  com códigos estáveis: `nubank`, `inter`, `itau`, `mercado_pago`, `neon` e `outro`. Cada
  formato aponta para o leitor. `GET /importacoes/bancos` é derivado dele.
- **Rationale**: acrescentar um banco é uma linha no registro mais um leitor testado.

## R7. Identificação da movimentação (`id_externo`)

- **Decision**: coluna `lancamento.id_externo VARCHAR(120) NULL` com índice único parcial
  `(usuario_id, id_externo) WHERE id_externo IS NOT NULL`.
  - Com identificador do banco (`FITID`, `Identificador` do CSV Nubank, "ID da operação" do
    Mercado Pago): `"{banco}:{formato}:{id}"`.
  - Sem identificador: `"{banco}:{formato}:h:{sha256[:40]}"` sobre data, valor com sinal,
    descrição normalizada e a **ordem entre linhas idênticas** do arquivo (o 1º café de R$ 8 do
    dia, o 2º…). É estável ao reimportar o mesmo período e distingue gastos iguais no mesmo dia
    (US3.4).
- **Rationale**: FR-011. O formato entra no id porque os ids de formatos diferentes do mesmo banco
  não batem (R1, Nubank). Entre formatos, a proteção é a "possível duplicada" (FR-012).
- **Risco aceito**: extratos sem id cujo período corta um dia no meio podem mudar a ordem entre
  linhas idênticas desse dia. O resultado é uma linha a mais como "nova"; a "possível duplicada"
  ainda a sinaliza.

## R8. Situação de cada linha na prévia

Função pura `classificar(linhas, ja_importados, existentes, primeiro_salario)`, em
`app/domain/importacao.py`, com esta precedência:
1. `invalida`: valor zero.
2. `ja_importada`: `id_externo` já existe para o usuário.
3. `antes_do_primeiro_ciclo`: o usuário **já tem** salário e a data é anterior ao primeiro. Sem
   salário no sistema, a linha fica `nova`, porque o lote pode trazer os salários (US2.1); a
   confirmação decide.
4. `possivel_duplicada`: há lançamento do usuário com a mesma data, tipo e valor, que ainda não foi
   "consumido" por outra linha do arquivo (dois cafés iguais contra um lançado à mão: o 1º é
   duplicado, o 2º é novo).
5. `nova`.

Só `nova` vem marcada por padrão (decisão do cliente; a API só informa a situação).

## R9. Sugestão de categoria

- **Decision**: `normalizar_descricao` (minúsculas, sem acentos, espaços colapsados, sem pontuação
  nas pontas). O serviço monta `norm → categoria_id` com o lançamento **mais recente** de cada
  descrição normalizada (por data e id), só com categorias ativas; a sugestão vale se o tipo da
  categoria for igual ao tipo da linha. Regra fixa, sem IA (Princípio VI).
- **Rationale**: FR-013 e US5. A normalização é feita em Python sobre as descrições do usuário
  (poucos milhares), numa consulta só.

## R10. Confirmação em lote

- **Decision**: `POST /importacoes` recebe as linhas (`id_externo`, `data`, `valor`, `tipo`,
  `descricao`, `categoria_id`) e, numa transação com `travar_escritas`:
  1. valida cada linha (categoria ativa do usuário; `categoria.tipo == tipo`; salário não futuro);
     todos os erros de linha voltam juntos, em 422 `campos` com a chave `linhas.<i>.<campo>`;
  2. descarta as linhas com `id_externo` já existente e as repetidas dentro do próprio lote
     (contadas em `ignoradas`);
  3. verifica a cobertura (`verificar_cobertura`, domínio já existente) no estado resultante,
     com os salários e a menor data dos demais, somando banco e lote;
  4. grava tudo; se o maior salário do lote passa a ser o maior de todos, gera os previstos do
     novo ciclo aberto (`gerar_previstos`, como em `criar_lancamento`), e só dele;
  5. o índice único protege de duas confirmações simultâneas (vira 409 `conflito_importacao`).
- **Rationale**: FR-008 a FR-010. Reusa as regras do lançamento manual sem chamar
  `criar_lancamento` por linha, que faria N travas, N commits e N checagens de cobertura.
- O aviso de limite (009) não é calculado na importação.

## R11. Transporte do arquivo

- **Decision**: JSON com `arquivo_base64` (máx. 2 MB decodificado; o texto base64 é limitado a
  2.796.203 caracteres no schema). O middleware `exigir_json` continua valendo para todas as
  rotas.
- **Rationale**: evita `multipart/form-data` (nova dependência `python-multipart` e exceção no
  middleware que protege contra CSRF por formulário). Arquivos de extrato são pequenos.
- Máximo de 5.000 linhas por arquivo (erro `extrato_grande`).

## R12. `LancamentoOut`

- **Decision**: `LancamentoOut` ganha `importado: bool` (derivado de `id_externo IS NOT NULL`). O
  `id_externo` não é exposto. A mudança é aditiva.
- **Rationale**: o cliente pode mostrar a origem sem conhecer o formato interno do id.

## R13. Frontend

- **Decision**: página `app/(app)/importar/page.tsx`, no padrão das features existentes
  (`features/importacao/`, `lib/api/importacao.ts`, `lib/api/types.ts`): escolha do banco e do
  formato, upload com leitura em base64 no navegador, formulário de mapeamento para CSV genérico,
  tabela de prévia (checkbox, categoria editável, selo da situação) e confirmação. Link no menu
  lateral.
