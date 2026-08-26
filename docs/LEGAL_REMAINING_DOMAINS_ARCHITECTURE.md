# Jurídico — domínios canônicos restantes

## Estado atual

Este documento é a referência técnica para as quatro áreas concluídas após Contratos. A arquitetura oficial do Jurídico permanece:

- Assuntos Jurídicos
- Contratos
  - Contratos
  - Templates
  - Variáveis
- Compliance e Políticas
- Propriedade Intelectual
- Societário

Contratos continua sendo um owner independente e não foi refatorado funcionalmente por esta etapa. Qualquer documentação anterior que descreva Assuntos Jurídicos, Compliance e Políticas, Propriedade Intelectual ou Societário como *placeholders* registra apenas o estado histórico anterior a esta implementação.

## Ownership

| Conceito | Owner |
| --- | --- |
| Pessoa / Organização | infraestrutura canônica de Pessoas/Organizações |
| Produto / Serviço / Unidade de Negócio | Negócios |
| Assunto jurídico operacional | Jurídico / Assuntos Jurídicos |
| Contrato, Template e Variável contratual | Jurídico / Contratos |
| Obrigação, controle, ocorrência e política de compliance | Jurídico / Compliance e Políticas |
| Ativo, registro e titularidade de propriedade intelectual | Jurídico / Propriedade Intelectual |
| Capital, posição societária, sócio e ato societário | Jurídico / Societário |
| Transação | Financeiro / Transações |
| Participação Econômica contratual | Financeiro / Participações |
| Repasse | Financeiro / Repasses |

A fronteira mais importante é obrigatória: **participação societária não é participação econômica**. Um sócio ou acionista não se torna participante econômico de contrato, um percentual de holding não vira percentual de regra econômica e um aporte societário não cria uma transação financeira.

## Assuntos Jurídicos

Fonte canônica: `state.crmLegalMatters`, operada por `ValtrenLegalMatterCore`.

Coleções separadas: `matters`, `parties`, `events`, `deadlines`, `actions`, `authorities`, `documents`, `settlements`, `history` e metadados/migração conservadora. As partes usam apenas `Person` ou `Organization` canônicas. Autoridades podem permanecer textuais/estruturadas quando não representam uma entidade de relacionamento.

O assunto suporta tipo extensível, status operacional interno, prioridade, risco, jurisdição/autoridade, responsável, exposição estimada, datas, vínculo opcional com Contrato e dimensões de Negócios. `estimatedExposure` é somente avaliação de risco e nunca cria despesa, lançamento contábil ou Transação. Acordo é evento jurídico; valor de acordo não gera pagamento.

Prazos possuem identidade própria e `crmLegalMatterDeadlinesFeed()` fornece projeção read-only adequada para consumo futuro pela Agenda. A Agenda não é modificada nesta etapa.

## Compliance e Políticas

Fonte canônica: `state.crmCompliance`, operada por `ValtrenComplianceCore`.

Coleções: `obligations`, `controls`, `occurrences`, `policies`, `policyVersions`, `evidence`, `reviews`, `history`. Nenhuma obrigação legal ou política é semeada automaticamente.

`Policy` e `PolicyVersion` são entidades distintas. O fluxo de versão é `draft → review → approved → active → superseded`; versões aprovadas/ativas/substituídas são imutáveis. Vigências e datas de revisão permanecem históricas. Evidências são metadata/referência quando não há storage persistente.

Ocorrências de compliance podem referenciar um Assunto Jurídico existente sem fundir os dois owners. Controles permanecem internos a Compliance.

`crmComplianceDeadlinesFeed()` projeta vencimentos/revisões read-only para futura Agenda.

## Propriedade Intelectual

Fonte canônica: `state.crmIntellectualProperty`, operada por `ValtrenIntellectualPropertyCore`.

Coleções: `assets`, `registrations`, `owners`, `licenses`, `deadlines`, `documents`, `history`. Tipos suportados são extensíveis (`trademark`, `patent`, `copyright`, `software`, `industrial_design`, `domain_related`, `other`).

Titularidade reutiliza `Person`/`Organization`. Produto, Serviço e Unidade são somente referências ao catálogo de Negócios. Status `registered` exige número de registro explícito; o sistema não simula integração com órgão registral.

Licenciamento jurídico de PI referencia `contractId`; Contratos continua sendo o owner das condições. Isso é diferente de licenças operacionais/administrativas, cujo owner permanece Administração / Patrimônio e Licenças.

Expiração, renovação e deadlines adicionais são projetados por `crmIntellectualPropertyDeadlinesFeed()` para futura Agenda, sem alterar Agenda nesta etapa.

## Societário

Fonte canônica: `state.crmCorporateGovernance`, operada por `ValtrenCorporateGovernanceCore`.

Coleções: `entities`, `capitalStructures`, `holdings`, `shareholders`, `administrators`, `contributions`, `corporateActs`, `resolutions`, `versions`, `documents`, `history`.

A entidade societária referencia uma `Organization` canônica; dados institucionais não são hardcoded. Sócios/acionistas e administradores usam `Person`/`Organization` canônicas conforme a semântica. Administrador societário não é papel de sistema nem cargo de RH.

Estruturas de capital são versionadas e têm vigência. Posições preservam instrumento, classe, quantidade, percentual e vigência. Soma de 100% só é exigida quando a própria estrutura declara `representationMode=percentage` e `integralRepresentation=true`; estruturas por quantidade, classes ou modelos mistos não recebem essa validação cegamente.

`resolveCorporateStructureAt(entityId, date)` retorna a estrutura histórica aplicável, `none` quando não há estrutura e `conflict` quando existem vigências concorrentes. Versões anteriores não são sobrescritas.

Capital autorizado, subscrito e integralizado são dados societários declarados. `contribution.financialEffect = none_automatic`: aporte prometido/subscrito/integralizado no registro societário não cria Transação. Uma referência futura a uma Transação existente pode ser registrada, sem criação de movimento.

O serviço expõe deliberadamente `economicParticipationFeed`, `payoutFeed` e `createFinancialTransaction` como ausentes. Não existe adapter de holding para Participações ou Repasses.

## Dados demo e legado

Todos os feeds reais excluem `isDemo=true` por padrão. Dados de teste só aparecem com `includeDemo=true` explícito.

A migração é conservadora. Registros ambíguos retornam `legacy_incompatible`; registros cujo domínio é explicitamente reconhecível retornam `legacy_review_required`. Nenhum registro real é criado automaticamente a partir de um label ambíguo.

## Materialização

Os quatro domínios são aplicados depois de Contratos, Participações, Repasses e Negócios. Essa ordem permite resolver referências canônicas sem reescrever os owners concluídos. Cada materializador substitui somente a rota reservada do seu domínio, valida o sidebar oficial, os owners anteriores e usa blocos/CSS marcados e idempotentes.

A pipeline executa suites de fonte e materializadas e verifica o SHA-256 do mesmo `app.js` antes/depois de cada suite materializada. `_site/app.js` precisa ter exatamente o SHA do bundle testado antes do upload do artifact.
