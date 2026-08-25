# Jurídico → Contratos — arquitetura canônica

## Escopo

Esta etapa implementa exclusivamente `Jurídico → Contratos`, com as áreas internas `Contratos`, `Templates` e `Variáveis`. Assuntos Jurídicos, Compliance e Políticas, Propriedade Intelectual e Societário permanecem placeholders. Financeiro → Participações e Financeiro → Repasses permanecem não implementados.

A regra de ownership é preservada: Contrato pertence ao Jurídico; identidade de Pessoas/Organizações continua na infraestrutura canônica; Produto/Serviço/Unidade pertencem a Negócios; Transações, Notas Fiscais, Rateios, Participações e Repasses pertencem ao Financeiro.

## Fonte única

A fonte contratual é `state.crmLegalContracts`, operada por `ValtrenContractCore.createService()`.

Estrutura:

```text
crmLegalContracts
├── contracts
├── versions
├── parties
├── clauses
├── economicRules
├── approvals
├── signatures
├── attachments
├── history
├── templates
├── templateVersions
├── variables
├── legacyBindings
└── metadata
```

Não existem bases paralelas de clientes, participantes, signatários ou contratos.

## Contract e ContractVersion

`Contract` representa identidade e ciclo de vida. Contém número interno/manual, nome, tipo, categoria, status, responsáveis, vigência, moeda, valor de referência, cliente canônico, referências a Produto/Serviço/Unidade, Template de origem e IDs das versões vigente/mais recente.

`ContractVersion` representa a redação jurídica em um momento. Contém versão, status, título, conteúdo, vigência, moeda/valor de referência, referência imutável ao Template/TemplateVersion usado, snapshot, workflow e cadeia de supersessão.

Status do Contrato:

```text
draft → negotiation → active → suspended / expired / terminated / archived
```

Status da Versão:

```text
draft → review → approved → signed
                 ↘ rejected
approved/signed → superseded por nova versão
```

Somente versões `draft` podem ser editadas. Versões aprovadas, assinadas, rejeitadas ou substituídas nunca são sobrescritas; alterações exigem uma nova versão.

## Partes e signatários

Partes referenciam `Person` ou `Organization` da infraestrutura canônica. Um papel contratual é uma relação da versão e não uma identidade independente. Para uma Organização, o signatário é uma `Person` canônica vinculada à Organização. O domínio bloqueia signatários sem vínculo real.

Snapshots de aprovação/assinatura preservam nome, documento, endereço, contatos e signatário efetivamente utilizados naquela versão, sem virar uma segunda fonte de identidade.

## Dados institucionais

Variáveis `EMPRESA.*` são resolvidas por um provider de Configurações → Empresa. O módulo não hardcode razão social, CNPJ, endereço ou representante. Quando dados obrigatórios não estão disponíveis, a aprovação é bloqueada e a UI orienta: `Dados institucionais incompletos. Configure em Configurações → Empresa.`

## Produto, Serviço e Unidade

São somente referências estáveis. O browser consulta fontes estruturadas já existentes e não inventa catálogo. IDs não vazios são validados antes de persistir.

## Templates

Template possui identidade e versões. Uma versão ativa de Template é imutável. Alterações relevantes criam uma nova versão. Ao criar um Contrato a partir de Template, conteúdo e `templateVersionId` são copiados para a versão contratual; mudanças futuras do Template não afetam contratos existentes.

Status do Template: `draft`, `active`, `archived`. Status de versão: `draft`, `active`, `superseded`.

## Variáveis

Existe um registry central. As variáveis internas iniciais incluem:

```text
EMPRESA.RAZAO_SOCIAL
EMPRESA.CNPJ
EMPRESA.ENDERECO
CLIENTE.NOME
CLIENTE.DOCUMENTO
CONTRATO.NUMERO
CONTRATO.VALOR
CONTRATO.INICIO
CONTRATO.FIM
PRODUTO.NOME
SERVICO.NOME
UNIDADE.NOME
```

Uma variável registra chave, label, descrição, escopo, tipo, resolver semântico, obrigatoriedade, status, origem e política de fallback. Na UI não são expostos IDs internos, resolver path ou metadata JSON.

