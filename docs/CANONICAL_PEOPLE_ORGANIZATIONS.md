# Infraestrutura Canônica de Pessoas e Organizações

## Objetivo

Esta infraestrutura estabelece uma fonte única de identidade para pessoas físicas e organizações do Sistema Interno da Valtren. Ela não cria módulo, página ou item de sidebar. Os módulos funcionais devem referenciar estas entidades e atribuir papéis/vínculos, em vez de manter cadastros independentes de cliente, fornecedor, parceiro, beneficiário, parte contratual, colaborador etc.

## Estado técnico do projeto

O projeto atual é uma aplicação estática materializada em `app.js`. Não existe banco de dados operacional, ORM, migrations SQL, API backend, repository ou service server-side. CRM e Agenda utilizam estado JavaScript em memória.

Por isso, esta etapa implementa a camada canônica no stack atual e uma migration/compatibility layer de runtime para os dados legados. Uma futura persistência deverá refletir o mesmo modelo no backend sem recriar cadastros por domínio.

## Modelo canônico

A store `state.crmCanonicalParties` possui `schemaVersion: 1` e as coleções:

- `people`: Pessoas canônicas;
- `organizations`: Organizações canônicas;
- `roles`: papéis atribuídos a Pessoa ou Organização;
- `personOrganizationRelationships`: vínculos Pessoa ↔ Organização;
- `contactPoints`: e-mails, telefones, WhatsApp, sites e demais canais;
- `addresses`: endereços relacionados à entidade;
- `documents`: CPF, CNPJ e outros identificadores;
- `userLinks`: relação explícita opcional entre Pessoa e Usuário do Sistema;
- `history`: trilha técnica de criação, atualização, papéis e vínculos;
- `legacyBindings`: aliases entre IDs legados e IDs canônicos;
- `potentialDuplicates`: sinais de possíveis duplicidades que não foram unificadas automaticamente.

## Pessoa

`Person`/Pessoa representa uma pessoa física independentemente de qualquer função de domínio.

Campos centrais incluem ID estável, nome, status, tags, metadados e timestamps/auditoria. CPF, e-mail, telefone e endereço ficam em estruturas normalizadas relacionadas à Pessoa.

Uma Pessoa não é automaticamente:

- Usuário do sistema;
- Colaborador;
- Lead;
- Cliente;
- Parceiro;
- Contato de empresa.

Esses conceitos são vínculos, papéis ou entidades de domínio que referenciam `person_id`.

## Organização

`Organization`/Organização representa uma pessoa jurídica ou outra organização. Possui ID estável, razão social, nome fantasia, tipo organizacional, segmento, status, tags, metadados e timestamps.

CNPJ não é obrigatório. Organizações estrangeiras ou registros sem CNPJ podem existir normalmente. Outros documentos podem ser adicionados através da coleção `documents`.

Organização não é sinônimo de Cliente. Uma única organização pode receber simultaneamente papéis como:

```text
Organização: Empresa ABC
├── Cliente
├── Fornecedor
├── Parceiro
├── Parte contratual
└── Beneficiário
```

## Papéis

Papéis são registros separados em `roles`, vinculados por `entityType + entityId`.

A atribuição é idempotente: atribuir o mesmo papel novamente não cria outra entidade nem outro papel ativo.

A infraestrutura reconhece aliases para papéis como:

- Cliente → `customer`;
- Lead → `lead`;
- Prospect → `prospect`;
- Fornecedor → `supplier`;
- Parceiro → `partner`;
- Prestador → `service_provider`;
- Beneficiário → `beneficiary`;
- Participante econômico → `economic_participant`;
- Parte contratual → `contractual_party`;
- Contato de empresa → `organization_contact`;
- Responsável → `responsible`.

Os módulos futuros podem adicionar papéis sem transformar esses papéis em novas bases concorrentes.

## Contatos de Organizações

O vínculo `personOrganizationRelationships` conecta uma Pessoa canônica a uma Organização canônica e carrega apenas informações específicas da relação, como:

- cargo/função naquela organização;
- departamento;
- contato principal;
- responsável financeiro;
- responsável jurídico;
- observações;
- status;
- metadados.

Os dados pessoais não são copiados para a Organização.

## Pessoa ≠ Usuário

`userLinks` existe exclusivamente para relacionar opcionalmente um Usuário do Sistema a uma Pessoa. Criar Pessoa nunca cria Usuário automaticamente.

A gestão de login, papéis de acesso, MFA e sessões continua pertencendo a `Configurações → Usuários`.

## Pessoa ≠ Colaborador

