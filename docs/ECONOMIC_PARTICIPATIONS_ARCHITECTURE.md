# Financeiro → Participações — Arquitetura Canônica

## Responsabilidade

Participações é a camada canônica de **cálculo, memória, revisão e aprovação de direitos econômicos contratuais**.

A separação de ownership é obrigatória:

```text
Regra econômica / vigência / participante / base permitida
→ Jurídico → Contratos

Cálculo do valor devido e memória econômica
→ Financeiro → Participações

Pagamento / liquidação / conciliação / quitação
→ Financeiro → Repasses (fora desta etapa)

Propriedade societária / quotas
→ Jurídico → Societário (não é fonte automática de Participações)
```

Participações nunca cria percentual contratual próprio, não consulta quotas societárias para inferir direito econômico e não cria Transação, Nota Fiscal, Rateio ou Repasse.

## Fonte canônica

O estado operacional é `state.crmEconomicParticipations`, operado por `ValtrenParticipationCore.createService()`.

Coleções:

- `calculations`: cabeçalho e lifecycle do cálculo;
- `calculationSegments`: trechos de vigência contratual efetivamente usados;
- `baseComponents`: memória rastreável dos componentes da base;
- `deductions`: deduções permitidas pelo contrato e sua origem;
- `approvals`: eventos de submissão/aprovação/rejeição;
- `history`: trilha operacional;
- `sourceSnapshots`: memória determinística das fontes + hashes;
- `legacyBindings`: reservado para compatibilidade explícita, sem migração semântica automática.

## Dependências read-only

A ordem de materialização e dependência é:

```text
Arquitetura definitiva
↓
CRM / Pessoas e Organizações
↓
Transações
↓
Contabilidade
↓
Notas Fiscais
↓
Rateios
↓
Contratos
↓
Participações
```

Participações consome:

- `crmContractEconomicRulesFeed()` e `crmContractResolveEconomicRuleForPeriod()`;
- `crmAccountingService()` como agregador econômico principal;
- `crmFiscalService().accountingFeed()` somente para deduções fiscais explicitamente autorizadas;
- `crmCostAllocationService().accountingProjection()` somente para Rateios postados e consistentes quando contratualmente elegíveis;
- `crmCanonicalPartyService()` para Person/Organization.

Não há segunda DRE nem cópia de `state.crmFinancialTransactions`, `state.crmAccounting`, `state.crmFiscalDocuments` ou `state.crmCostAllocations`.

## Identidade do cálculo

Um cálculo preserva, no mínimo:

- `contractId`, `contractNumber`;
- `contractVersionId`, `contractVersionNumber`;
- `economicRuleId`;
- `participantPartyType`, `participantPartyId`;
- `periodStart`, `periodEnd`;
- `basisType`, `ruleType`, percentual/valor fixo quando aplicável;
- dimensões (`productId`, `serviceId`, `businessUnitId`);
- `calculationBase`, `deductionsTotal`, `distributableBase`, `participationAmount`;
- `currency`;
- `workflowStatus`, `calculationStatus`, `consistencyStatus`;
- `sourceSnapshotHash`, `ruleSnapshotHash`;
- revisão e relação de substituição.

## Resolução por período e segmentação

A família de obrigação é resolvida por Contrato + participante + base + dimensão + moeda. Os limites de vigência de todas as regras históricas elegíveis formam os segmentos.

Exemplo:

```text
01/06 → 30/06  · Versão 1 · 20%
01/07 → 31/07  · Versão 2 · 25%
```

Cada segmento resolve e calcula sua própria base econômica. O valor agregado é a soma dos segmentos; não é usada média de percentuais.

Se o mesmo segmento possuir mais de uma regra incompatível da mesma família:

```text
calculationStatus = blocked
consistencyStatus = conflict
message = "Conflito contratual de vigência."
```

Uma lacuna de vigência também bloqueia o cálculo do período integral.

## Bases econômicas

### `gross_revenue`

Usa Receita Bruta do domínio de Contabilidade no período/dimensão/regime aplicável. Transferências, pendentes, excluídos e demo não são receita oficial; estornos/chargebacks seguem a semântica canônica da Contabilidade.

### `net_revenue`

Usa Receita Líquida do domínio de Contabilidade. Deduções já incorporadas à Receita Líquida são marcadas como `alreadyIncludedInBase` quando também aparecem como permissões contratuais, impedindo dedução dupla.

### `product_result`

Usa `buildDre()` filtrado pelo `productId` contratual e consome o Resultado Final dimensional. Rateios efetivos entram exatamente como já entram na Contabilidade.

### `service_result`

