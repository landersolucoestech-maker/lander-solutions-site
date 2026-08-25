# Financeiro → Rateios — Arquitetura canônica

## Escopo

Este documento descreve exclusivamente o domínio **Financeiro → Rateios**. Ele formaliza a distribuição analítica de custos e despesas já existentes sem criar novas movimentações financeiras.

A regra de ownership é:

```text
DESPESA EXISTENTE
→ RATEIO
→ DISTRIBUIÇÃO ANALÍTICA
```

Nunca:

```text
DESPESA EXISTENTE
→ RATEIO
→ NOVAS DESPESAS
```

Rateio não é Participação Econômica, Repasse, regra societária ou categorização financeira.

## Fonte financeira

A movimentação financeira continua pertencendo a:

```text
state.crmFinancialTransactions
ValtrenFinanceCore.createService()
```

Cada Rateio guarda somente `sourceTransactionId`. A transação original continua existindo uma única vez e mantém seu `amount` original.

## Fonte canônica de Rateios

O estado canônico é:

```text
state.crmCostAllocations
├── allocations
├── lines
├── criteria
├── approvals
├── history
└── metadata
```

`allocations` contém o cabeçalho e workflow. `lines` contém os destinos e a memória calculada. `criteria` contém modelos reutilizáveis internos. `approvals` e `history` registram governança operacional.

## Relação com `transaction.allocations[]`

`transaction.allocations[]` deixa de ser o owner da definição do Rateio e passa a ser **projeção efetiva do Rateio postado**.

```text
state.crmCostAllocations
        │
        ├─ draft / review / approved
        │     → não projeta nada
        │
        └─ posted
              → transaction.allocations[]
                 source = cost_allocation
                 status = posted
```

Assim existem duas responsabilidades, mas uma única definição oficial:

- `state.crmCostAllocations`: fonte canônica e auditável do Rateio;
- `transaction.allocations[]`: projeção derivada usada pelo consumidor dimensional existente.

A projeção nunca cria uma nova transação.

## Legado

Distribuições simples já presentes em `transaction.allocations[]` são tratadas por compatibilidade:

- somente custos/despesas de saída elegíveis podem ser promovidos a Rateio;
- allocation legado de receita não é transformado em Rateio;
- allocation de transação `pending` vira Rascunho e deixa de produzir efeito dimensional;
- allocation de despesa `posted` pode ser promovido a Rateio postado, preservando o mesmo valor financeiro;
- o processo é marcado por `metadata.legacyMigrated` para não criar estruturas concorrentes.

A antiga ação **Distribuir transação** em Transações deixa de manter editor próprio e direciona para `Financeiro → Rateios` com a transação de origem pré-selecionada.

## Elegibilidade

O domínio aceita normalmente apenas transações que satisfaçam:

```text
financialNature = expense
direction = outflow
isDemo != true
status != excluded
financialNature != transfer
```

Transação `pending` pode originar um Rateio em preparação, porém o Rateio só pode ser postado quando a transação estiver `posted`.

Receitas não são distribuídas por este domínio. Participação de receitas pertence ao futuro módulo **Participações**.

## Modelagem do Rateio

Cabeçalho principal:

```text
id
sourceTransactionId
name
description
method
criterionId
basisAmount
distributedAmount
unallocatedAmount
totalPercentage
allowPartial
status
effectiveDate
accountingPeriod
submittedAt / submittedBy
reviewedAt / reviewedBy
approvedAt / approvedBy
postedAt / postedBy
reversedAt / reversedBy
reversalReason
notes
version
parentAllocationId
replacesAllocationId
sourceSnapshot
consistencyStatus
consistencyIssues
isDemo
metadata
createdAt / createdBy
updatedAt / updatedBy
```

`sourceSnapshot` preserva a memória da transação observada durante a criação/postagem. Ele não substitui a transação original e é usado para detectar alterações posteriores.

## Linhas

Cada destino é uma linha:

```text
id
allocationId
destinationType
destinationId
percentage
amount
driverValue
note
metadata
order
```

Destinos suportados nesta etapa:

```text
corporate
product
service
business_unit
```

`corporate` é dimensão própria e não é um produto fictício.

Produto, Serviço e Unidade de Negócio são apenas referências a owners externos. Rateios não cria catálogos paralelos.

## Métodos

### Percentual

Todos os percentuais são informados explicitamente. Rateio integral exige soma lógica de 100%, com tolerância numérica controlada.

### Valor fixo

Cada linha informa valor. Rateio integral exige soma monetária exata do `basisAmount` até o centavo.

### Divisão igual

O valor é dividido em centavos inteiros. Sobras de arredondamento são distribuídas deterministicamente.

Exemplo:

```text
R$ 100,00 / 3
→ R$ 33,34
→ R$ 33,33
→ R$ 33,33
= R$ 100,00
```

### Direcionador

Cada linha recebe `driverValue`. O sistema calcula a proporção relativa e distribui o valor em centavos.