Colaborador será futuramente um vínculo profissional do RH que referencia uma Pessoa por ID. Cargo e dados trabalhistas não fazem parte da entidade Pessoa.

Exemplo futuro:

```text
Pessoa: Maria Silva
Employment/Colaborador: person_id = <ID da Maria>
```

## Organização ≠ Cliente

Cliente é um papel comercial. Fornecedor é um papel comercial/financeiro. Beneficiário é um papel econômico. Parte contratual é um papel/relação jurídica. Todos referenciam a mesma Pessoa ou Organização canônica quando se trata do mesmo sujeito.

## Identificadores e normalização

- CPF e CNPJ são armazenados com valor original e `normalizedValue` somente alfanumérico;
- a máscara é responsabilidade da interface;
- CPF e CNPJ novos são validados antes de serem aceitos;
- documentos legados inválidos não são descartados: são migrados com `validationStatus = legacy-unverified`;
- documentos podem ser ausentes;
- documentos de outros países/tipos podem usar `documents` sem forçar CPF/CNPJ;
- um mesmo CPF/CNPJ normalizado não pode ser vinculado a duas entidades diferentes.

## Matching e deduplicação

Não existe merge por similaridade/fuzzy name.

### Pessoa

Match automático forte ocorre somente quando há:

- mesmo CPF; ou
- mesmo e-mail + mesmo nome exato normalizado; ou
- mesmo telefone + mesmo nome exato normalizado.

Nome idêntico isoladamente é apenas sinal de possível duplicidade e não gera merge automático.

### Organização

Match automático forte ocorre por:

- mesmo CNPJ; ou
- mesmo domínio + mesmo nome legal/fantasia exato.

Na migration legada existe compatibilidade controlada de nome exato para referências de empresa que não possuem CNPJ/domínio. Nomes apenas parecidos não são unidos.

Sinais insuficientes são registrados em `potentialDuplicates` para análise futura.

## Camada de serviço

`ValtrenPartyCore.createService()` centraliza:

- `createPerson` / `updatePerson`;
- `createOrganization` / `updateOrganization`;
- `assignRole` / `removeRole` / `getRoles`;
- `linkPersonOrganization` / `getOrganizationContacts`;
- `linkUser`;
- `addDocument`;
- `addContactPoint`;
- `setPrimaryAddress`;
- `detectPotentialDuplicates`;
- `findStrongMatch`.

Não devem ser criadas futuramente bases paralelas com funções do tipo `createCustomer`, `createSupplier` ou `createPartner` que dupliquem identidade. Esses domínios devem criar/obter a entidade canônica e atribuir o papel correspondente.

## Compatibilidade com CRM existente

Os arrays legados `state.crmRelContacts` e `state.crmRelLeads` continuam disponíveis como projeções compatíveis para evitar regressão no CRM e na Agenda.

A fonte de identidade passa a ser `state.crmCanonicalParties`.

A migration de runtime:

1. lê os registros atuais de `crmRelContacts` e `crmRelLeads`;
2. cria/reutiliza Pessoa ou Organização canônica;
3. normaliza documentos, canais e endereços;
4. cria papéis e vínculos;
5. cria `legacyBindings` preservando IDs como `c1`, `l1` etc.;
6. projeta novamente os arrays legados com os mesmos IDs e adiciona `canonicalEntityId`/`canonicalEntityType` para transição futura.

Cadastros novos/editados pelo CRM passam pelo adapter canônico. Exclusão de um registro do CRM remove o binding/papel daquele contexto, mas não apaga indiscriminadamente a Pessoa/Organização canônica, evitando perda de relacionamentos de outros domínios.

## Preservação histórica

Entidades, papéis e vínculos armazenam timestamps e IDs de ator quando disponíveis. A coleção `history` registra operações importantes. O snapshot legado é mantido na compatibility layer para evitar perda de informação durante a migração desta arquitetura estática.

Isso prepara a estrutura para a futura aba de Auditoria sem implementar o módulo de Auditoria nesta etapa.

## Persistência e migrations de banco

Nenhuma migration SQL foi criada porque o repositório não possui banco de dados ou schema persistente nesta versão. A migration criada é a migration de runtime `crmCanonicalEnsureFromLegacy()` aplicada durante o uso do bundle materializado.

Quando um backend for introduzido, o schema relacional recomendado deve refletir estas relações conceituais sem duplicar dados por módulo:

```text
people
organizations
entity_roles
person_organization_relationships
contact_points
addresses
documents
user_person_links
history/audit_events
legacy_bindings (temporário durante migração)
```

A migration futura deverá preservar os IDs canônicos ou mapear explicitamente os aliases legados.
