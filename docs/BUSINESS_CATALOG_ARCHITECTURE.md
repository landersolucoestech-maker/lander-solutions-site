# Negócios — catálogo canônico de Produtos, Serviços e Unidades de Negócio

## Objetivo

Esta etapa estabelece `state.crmBusinessCatalog`, operado por `ValtrenBusinessCore.createService()`, como owner único de Produtos, Serviços e Unidades de Negócio. Financeiro, Jurídico e demais domínios passam a manter somente referências por `productId`, `serviceId` e `businessUnitId`.

## Auditoria do legado

A auditoria foi feita sobre fontes de runtime, materializadores, testes e módulos de referência procurando os termos product/products/produto/produtos, service/services/serviço/serviços, businessUnit/businessUnitId/unit/units/unidade/unidades e system/systems/sistema/sistemas.

Achados principais:

- Transações possuía `crmFinanceProducts()` com fallback sobre `state.businessProducts`, `state.crmBusinessProducts` e `state.negociosProducts`. Era uma referência futura, não um owner real.
- Contabilidade possuía fallbacks equivalentes para Produtos, Serviços e Unidades. Eram somente lookups futuros para filtros dimensionais.
- Notas Fiscais possuía fallbacks equivalentes e campos `productId`, `serviceId` e `businessUnitId`. O domínio fiscal não possuía catálogo próprio.
- Rateios já modelava destinos `corporate`, `product`, `service` e `business_unit`, com resolver injetável. Os fallbacks de catálogo eram temporários; `corporate` é e continua sendo dimensão própria.
- Contratos já possuía referências e resolver injetável para Produto, Serviço e Unidade. Templates/Variáveis usam esse resolver; não existia catálogo jurídico próprio.
- Participações e Repasses carregavam as mesmas dimensões como referências/snapshots. Nenhum deles é owner do cadastro.
- Os módulos legados de referência contêm labels históricos de serviços, sistemas e P&L por projeto. Esses textos foram classificados como labels/mocks/legado incompatível e NÃO foram convertidos automaticamente em entidades canônicas.
- `Projeto` permanece conceito distinto de Produto, Serviço e Unidade. Nenhum módulo Projetos foi criado.
- `Sistema` é tratado como possível tipo/categoria comercial de Produto, não como uma quarta entidade canônica.
- Nenhum registro real como Music OS 360, Vivendo da Música, Dica de Cria ou Visa Fácil é criado automaticamente por esta etapa.

Labels legados sem ID forte podem ser registrados como `potential_catalog_reference` em `legacyBindings`; isso nunca cria Produto/Serviço/Unidade automaticamente.

## Fonte canônica

```text
state.crmBusinessCatalog
├── products
├── services
├── businessUnits
├── relationships
├── history
├── legacyBindings
└── metadata
```

O serviço expõe operações de criação/edição/arquivamento, lookup por ID, listagens read-only, paginação, resolução central de dimensão, verificação de referências e histórico.

## Produto

Produto é propriedade comercializável e pode representar SaaS, software, plataforma, aplicativo, assinatura, curso, produto digital, produto físico, licença ou outra solução. Não cria Receita, Transação, Nota Fiscal ou Contrato.

Campos principais: `id`, `code`, `name`, `slug`, `category`, `type`, `description`, `status`, `businessUnitId`, `ownerUserId`, `revenueModel`, `billingModel`, `currency`, `referencePrice`, `billingFrequency`, `launchDate`, `retirementDate`, `websiteUrl`, `internalReference`, `metadata`, `isDemo` e auditoria temporal.

`referencePrice = null` significa preço não informado. Zero explícito permanece zero.

Status: `draft`, `active`, `paused`, `retired`, `archived`.

Modelos de receita: `subscription`, `one_time`, `license`, `usage`, `commission`, `revenue_share`, `free`, `custom`. `revenue_share` é somente modelo comercial; não representa Participação Econômica.

Modelos de cobrança: `monthly`, `quarterly`, `annual`, `one_time`, `usage_based`, `custom`.

## Serviço

Serviço é catálogo do que a Valtren presta. Não é Contrato e não é Projeto.

Campos principais: `id`, `code`, `name`, `category`, `description`, `status`, `businessUnitId`, `ownerUserId`, `pricingModel`, `currency`, `referencePrice`, `billingFrequency`, `defaultDuration`, `metadata`, `isDemo` e auditoria temporal.

Modelos de preço são extensíveis dentro do enum operacional atual: `fixed`, `hourly`, `daily`, `project`, `retainer`, `usage`, `commission`, `free`, `custom`.

## Unidade de Negócio

Unidade de Negócio é agrupamento gerencial de Produtos e Serviços. Não é Departamento, Área ou Equipe; esses pertencem à Administração/Estrutura Organizacional.

Campos principais: `id`, `code`, `name`, `description`, `status`, `ownerUserId`, `parentBusinessUnitId`, `metadata`, `isDemo` e auditoria temporal. A hierarquia é opcional e ciclos são bloqueados.

## Integridade e códigos

Códigos automáticos seguem `PRD-001`, `SRV-001` e `BU-001`, incrementando de forma determinística sem colisão. Eles são códigos internos e nunca são apresentados como identificadores fiscais ou legais.

Prevenção de duplicidade:

- Produto: código, slug e nome normalizado + categoria;
- Serviço: código e nome normalizado;
- Unidade: código e nome normalizado.

Não existe auto-merge por nome parcial.

Entidades usadas historicamente são arquivadas em vez de destruídas. Exclusão física é permitida apenas para rascunho sem referência detectada.

## Feeds e resolução

Interfaces read-only:

```text
crmBusinessProductsFeed()
crmBusinessServicesFeed()
crmBusinessUnitsFeed()
```

Lookups:

```text
crmBusinessGetProduct(id)
crmBusinessGetService(id)
crmBusinessGetUnit(id)
crmBusinessResolveDimension(type, id)
crmBusinessDimensionLabel(type, id)
```

Demo é excluído por padrão. Referência inexistente é exibida como `Referência não resolvida` e não é convertida em entidade fake. `corporate` é resolvido como `Corporativo` fora do catálogo.

## Adapters mínimos

A etapa altera apenas lookup, validação de referência e resolução de labels nos owners concluídos:

- Transações: `Produto/Sistema` lê Produtos canônicos; `Corporativo` continua independente.
- Contabilidade: filtros de Produto, Serviço e Unidade leem o catálogo canônico; DRE não muda.
- Notas Fiscais: selects de Produto, Serviço e Unidade leem o catálogo canônico; domínio fiscal não muda.
- Rateios: destinos validam IDs canônicos; workflow/cálculo não muda.
- Contratos: resolver de Produto/Serviço/Unidade passa pelo catálogo; versionamento não muda.
- Templates/Variáveis: `PRODUTO.NOME`, `SERVICO.NOME` e `UNIDADE.NOME` usam o resolver contratual canônico; referência ausente continua pendente.
- Participações: somente label/lookup de dimensões muda; cálculo econômico permanece intacto.
- Repasses: somente label/lookup de dimensões muda; obrigação, pagamento e conciliação permanecem intactos.

## Ordem de materialização

Negócios é aplicado **depois de Repasses** nesta versão. Essa escolha é deliberada: os módulos anteriores já materializam seus helpers completos. Aplicar Negócios por último permite substituir somente os helpers finais de lookup/validação/label sem que um materializador posterior restaure os fallbacks antigos. As funções globais do catálogo ficam disponíveis no runtime do bundle independentemente da posição textual de declaração.

A ordem evita reorganizar arbitrariamente o pipeline consolidado e mantém todos os workflows/cálculos dos owners anteriores intocados.