Variáveis obrigatórias não resolvidas nunca viram `undefined`, `null` ou `-`. O conteúdo mostra `Variável pendente: {{CHAVE}}`; a aprovação é bloqueada quando a variável obrigatória necessária não puder ser resolvida. Na aprovação/assinatura, os valores resolvidos são congelados no snapshot.

## Preview A4

O core gera um modelo de preview com página A4 (210 × 297 mm), margens, cabeçalho, conteúdo, cláusulas, rodapé, valores resolvidos e pendências. O browser renderiza preview interno A4. Não há declaração de PDF jurídico assinado ou assinatura digital sem provedor real.

## Aprovação e assinatura

O workflow mínimo é `Rascunho → Revisão → Aprovado`, com rejeição/devolução registrada. Aprovação grava ator, data, versão e snapshot. Assinaturas possuem signatário canônico, status, provider, referência externa opcional e data. Sem integração externa, o único comportamento operacional é registro manual explícito; nunca se declara assinatura digital fictícia.

Contrato só passa a `active` quando uma versão aprovada é efetivamente marcada como assinada segundo as assinaturas requeridas.

## Regras econômicas

Regras econômicas pertencem a `ContractVersion` e são cláusulas estruturadas para consumo futuro por Financeiro → Participações. Campos principais:

```text
contractVersionId
participantPartyType
participantPartyId
type
percentage / fixedValue
basisType
deductions[]
effectiveFrom
effectiveUntil
productId
serviceId
businessUnitId
currency
```

Participante é `Person` ou `Organization` canônica. Participante econômico não é sinônimo de sócio e o domínio não consulta Societário.

Bases reconhecidas semanticamente:

```text
gross_revenue
net_revenue
distributable_base
product_result
service_result
custom_reference
```

Deduções registram apenas o que o contrato permite (por exemplo impostos, custos elegíveis, comissões ou rateios elegíveis). Nenhum valor é calculado nesta etapa. Percentuais precisam ser finitos, maiores que zero e no máximo 100%. A soma global das regras não é forçada a 100%, porque a Valtren pode reter a parcela restante.

## Feed para Participações

`crmContractEconomicRulesFeed()` é read-only e expõe somente dados contratuais necessários a uma futura implementação de Participações:

```text
contractId
contractNumber
versionId
versionNumber
ruleId
participantPartyType
participantPartyId
basisType
type
percentage
fixedValue
deductions
effectiveFrom
effectiveUntil
productId
serviceId
businessUnitId
currency
```

Não existe `amount`, `calculatedAmount`, `participationId`, `payoutId` ou pagamento.

O feed atual considera versões aprovadas/assinadas e, quando consultado historicamente, versões superseded em sua janela de vigência. Draft e rejected nunca entram. Contratos demo nunca entram.

`resolveEconomicRuleForPeriod()` retorna `resolved`, `none` ou `conflict`. Uma ambiguidade temporal nunca é resolvida silenciosamente. Nova versão com supersessão explícita encerra historicamente a janela da versão anterior na véspera da nova vigência.

## Legado

Não havia domínio contratual canônico anterior. Referências antigas encontradas em formulários financeiros e automações removidas são campos/protótipos ambíguos e não são promovidos a Contrato.

A migração conservadora só aceita registros explicitamente identificados como contrato (`entityType/kind/recordType = contract` ou `isContract = true`) e com evidência mínima. Propostas, documentos genéricos e textos demo ambíguos são apenas registrados como `legacySkipped`. Bindings preservam IDs legados quando uma migração segura ocorre.

## Regras de não duplicação

Criar/aprovar/assinar Contrato não cria Transação, Receita, Conta a Receber, Nota Fiscal, Participação nem Repasse. Valor contratual é condição jurídica, não movimentação financeira.

## Materialização

A sequência canônica termina em:

```text
Arquitetura definitiva
→ CRM
→ Transações
→ Contabilidade
→ Notas Fiscais
→ Rateios
→ Contratos
```

O materializador de Contratos substitui somente os três placeholders de `Contratos`, `Templates` e `Variáveis`; valida que os demais módulos Jurídicos permanecem placeholders, que Participações/Repasses permanecem placeholders e que o stack Financeiro continua canônico.