O domínio não inventa driver real. Receita, headcount, usuários, horas, consumo ou área precisam ser fornecidos por fonte válida ou usuário.

## Rateio parcial

O padrão é integral.

Rateio parcial só é permitido quando `allowPartial = true`. Nessa situação são exibidos e preservados:

```text
distributedAmount
unallocatedAmount
totalPercentage
```

Uma diferença nunca é escondida.

## Workflow

Fluxo normal:

```text
Rascunho
→ Em revisão
→ Aprovado
→ Postado
```

Fluxo de correção:

```text
Em revisão
→ Rascunho
```

Fluxo de reversão:

```text
Postado
→ Estornado
```

Transições fora desse fluxo são rejeitadas pelo domínio.

### Rascunho

Pode alterar origem, método, destinos, valores, percentuais, drivers e observações. Não tem efeito contábil dimensional.

### Revisão

A entrada em revisão valida origem, linhas, destinos, soma e reconciliação. O evento e usuário são registrados.

### Aprovação

Registra `approvedAt`, `approvedBy` e a versão. Ainda não produz efeito dimensional.

### Postagem

É o único momento em que o Rateio passa a produzir a projeção efetiva em `transaction.allocations[]`.

A postagem é idempotente: postar novamente o mesmo Rateio não multiplica as linhas.

### Estorno

Remove/reverte somente a projeção dimensional do Rateio, preservando:

- transação financeira;
- cabeçalho do Rateio;
- linhas;
- versão;
- motivo;
- histórico.

O Rateio permanece com `status = reversed`.

## Versionamento

Rateio postado ou estornado não é editado silenciosamente.

Uma nova distribuição cria nova versão:

```text
v1 → posted → reversed
v2 → draft → review → approved → posted
```

`parentAllocationId` e `replacesAllocationId` preservam a cadeia.

Enquanto um Rateio postado consistente estiver ativo, outro Rateio concorrente para a mesma transação é bloqueado para evitar double counting.

## Memória de cálculo

O serviço expõe a memória com:

```text
sourceTransactionId
sourceDescription
basisAmount
method
criterionId
lines
distributedAmount
unallocatedAmount
totalPercentage
version
consistency
```

A UI apresenta:

```text
Destino
Base / Driver
Percentual
Valor
```

com total consolidado.

## Critérios reutilizáveis

`criteria[]` permite guardar modelos internos de distribuição. Eles não são um submódulo do sidebar e não são aplicados automaticamente a novas despesas.

A aplicação de um critério requer ação explícita e continua passando pelas validações do Rateio.

## Integração com Contabilidade

A DRE consolidada continua lendo a transação original uma única vez:

```text
Despesa original = R$ 10.000
DRE geral        = R$ 10.000
```

Quando há Rateio postado:

```text
Produto A   = R$ 4.000
Produto B   = R$ 3.500
Corporativo = R$ 2.500
```

A soma dimensional reconcilia:

```text
R$ 4.000 + R$ 3.500 + R$ 2.500 = R$ 10.000
```

Nunca é adicionada outra despesa à DRE.

O adapter dimensional do bundle reconhece:

```text
corporate
product
service
business_unit
```

Somente projeções efetivas/postadas são consumidas.

## Alteração da transação após Rateio

O Rateio guarda `sourceSnapshot` e revalida transações aprovadas/postadas.

Mudanças relevantes incluem:

```text
valor
status/exclusão
categoria
businessDimension/productId
natureza financeira
direção
```

Se uma transação postada mudar de forma incompatível:

```text
consistencyStatus = needs_review
```

A memória original é preservada e a projeção dimensional efetiva é retirada. O sistema não recalcula o Rateio silenciosamente.

A Contabilidade recebe uma pendência `allocation_needs_review` quando aplicável.

## Dados demo

Rateios marcados `isDemo = true` não entram na consulta operacional real por padrão. Transações demo não são elegíveis como origem de um Rateio real.

## Não pertencem ao domínio

Rateios não implementa:

- cálculo de Participações;
- Repasses ou pagamentos;
- regras societárias;
- cadastro de Produtos;
- cadastro de Serviços;
- cadastro de Unidades de Negócio;
- categorização automática da transação;
- criação de novas movimentações bancárias.

## Rota e navegação

Rota canônica:

```text
#/crm/financeiro/rateios
```

Breadcrumb:

```text
Financeiro / Rateios
```

A arquitetura do sidebar permanece:

```text
Financeiro
├── Transações
├── Contabilidade
├── Notas Fiscais
├── Rateios
├── Participações
└── Repasses
```

Direcionadores, Critérios, Alocações e Memória de Cálculo são conceitos internos e não viram itens do sidebar.

## Limitações atuais honestas

O projeto continua sendo frontend materializado/local-state. Esta etapa não cria backend, banco de dados, workflow de autorização server-side ou catálogo de Negócios inexistente.

Papéis de Criar/Revisar/Aprovar/Postar/Estornar ficam estruturalmente separáveis, mas não é criado um novo sistema de permissões e nenhuma autorização inexistente é simulada.