Usa `buildDre()` filtrado pelo `serviceId` contratual e consome o Resultado Final dimensional.

### `distributable_base`

Exige `rule.metadata.baseSource` explícito, com origem formal entre `gross_revenue`, `net_revenue`, `product_result` ou `service_result`. Ausência de origem bloqueia; não há default silencioso.

### `custom_reference`

Só calcula quando um `customBaseResolver` formal e determinístico é fornecido. Sem resolver:

```text
Base personalizada requer configuração explícita.
```

## Regime contábil

Quando `rule.metadata.accountingBasis` define `cash` ou `accrual`, a regra é obedecida. Na ausência, Participações utiliza a política documentada `accrual` (competência) e registra esse regime na memória de cada componente.

## Deduções

Somente `rule.deductions` autoriza deduções. A normalização reconhece semanticamente impostos/tributos, custos, comissões, taxas e Rateios.

Cada dedução preserva:

- tipo;
- origem (`transaction`, `fiscal_document`, `cost_allocation` etc.);
- `sourceId`;
- descrição;
- valor observado;
- valor efetivamente aplicado;
- permissão contratual;
- período e moeda;
- metadata de rastreabilidade.

### Double counting

A memória utiliza `sourceKey`/`economicKey` para impedir a mesma origem econômica de ser aplicada duas vezes.

Casos protegidos:

- `net_revenue` já contém deduções contábeis — a mesma dedução não é subtraída novamente;
- `product_result`/`service_result` já contêm custos do resultado — o mesmo custo não é subtraído novamente;
- imposto fiscal vinculado a uma transação contábil de tributo não é duplicado;
- custo original e sua projeção de Rateio representam uma única origem econômica para a dimensão.

Rateio `reversed` não é consumido. Rateio `posted` com inconsistência necessária ao cálculo bloqueia/requer revisão.

## Regras

### `percentage`

Usa aritmética monetária em centavos inteiros:

```text
participationAmount = distributableBase × percentage
```

### `fixed`

Executa quando `fixedValue` é determinístico. Se a regra for mensal e o intervalo for parcial, exige `prorationPolicy` explícita. Não existe prorrata implícita.

### `tiered`

Exige `metadata.tiers` completos, válidos e não ambíguos. Ausência, lacunas ou sobreposição bloqueiam.

### `custom`

Exige `customRuleResolver` formal. Nenhum código arbitrário armazenado no contrato é executado.

## Moeda

Não existe conversão cambial implícita. Se componentes relevantes tiverem moeda divergente da regra, o cálculo é bloqueado.

## Workflow e consistência

Workflow humano:

```text
draft → review → approved
               ↘ rejected
approved → nova revisão → approved
                         ↳ anterior = superseded
```

Status matemático:

```text
pending | calculated | blocked
```

Consistência:

```text
consistent | source_changed | rule_changed | conflict | needs_review
```

Uma aprovação não é reescrita quando uma fonte muda. `refreshConsistency()` compara o snapshot atual com os hashes congelados e altera apenas o status de consistência/trilha. Para mudar o valor, cria-se nova revisão.

## Snapshots e hashes

A memória persistida contém:

- snapshots das regras usadas por segmento;
- componentes da base;
- deduções;
- IDs/valores/origens suficientes para reconstrução operacional;
- snapshot do participante;
- `sourceSnapshotHash` e `ruleSnapshotHash` determinísticos.

Os hashes usam serialização estável + FNV-1a 32 como detector determinístico de alteração. Não são assinatura criptográfica e não pretendem substituir trilha de auditoria externa.

## Feed futuro para Repasses

`crmParticipationObligationsFeed()` é read-only e expõe apenas Participações:

- `approved`;
- `consistent`;
- não demo;
- não substituídas.

O feed inclui cálculo, contrato/versão/regra, participante, período, moeda, `amountDue`, dimensões, aprovação e hash. `dueDate` permanece `null` sem prazo formal já resolvido.

A chamada do feed não cria Repasse, Transação, pagamento ou conta a pagar.

## Legado e demo

Percentuais de Dashboard, Produto, Projeto, “Sócio”, `revenueShares` e equivalentes não são convertidos em obrigação contratual. O migrador conservador classifica registros sem rastreabilidade suficiente como incompatíveis e, mesmo quando há IDs aparentes, exige recálculo explícito pela regra canônica.

Registros `isDemo` não entram nas consultas reais nem no feed para Repasses.

## Escopo excluído

Nesta etapa não são implementados:

- Financeiro → Repasses;
- pagamento/liquidação/conciliação;
- dados bancários de participante;
- contas a pagar derivadas;
- Societário;
- novas regras em Contratos;
- qualquer segundo ledger/DRE.
