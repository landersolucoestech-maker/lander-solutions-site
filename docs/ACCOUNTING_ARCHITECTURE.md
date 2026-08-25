# Financeiro → Contabilidade — Arquitetura Canônica

Esta documentação registra exclusivamente a camada de `Financeiro → Contabilidade` do Sistema Interno da Valtren.

## Responsabilidade

Contabilidade é uma camada contábil e gerencial **derivada de Transações**. Ela classifica, atribui competência, agrega e analisa movimentos financeiros existentes. Não cria uma segunda base de receitas, despesas, pagamentos ou recebimentos.

A fonte operacional permanece:

```text
state.crmFinancialTransactions
ValtrenFinanceCore.createService()
```

A Contabilidade consulta essa fonte por meio de `crmFinanceService()`.

## Estado contábil

A fonte de metadados contábeis é:

```text
state.crmAccounting
```

Ela contém somente:

```text
classifications
mappings
transactionMeta
history
periods
metadata
```

`transactionMeta` referencia o movimento financeiro pelo `transactionId` e armazena somente atributos contábeis complementares, como:

```text
recognitionDate
classificationId
serviceId
businessUnitId
```

Valor, descrição bancária, conta, contraparte e categoria financeira continuam pertencendo à transação canônica e não são copiados para Contabilidade.

## DRE gerencial

A estrutura gerencial é extensível e contempla os grupos:

```text
Receita Bruta
Deduções da Receita
Custos
Despesas Operacionais
Resultado Financeiro
Outros Resultados
Tributos sobre Resultado
```

A apresentação deriva matematicamente:

```text
Receita Bruta
(-) Deduções
= Receita Líquida
(-) Custos
= Resultado Bruto
(-) Despesas Operacionais
= Resultado Operacional
(+/-) Resultado Financeiro
(+/-) Outros Resultados
= Resultado antes de Tributos
(-) Tributos sobre Resultado
= Resultado Final
```

Linhas sem movimentos não precisam ser forçadas na interface. Tributos não são inferidos a partir de receita; só entram quando possuem classificação explícita.

## Elegibilidade

A DRE oficial considera somente movimentos que sejam:

```text
status = posted
isDemo = false
financialNature != transfer
```

`pending`, `excluded`, demonstrações e transferências não contaminam o resultado oficial.

No regime de competência, uma movimentação também precisa possuir data de reconhecimento válida. Movimentos incompletos permanecem visíveis em `Lançamentos` como pendências contábeis, mas não entram silenciosamente na DRE.

## Caixa e Competência

### Caixa

A data utilizada é, em ordem:

```text
settlementDate
transactionDate
postedAt
```

### Competência

A data utilizada é:

```text
state.crmAccounting.transactionMeta[transactionId].recognitionDate
```

com compatibilidade para uma futura referência confiável em metadados da própria transação.

A data financeira original `transactionDate` nunca é sobrescrita para representar competência.

## Períodos

A estrutura está preparada para estados:

```text
open
review
closed
```

Esses estados são apenas infraestrutura de metadados nesta etapa. Não existe processo de fechamento contábil simulado nem governança de fechamento apresentada como funcional.

## Categoria financeira e classificação contábil

Categoria financeira continua sendo propriedade de `Financeiro → Transações`.

Contabilidade possui mapeamentos:

```text
Categoria Financeira
→ Classificação Contábil padrão
```

A estrutura padrão é deliberadamente conservadora. Categorias ambíguas não recebem automaticamente um significado fiscal/contábil específico.

Exemplos de mapeamentos seguros:

```text
Receita de Produto → Receita Operacional / Produtos
Receita de Serviços → Receita Operacional / Serviços
Marketing → Despesas Operacionais / Marketing
Software → Despesas Operacionais / Tecnologia
Folha → Despesas Operacionais / Pessoal
Tarifas Bancárias → Resultado Financeiro / Despesas Financeiras
```

## Override

Uma transação pode receber `classificationId` manual em Contabilidade. O override prevalece sobre o mapeamento padrão sem alterar `categoryId` da transação financeira.

Alterações registram histórico com transação, antes/depois, usuário, horário e origem.

## Produto, Corporativo, Serviço e Unidade

Produto/Sistema reutiliza `productId` e `businessDimension` vindos de Transações. `Corporativo` continua sendo uma dimensão válida e não exige produto.

Serviço e Unidade de Negócio são apenas referências estáveis:

```text
serviceId
businessUnitId
```

A Contabilidade não cria catálogos próprios. As opções de interface só aparecem quando dados reais forem disponibilizados pelos futuros owners de Negócios.

## Allocations / Rateios

A Contabilidade consome `allocations` existentes na transação.

Na consolidação geral, a transação é contabilizada **uma única vez pelo valor integral**. Em análises dimensionais, o mesmo valor é distribuído pelas parcelas válidas.

Exemplo:

```text
Transação = R$ 10.000
Produto A = 40% → R$ 4.000
Produto B = 35% → R$ 3.500
Corporativo = 25% → R$ 2.500
```

A DRE geral continua em R$ 10.000, não R$ 20.000. Contabilidade não implementa aprovação, postagem, estorno ou governança do futuro módulo Rateios.

## Transferências

`financialNature = transfer` é excluída de receita, custo, despesa, margem e resultado. A movimentação entre contas permanece patrimonial e não infla a DRE.

## Estornos, reembolsos e chargebacks

Quando `refund`, `reimbursement`, `reversal` ou `chargeback` possui `relatedTransactionId`, a Contabilidade pode herdar a classificação econômica da movimentação original e aplicar contribuição reversa.

Assim, por exemplo, um chargeback relacionado a uma receita reduz aquela receita em vez de virar uma nova receita ou despesa arbitrária.

## Pendências contábeis

São identificáveis, conforme aplicável:

```text
unclassified
missing_competence
missing_product_reference
invalid_allocation_reference
invalid_classification_reference
```

A interface exibe contagem real e permite revisar esses movimentos em `Lançamentos`.

## Drill-down

Cada linha da DRE consulta os movimentos canônicos que compõem o valor. O drill-down não cria cópias financeiras e oferece navegação de volta para `Financeiro → Transações`.

## Partidas dobradas

Esta etapa implementa **contabilidade gerencial, classificação, competência e DRE**. Não existe um motor confiável de partidas dobradas no stack atual, portanto a aplicação não se apresenta como razão contábil legal oficial nem inventa débito/crédito formal incompleto.

## P&L legado

As antigas estruturas independentes de:

```text
P&L Empresa
P&L Projetos
P&L Artistas
```

foram neutralizadas na materialização. Dimensões gerenciais são filtros da mesma Contabilidade, não páginas paralelas.

A rota canônica permanece:

```text
#/crm/financeiro/accounting
```

O sidebar não é alterado por esta camada.
