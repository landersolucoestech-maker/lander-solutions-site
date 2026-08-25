# Financeiro → Transações — Arquitetura Canônica

Esta documentação registra exclusivamente a implementação de `Financeiro → Transações` do Sistema Interno da Valtren.

## Responsabilidade

Transações é o livro financeiro operacional. Sua função é capturar, revisar, identificar, classificar, relacionar, confirmar e conciliar movimentações financeiras.

Não é Dashboard, DRE, Contabilidade, Rateios, Participações ou Repasses.

## Fonte canônica

A fonte de verdade é:

```text
state.crmFinancialTransactions
```

A manipulação é centralizada por:

```text
ValtrenFinanceCore.createService()
```

O estado possui:

```text
accounts
transactions
categories
rules
matches
history
imports
metadata
```

`state.crmRefTransactions` permanece apenas como projeção temporária de compatibilidade para código legado. Nenhum fluxo novo deve tratá-lo como fonte de verdade.

## Conta financeira

Uma conta financeira possui ID estável, nome, instituição, tipo, moeda, saldos opcionais, status, origem, referência de integração, flag de integração validada, última atualização e metadados.

Contas manuais não são exibidas como conectadas ou sincronizadas. `integrationValidated=true` só é aceito quando existe `integrationId` explícito.

Saldos desconhecidos permanecem `null`; não são transformados em `R$ 0,00` fictício.

## Transação

A transação canônica possui, conforme aplicável:

```text
id
financialAccountId
externalId
transactionDate
settlementDate
importedAt
postedAt
originalDescription
normalizedDescription
amount
direction
financialNature
counterpartyType
counterpartyId
categoryId
subcategoryId
businessDimension
productId
unitReferenceId
allocations
source
sourceReference
status
reconciliationStatus
attachments
notes
relatedTransactionId
classificationSource
isDemo
createdAt
updatedAt
createdBy
updatedBy
```

### Valor

A regra interna é:

```text
amount = valor absoluto
direction = inflow | outflow
```

Não se usa valor negativo para representar saída.

### Status operacional

Os estados visíveis são exatamente:

```text
pending  → Pendente
posted   → Lançada
excluded → Excluída
```

Exclusão é lógica e preserva registro, motivo, usuário, horário e histórico. A transação pode ser restaurada.

### Conciliação

Conciliação é separada do status operacional:

```text
unreconciled
matched
reconciled
```

Uma transação lançada pode ser conciliada e a conciliação pode ser revertida de forma rastreável.

## Contraparte

A contraparte financeira não possui cadastro independente.

Pode apontar para:

```text
Person
Organization
FinancialAccount
```

Pessoas e Organizações utilizam diretamente a infraestrutura canônica:

```text
state.crmCanonicalParties
crmCanonicalPartyService()
```

Não existem `financialCustomers`, `financialSuppliers` ou `transactionVendors` como identidades paralelas.

## Categorias

Categorias são dados auxiliares de Transações e não módulo do sidebar.

A taxonomia inicial do domínio contempla categorias e subcategorias operacionais como Receita de Serviços, Receita de Produto, Marketing / Tráfego Pago, Software, Infraestrutura / Cloud, Impostos, Honorários, Folha, Comissão, Reembolso, Tarifas Bancárias e Transferência entre Contas.

A classificação pode ser corrigida inline e toda alteração relevante gera histórico operacional.

## Produto/Sistema e Corporativo

A transação pode possuir:

```text
businessDimension = unassigned | corporate | product
```

`corporate` representa movimentação geral da Valtren sem produto específico.

`product` exige `productId` estável. O Financeiro não cria catálogo próprio. O browser consulta apenas referências estruturadas disponibilizadas futuramente por Negócios.

Nenhum produto específico é hardcoded no módulo financeiro.

## Rateio / allocations

A transação permanece única. A distribuição analítica fica em `allocations`.

São suportados:

```text
percentual total = 100%
```

ou:

```text
soma dos valores = valor integral da transação
```

Um destino pode ser `corporate` ou `product`.

Configurar rateio não cria nova despesa nem nova transação.

A governança completa de Rateios permanece fora deste módulo.

## Regras automáticas

`rules` permite critérios por descrição, contraparte, direção, conta e faixa de valor, aplicando classificação de categoria, Produto/Sistema e natureza.

Quando uma regra classifica uma transação:

```text
classificationSource = rule
metadata.classificationRuleId = <id>
```

Uma correção manual muda a origem para `manual` e prevalece sobre a regra aplicada anteriormente.

## Correspondência / Match

`matches` relaciona uma transação a um registro financeiro existente por referência:

```text
transactionId
↔
targetType + targetId
```

Tipos preparados incluem conta a receber, conta a pagar, recebimento/pagamento previsto, transferência, reembolso, repasse, Nota Fiscal e outros.

Match não cria outro lançamento financeiro.

## Transferências

Transferência interna cria duas pontas bancárias relacionadas:

```text
Conta A → outflow
Conta B → inflow
```

Ambas possuem:

```text
financialNature = transfer
relatedTransactionId = outra ponta
```

Transferências não entram em receita nem despesa operacional.

## Estornos, reembolsos e reversões

Movimentos reversos usam `relatedTransactionId` para referenciar a transação original e naturezas separadas (`reversal`, `reimbursement`, `refund`, `chargeback`).

Nenhum crédito ou débito reverso é automaticamente tratado como receita/despesa sem classificação explícita.

## Origem

A origem é centralizada em:

```text
manual
import
integration
```

Todos os fluxos criam o mesmo tipo de transação canônica.

## Importação

O domínio suporta importação de registros já normalizados e deduplicação segura.

Prioridade de deduplicação:

```text
financialAccountId + externalId/FITID
```

Fallback:

```text
conta + data + direção + valor + descrição normalizada
```

O projeto ainda não possui parser OFX validado. Por isso a UI não simula upload funcional. A tela informa explicitamente essa limitação e não apresenta importação falsa como concluída.

## Dados demonstrativos

O domínio suporta `isDemo`, porém nenhuma movimentação financeira demonstrativa é criada pela implementação nova.

Transações `isDemo=true` são excluídas de consultas operacionais padrão e de totais reais.

## Interface

A estrutura visual segue:

```text
Transações

[Contas financeiras horizontais]

[Pendentes] [Lançadas] [Excluídas]

[Busca + período + tipo + Produto/Sistema + conta + mais filtros]

[TableView]

[Paginação]
```

A TableView prioriza:

```text
Data
Descrição
Saída
Entrada
Origem/Destino
Categoria
Produto/Sistema
Status
Ação
```

Contraparte, categoria e Produto/Sistema podem ser alterados inline.

Ações em massa são contextuais por status.

O detalhe da transação usa drawer lateral e apresenta dados da movimentação, classificação, distribuição, correspondência, documentos, observações e histórico.

## Compatibilidade legada

Quando existirem registros em `state.crmRefTransactions`, eles são migrados uma única vez para a fonte canônica e preservam snapshot/ID legado em metadados.

Após a migração, `state.crmRefTransactions` é apenas uma projeção derivada da fonte canônica.

## Materialização

`scripts/crm_financial_transactions.py` é executado após a arquitetura definitiva e o CRM completo. Ele substitui apenas a rota raiz:

```text
#/crm/financeiro
```

para `crmTransactionsPage()`.

O patch valida que o sidebar financeiro continua contendo somente:

```text
Transações
Contabilidade
Notas Fiscais
Rateios
Participações
Repasses
```

E garante que Regras de Categorização, Categorias Financeiras e Automações Financeiras não sejam reintroduzidas no sidebar.
