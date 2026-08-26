# Jurídico → Contratos — arquitetura canônica

## Escopo atual

`Jurídico → Contratos` continua sendo o owner exclusivo de `Contratos`, `Templates` e `Variáveis`. Esta etapa não refatora funcionalmente esse domínio.

O Jurídico completo agora está distribuído em owners separados:

```text
Jurídico
├── Assuntos Jurídicos
├── Contratos
│   ├── Contratos
│   ├── Templates
│   └── Variáveis
├── Compliance e Políticas
├── Propriedade Intelectual
└── Societário
```

As quatro áreas externas a Contratos possuem fontes canônicas próprias e não compartilham uma lista jurídica genérica. Financeiro → Participações e Financeiro → Repasses também estão implementados como owners financeiros independentes.

## Ownership de Contratos

A fonte contratual é `state.crmLegalContracts`, operada por `ValtrenContractCore.createService()`.

Estrutura principal:

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

Identidade de Pessoas/Organizações continua na infraestrutura canônica. Produto/Serviço/Unidade pertencem a Negócios. Transações, Notas Fiscais, Rateios, Participações e Repasses pertencem ao Financeiro. Contratos não duplica nenhum desses owners.

## Contract e ContractVersion

`Contract` representa identidade e ciclo de vida. `ContractVersion` representa a redação jurídica em um momento. Versões aprovadas, assinadas, rejeitadas ou substituídas não são sobrescritas; alterações exigem nova versão.

Partes referenciam `Person` ou `Organization` canônicas. Para uma Organization, signatário é uma `Person` canônica vinculada. Snapshots históricos preservam os dados usados naquela versão sem virar uma nova fonte de identidade.

## Dados institucionais

Variáveis `EMPRESA.*` são resolvidas pelo provider de Configurações → Empresa. O módulo não hardcode razão social, CNPJ, endereço ou representante. Dados obrigatórios ausentes bloqueiam aprovação quando necessários.

## Produto, Serviço e Unidade

São somente referências estáveis ao owner Negócios. IDs não vazios são validados antes de persistir. Contratos não mantém catálogo paralelo.

## Templates e Variáveis

Template possui identidade e versões. Versão ativa é imutável. Um Contrato criado de Template guarda a versão utilizada; mudanças futuras no Template não alteram o Contrato existente.

O registry de Variáveis inclui referências institucionais, de cliente, contrato e Negócios, incluindo:

```text
EMPRESA.RAZAO_SOCIAL
EMPRESA.CNPJ
CLIENTE.NOME
CLIENTE.DOCUMENTO
CONTRATO.NUMERO
CONTRATO.VALOR
PRODUTO.NOME
SERVICO.NOME
UNIDADE.NOME
```

Variáveis obrigatórias pendentes são explicitadas e valores usados em aprovação/assinatura são congelados no snapshot.

## Aprovação, assinatura e Preview A4

O workflow de versão mantém revisão/aprovação/rejeição, histórico e imutabilidade. Sem integração externa validada, assinatura é somente registro manual explícito. O Preview A4 é interno e não representa PDF jurídico assinado.

## Regras econômicas

Regras econômicas pertencem a `ContractVersion` e alimentam Financeiro → Participações por interface read-only. Participante econômico é `Person` ou `Organization` canônica e **não é sinônimo de sócio**.

Contratos não consulta Societário para inferir percentuais. `shareholder.percentage` ou `holding.percentage` nunca substituem `economicRule.percentage`.

O feed `crmContractEconomicRulesFeed()` e o resolver `crmContractResolveEconomicRuleForPeriod()` expõem somente cláusulas/regras contratuais e rastreabilidade. O cálculo monetário continua em Participações; liquidação continua em Repasses.

## Regras de não duplicação

Criar, aprovar ou assinar Contrato não cria automaticamente Transação, Receita, Nota Fiscal, Participação ou Repasse. Valor contratual é condição jurídica, não movimento financeiro.

## Materialização atual

A ordem relevante é:

```text
Arquitetura definitiva
→ CRM
→ Transações
→ Contabilidade
→ Notas Fiscais
→ Rateios
→ Contratos
→ Participações
→ Repasses
→ Negócios
→ Assuntos Jurídicos
→ Compliance e Políticas
→ Propriedade Intelectual
→ Societário
```

O materializador de Contratos continua substituindo somente as três rotas de `Contratos`, `Templates` e `Variáveis`. Os demais owners Jurídicos são materializados posteriormente e não alteram o domínio contratual.

A arquitetura detalhada dos quatro owners jurídicos restantes está em `docs/LEGAL_REMAINING_DOMAINS_ARCHITECTURE.md`.
