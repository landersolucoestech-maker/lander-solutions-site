# Financeiro → Repasses — arquitetura canônica

## Responsabilidade

`Financeiro → Repasses` transforma exclusivamente obrigações oriundas de Participações Econômicas aprovadas em um processo operacional de liquidação. O domínio não recalcula a Participação, não redefine percentuais, não consulta Societário e não cria movimentação bancária duplicada.

Fluxo canônico:

```text
Contrato / Versão / Regra Econômica
→ Financeiro / Participações (cálculo e aprovação)
→ crmParticipationObligationsFeed()
→ Financeiro / Repasses (obrigação e liquidação)
→ Financeiro / Transações (movimentação efetiva)
→ conciliação
```

Separação obrigatória:

```text
Rateio ≠ Participação Econômica ≠ Repasse ≠ Societário
```

## Fonte de verdade

O estado do domínio é `state.crmPayouts`, operado por `ValtrenPayoutCore.createService()`.

Coleções:

- `obligations`: obrigação operacional derivada de uma Participação aprovada;
- `payments`: vínculos de liquidação com Transações canônicas existentes;
- `transactionLinks`: relações entre obrigação/pagamento e movimentação financeira;
- `reconciliation`: eventos de conciliação/desconciliação;
- `history`: histórico operacional;
- `sourceSnapshots`: snapshot da Participação que originou a obrigação;
- `legacyBindings`: registros conservadores de legado identificável;
- `metadata`: versão e controles internos.

`amountPaid` e `openBalance` são derivados das liquidações válidas; não constituem segunda fonte financeira concorrente.

## Nascimento e sincronização da obrigação

A única fonte elegível é `crmParticipationObligationsFeed()`, que já expõe Participações `approved`, consistentes, não demo e não superseded. `participationCalculationId` é a chave forte para sincronização idempotente.

Sincronizar repetidamente a mesma Participação preserva uma única obrigação. O snapshot preserva contrato, versão, regra, participante, período, moeda, valor devido, aprovação e `sourceSnapshotHash`.

`dueDate` é copiado somente quando a origem oferece uma data determinística. Ausência de prazo permanece `null`; o domínio não inventa D+30 ou política semelhante.

## Participante

O beneficiário é a mesma `Person` ou `Organization` canônica da Participação. Repasses não mantém cadastro paralelo de beneficiários, parceiros, sócios ou fornecedores financeiros. Dados bancários não são simulados quando não existe owner canônico para eles.

## Obrigação e pagamento são entidades distintas

A obrigação preserva o direito aprovado. O pagamento representa apenas uma liquidação vinculada a uma Transação existente.

Uma obrigação de 10.000 pode possuir duas liquidações de 4.000 e 6.000 sem alterar `amountDue`. O saldo aberto é derivado do efeito líquido das liquidações válidas.

## Owner da movimentação financeira

Movimentações pertencem a `Financeiro → Transações`. Repasses nunca chama `createTransaction()` para registrar pagamento. O fluxo de vínculo seleciona uma Transação existente e cria somente a relação de match/settlement.

Para liquidação normal, a movimentação deve ser `posted`, `outflow`, não demo, não transferência e na mesma moeda da obrigação. Contraparte canônica incompatível bloqueia o vínculo. Sugestões de match nunca são aplicadas automaticamente apenas por igualdade de valor.

## Pagamentos parciais, integrais e sobrepagamento

- parcial: `amountPaid < amountDue`, status derivado `partial`;
- integral: `openBalance = 0`, status derivado `paid`;
- sobrepagamento: bloqueado enquanto não existir um domínio explícito de crédito/adiantamento.

Quitação e conciliação são conceitos separados. Uma obrigação pode estar quitada e ainda não reconciliada.

## Reversões

`refund`, `reversal`, `chargeback` e `reimbursement` relacionados à Transação de pagamento reduzem a liquidação pelo efeito líquido. Transferências internas não liquidam Repasse. Alterações de reversão preservam o pagamento e seu histórico; não apagam a obrigação.

## Conciliação

A conciliação referencia pagamento e Transação existentes e registra usuário/data/valor. Múltiplos pagamentos podem ter estados de conciliação diferentes, resultando em `unreconciled`, `partially_reconciled` ou `reconciled` sem mudar o valor originalmente devido.

## Participação substituída

Se a Participação original for superseded, a obrigação antiga permanece histórica. Sem pagamentos ela pode ser marcada como `superseded`; com pagamentos, a inconsistência é explicitamente sinalizada e nenhum pagamento é migrado silenciosamente para a nova obrigação. A nova Participação aprovada gera uma nova obrigação.

## Moeda e vencimento

Não há conversão cambial implícita. Moedas incompatíveis bloqueiam a liquidação. Vencimento é derivado de `dueDate` apenas quando existe e há saldo em aberto.

## Legado e demos

Nenhum registro legado ambíguo é convertido automaticamente sem `participationCalculationId` ou rastreabilidade equivalente. Participações demo não originam obrigações reais.

## O que Repasses não faz

- não calcula Participação Econômica;
- não define percentual econômico;
- não consulta quotas, equity ou Societário;
- não cria Transação bancária;
- não cria segunda despesa;
- não cria Contas a Pagar paralelas para o mesmo fato;
- não cria identidade de beneficiário;
- não simula dados bancários ou pagamentos reais.
