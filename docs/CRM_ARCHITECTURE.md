# CRM — Arquitetura funcional sobre Pessoas e Organizações canônicas

## Escopo

O CRM é um único módulo do Sistema Interno e possui exatamente cinco áreas internas:

```text
CRM
├── Contatos
├── Empresas
├── Clientes
├── Leads
└── Interações
```

Essas áreas são tabs internas da rota canônica `#/crm/relationships`. Nenhuma delas é item independente do sidebar.

## Fonte de verdade

Identidade nunca pertence ao CRM. A fonte canônica é:

```text
state.crmCanonicalParties
ValtrenPartyCore.createService()
```

O CRM mantém apenas contexto comercial em `state.crmDomain`, referenciando IDs canônicos.

### Person

Identidade de uma pessoa física. Nome, CPF, e-mail, telefone, WhatsApp, endereço e demais dados identitários são mantidos na infraestrutura canônica.

### Organization

Identidade de uma empresa/organização. Razão social, nome fantasia, CNPJ, contatos institucionais e endereço são mantidos na infraestrutura canônica.

### Contact

É uma visão/contexto CRM sobre `Person`. Não é entidade identitária independente.

### Company

É uma visão/contexto CRM sobre `Organization`. Não é uma segunda empresa.

### Customer

É o papel `customer` aplicado a `Person` ou `Organization`.

```text
Person + customer role       = Cliente PF
Organization + customer role = Cliente PJ
```

Não existe `CustomerIdentity` separado.

### Lead

É um contexto comercial que referencia uma Pessoa, uma Organização ou ambas. Origem, etapa, prioridade, responsável e interesses pertencem ao Lead; nome, documentos e contatos pertencem à identidade canônica.

### Interaction

É um evento de relacionamento que referencia IDs de Pessoa, Organização, Lead e/ou Cliente. A interação não copia a identidade relacionada.

## Papéis

Prospect, Parceiro, Fornecedor e Prestador não são módulos nem identidades. São papéis:

```text
prospect
partner
supplier
service_provider
```

Uma mesma Organização pode possuir vários papéis simultaneamente.

## Contexto CRM

`state.crmDomain.contexts` mantém somente informações específicas do CRM, como:

- responsável comercial;
- prioridade;
- origem;
- status do contexto;
- observações;
- tags;
- vínculo de compatibilidade legada;
- metadados do CRM.

## Contato ↔ Empresa

Pessoa e Organização são relacionadas por `personOrganizationRelationships`.

Cargo, função e departamento naquela empresa pertencem ao relacionamento, não à identidade global da Pessoa.

## Pipeline

O pipeline inicial possui exatamente cinco etapas internas estáveis:

```text
new        → Novo
contacted  → Em contato
qualified  → Qualificado
proposal   → Proposta
converted  → Convertido
```

Alterações de etapa geram histórico comercial e uma interação `stage_change`.

## Conversão Lead → Cliente

A conversão:

1. preserva Pessoa/Organização existentes;
2. preserva o Lead;
3. preserva origem, datas, histórico e interações;
4. mantém o papel `lead` para rastreabilidade;
5. atribui `customer` à identidade correspondente;
6. registra `lead.converted`;
7. marca o Lead como `converted`;
8. não cria nova identidade quando a identidade já existe.

Quando o Lead referencia Pessoa + Organização, a Organização é o alvo padrão de conversão. Quando referencia somente Pessoa, a Pessoa recebe o papel `customer`.

## Interações

Tipos iniciais:

```text
call                Ligação
email               E-mail
whatsapp            WhatsApp
meeting             Reunião
message             Mensagem
note                Anotação
stage_change        Mudança de etapa
follow_up           Follow-up
proposal            Proposta
commercial_activity Atividade comercial
```

Follow-up é apenas uma interação com data prevista e status; não substitui um sistema de tarefas.

## Projeções legadas

```text
state.crmRelContacts
state.crmRelLeads
```

continuam existindo somente como projeções de compatibilidade para consumidores legados, principalmente Agenda.

O CRM completo não realiza writes diretos nesses arrays. Atualizações passam por:

```text
crmCanonicalUpsertLegacyRecord()
crmCanonicalSyncLegacyViews()
```

A remoção de um contexto CRM não destrói automaticamente `Person` ou `Organization`.

## Dados de demonstração

Os seeds históricos do protótipo são marcados como demonstração e:

- não entram em KPIs reais;
- não aparecem por padrão;
- podem ser exibidos explicitamente pelo controle "Mostrar dados de demonstração";
- permanecem preservados para compatibilidade e inspeção.

## Persistência no stack atual

O projeto ainda é um bundle estático sem backend operacional. O CRM utiliza o estado canônico em memória e uma persistência local de navegador como adaptação provisória:

```text
valtren.crm.canonical-parties.v1
valtren.crm.domain.v1
```

Essa persistência não altera o modelo canônico e poderá ser substituída por repository/API quando o backend definitivo for implementado.

## Deep links

```text
#/crm/relationships?tab=contacts
#/crm/relationships?tab=companies
#/crm/relationships?tab=customers
#/crm/relationships?tab=leads
#/crm/relationships?tab=interactions
```

Refresh e navegação back/forward usam o próprio hash/query para restaurar a tab ativa.

## Ownership futuro

O CRM não se torna owner de dados de outros domínios:

```text
Contrato             → Jurídico
Transação             → Financeiro
Nota Fiscal           → Financeiro
Atendimento/Conversa  → ValtrenChat
Produto/Serviço       → Negócios
```

A visão de Cliente pode preparar estados vazios para essas integrações, mas não cria registros fictícios.
