# Valtren Solutions — Auditoria da Arquitetura Atual do Sistema Interno

**Escopo:** diagnóstico técnico, sem refatoração funcional.

**Baseline auditado:** branch `dev`, commit `db1ffb3acaa40b014b05f27930dded92c2c7e015`.

**Objetivo:** registrar o estado real do Sistema Interno da Valtren antes da implantação da arquitetura definitiva.

---

## 1. Arquitetura definitiva de referência

```text
DASHBOARD

CRM

AGENDA

FINANCEIRO
├── Transações
├── Contabilidade
├── Notas Fiscais
├── Rateios
├── Participações
└── Repasses

JURÍDICO
├── Assuntos Jurídicos
├── Contratos
│   ├── Contratos
│   ├── Templates
│   └── Variáveis
├── Compliance e Políticas
├── Propriedade Intelectual
└── Societário

VALTRENCHAT

RH

MARKETING
├── Visão Geral
├── Campanhas
├── Calendário
├── Métricas
└── Tarefas

NEGÓCIOS
├── Produtos
├── Serviços
└── Unidades de Negócio

RELATÓRIOS

CONFIGURAÇÕES

ADMINISTRAÇÃO
├── Estrutura Organizacional
├── Patrimônio e Licenças
├── Acessos e Permissões
├── Auditoria
└── Integrações
```

---

## 2. Constatação arquitetural principal

O sistema atual não é uma aplicação modular convencional com frontend, backend, banco, models, services e APIs separados. O repositório armazena um pacote-base em `.bootstrap` e uma cadeia extensa de scripts Python/fragmentos JavaScript/CSS que reconstruem e modificam um `app.js` estático durante `scripts/materialize.py`.

O deploy da branch `dev` executa `python scripts/materialize.py` e publica o resultado estático no GitHub Pages. Portanto, o comportamento final depende simultaneamente de:

1. conteúdo original recuperado do `.bootstrap`;
2. ordem dos scripts executados por `materialize.py`;
3. substituições por string/regex realizadas por cada patch;
4. funções duplicadas/sobrescritas em etapas posteriores;
5. CSS global acumulado, incluindo regras com `!important`.

Isto cria uma diferença importante entre **fonte intermediária** e **runtime materializado**. Há módulos e referências ainda presentes em arquivos-fonte de patch que são removidos ou substituídos apenas em etapas posteriores do materializador.

---

## 3. Sidebar atual — runtime materializado

A navegação visível final é, hoje:

```text
Dashboard
CRM
Agenda
Financeiro
├── Transações
├── Contabilidade
└── Notas Fiscais
Marketing
├── Visão Geral
├── Campanhas
├── Calendário
├── Métricas
├── Briefings
└── Tarefas
ValtrenChat
Relatórios
Configurações
├── Configurações
├── Usuários
├── Meu Perfil
├── Audit Trail
└── Billing
```

### Observações

- `Regras de Categorização` e `Categorias Financeiras` continuam existindo como páginas auxiliares, mas foram removidas do sidebar.
- `Automações Financeiras` foi removido do runtime final, porém ainda existe em fontes intermediárias anteriores ao patch de remoção.
- `IA Criativa` não aparece no sidebar como módulo independente.
- `MusicChat` não aparece no sidebar; o item visível é `ValtrenChat`.
- `Usuários`, `Meu Perfil`, `Audit Trail` e `Billing` ainda são tratados como submódulos de `Configurações`, o que conflita com a arquitetura definitiva.

---

## 4. Rotas atuais

### Principais

```text
#/crm/dashboard
#/crm/relationships
#/crm/agenda

#/crm/financeiro
#/crm/financeiro/accounting
#/crm/financeiro/invoices
#/crm/financeiro/rules
#/crm/financeiro/categories

#/crm/marketing
#/crm/marketing/campaigns
#/crm/marketing/calendar
#/crm/marketing/metrics
#/crm/marketing/briefings
#/crm/marketing/tasks

#/crm/valtrenchat
#/crm/relatorios

#/crm/configuracoes
#/crm/configuracoes/users
#/crm/configuracoes/profile
#/crm/configuracoes/audit
#/crm/configuracoes/billing
```

### Rotas legadas / aliases

```text
#/crm/musicchat
#/crm/marketing/ai
```

- `#/crm/musicchat` funciona como alias legado para ValtrenChat.
- `#/crm/marketing/ai` permanece como alias invisível que retorna a Visão Geral do Marketing; não existe IA Criativa independente visível.
- A rota de `Automações Financeiras` aparece em fonte intermediária (`#/crm/financeiro/automations`), mas é removida pelo patch final correspondente.

### Problemas de consistência

- Os slugs misturam português e inglês (`accounting`, `invoices`, `users`, `audit`, `billing`).
- CRM é apresentado ao usuário como `CRM`, porém sua rota canônica ainda expõe o nome técnico/legado `relationships`.
- O roteamento é manual por hash e é inserido em mais de uma rotina de renderização, aumentando o risco de divergência.

---

## 5. Layouts e navegação estrutural

Há três famílias principais de layout:

### A. Layout compartilhado dos módulos de referência

Usa:

- `crmFidelityPage`
- `crmRelSidebar`
- `crmHeaderActions`
- `crmFidelityTable`
- `crmFidelityPanel`
- `crmRefToolbar`
- `crmRefKpi`
- `crmRefModal`
- `crmRefField`
- `crmRefSelect`
- `crmRefTextarea`

É usado principalmente por Financeiro, Marketing, ValtrenChat, Relatórios e Configurações.

### B. Layout próprio do CRM

O CRM/Relacionamentos mantém uma implementação separada (`crmRelationshipsPage`) com tabela, KPIs, modais, filtros, seleção em massa e CRUD próprio.

### C. Layout próprio da Agenda

Agenda possui calendário, filtros, modais e helpers próprios (`crmAgenda*`) e depende de dados do CRM para participantes e locais.

### Dashboard

Dashboard também possui implementação própria, com seus próprios cards e seções, embora reutilize o shell/sidebar global após os patches.

### Breadcrumbs

Não existe hoje um componente real de breadcrumb para o Sistema Interno. A hierarquia é representada por sidebar, topbar, tabs e subtabs locais. Para a arquitetura definitiva será necessário definir uma única fonte de metadados de rota/navegação para breadcrumb, título, módulo ativo e permissões.

---

## 6. Banco de dados e persistência

### Estado atual

Não existe banco de dados operacional no projeto auditado.

Também não existe, na estrutura rastreada do repositório:

- migrations;
- schema SQL;
- ORM;
- Supabase configurado;
- API backend;
- servidor de aplicação;
- camada repository;
- camada service de domínio.

O README confirma que esta etapa não possui Supabase/backend externo e que o projeto é publicado como aplicação estática.

### Persistência real por módulo

- CRM e Agenda manipulam objetos em um `state` global em memória.
- Os módulos de referência criam arrays no `state`, mas grande parte dos formulários apenas fecha o modal e rerenderiza; não há persistência real das entidades.
- O site/CMS possui mecanismos próprios de `localStorage`, mas isto não equivale a banco de dados do Sistema Interno.

Conclusão: **não existe hoje uma fonte de verdade persistente para os domínios do Sistema Interno**.

---

## 7. Models / entities atuais

Não existem classes/models formais. Os “models” são objetos JavaScript implícitos em arrays do estado global.

### CRM

**Contact** (`state.crmRelContacts`)

Campos observados: `id`, `tipo_pessoa`, `name`, `company`, `segment`, `profile`, `phone`, `email`, `city`, `responsible`, `status`, `priority`, `cpf`, `cnpj`, `instagram`, `function`, `address`, `notes`, `interactions`.

**Lead** (`state.crmRelLeads`)

Campos observados: `id`, `name`, `company`, `email`, `phone`, `source`, `stage`, `responsible`, `status`, `priority`, `notes`.

### Agenda

**AgendaEvent** (`state.crmAgendaEvents`)

Campos observados: `id`, `title`, `type`, `participants`, `status`, `startDate`, `startTime`, `endDate`, `endTime`, `venueContactId`, `venue`, `contact`, `address`, `capacity`, `cache`, `expected`, `description`, `notes`.

`participants` é armazenado como string separada por vírgulas, não como relacionamento por IDs.

### Financeiro / referência

Arrays existentes ou preparados:

- `state.crmRefTransactions`
- `state.crmRefInvoices`
- `state.crmRefCategories`
- `state.crmRefCategorizationRules`
- `state.crmRefCampaigns`
- `state.crmRefBriefings`
- `state.crmRefTasks`
- `state.crmRefContents`
- `state.crmRefUsers`
- `state.crmRefAudit`

`crmRefFinancialRules` existe em fonte intermediária, mas é removido do runtime final junto com Automações Financeiras.

### ValtrenChat

Há dois estados conceitualmente sobrepostos:

- `state.crmRefMusicChat`
- `state.crmRefValtrenChat`

O ValtrenChat usa a configuração `crmRefValtrenChat`, porém a aba ativa ainda é lida/escrita em `crmRefMusicChat.tab`. Isto é uma inconsistência real de modelo/estado.

### Relatórios

`state.crmReportEntities` espera objetos com propriedades como `label/tableName`, `reportable`, `available`, `supportsImport` e `supportsExport`, mas não há backend atual que alimente essa coleção.

---

## 8. APIs, services e hooks

### APIs

Não foi identificada uma camada API real para o Sistema Interno. As integrações exibidas são configuração visual/placeholder.

### Services

Não há camada de services de domínio. A lógica está diretamente dentro de funções de renderização, manipuladores de evento e arrays globais.

### Hooks

Não há arquitetura baseada em React/Vue hooks. O sistema é JavaScript imperativo com listeners globais de DOM.

### Consequência

Antes de os novos domínios crescerem, será necessário definir uma camada de dados/serviços estável; caso contrário Rateios, Participações, Repasses, Jurídico, RH, Negócios e Administração serão apenas novas telas sobre o mesmo estado global.

---

## 9. Permissões e autenticação

Existe UI de usuários, perfil, papel e permissões, mas não existe uma implementação operacional de RBAC/ABAC no Sistema Interno.

Problemas atuais:

- nenhuma proteção de rota por permissão identificada;
- nenhuma autorização por ação identificada;
- papéis/permissões são apresentados como dependentes de um backend inexistente;
- usuário global usa valores default como `Administrador` / `AD`;
- notificações do header são hardcoded;
- `Usuários` existe simultaneamente como submódulo e como aba interna de Configurações.

Na arquitetura definitiva, a fonte de verdade deve migrar para `Administração > Acessos e Permissões`.

---

## 10. Integrações atuais

A página de Configurações exibe:

- Soundcharts;
- Meta;
- Google Ads;
- TikTok Ads;
- YouTube Ads;
- Spotify Ads;
- Distribuidoras.

Não há evidência de clientes de API/serviços funcionais correspondentes no Sistema Interno auditado.

Na arquitetura definitiva, esta responsabilidade deve ser movida para `Administração > Integrações`.

---

## 11. Dados mockados / hardcoded

### Dashboard

É a maior concentração de dados hardcoded. Existem valores, percentuais, produtos, resultados e repasses ilustrativos diretamente no código, incluindo produtos/ventures, participação da Valtren, resultados e distribuição financeira.

### CRM

É inicializado com contatos e leads fictícios/hardcoded.

### Header

Usuário default e notificações são hardcoded.

### Marketing

KPIs usam `0`, `—` ou valores fixos. O calendário contém mês/data fixa no markup de referência e diversos fluxos são apenas visuais.

### Financeiro

KPIs são majoritariamente `0`. Formulários de referência não implementam persistência operacional completa.

### Billing

Planos, preços e textos são hardcoded e carregam referências antigas do ecossistema musical.

### ValtrenChat

Menu, filas, setores, regras de escalonamento e questionários são hardcoded e fortemente orientados a shows/produção musical/editora.

---

## 12. Funcionalidades legadas, antigas ou duplicadas

### Automações Financeiras

- removido do runtime final;
- ainda existe em fonte intermediária de fidelidade;
- patch posterior remove menu, rota, página, modal e estado.

**Classificação:** legado residual de fonte. Deve ser eliminado da fonte canônica quando a arquitetura for consolidada.

### IA Criativa

- não existe como módulo independente visível;
- implementação independente foi removida;
- `#/crm/marketing/ai` permanece como alias legado para Marketing.

**Classificação:** alias legado.

### P&L Artistas / P&L Projetos

- ainda aparecem na fonte intermediária `crm_reference_fidelity_fix.js.part01`;
- o builder `crm_reference_fidelity_fix.py` substitui a página de Contabilidade antes de injetá-la, mantendo apenas `Todos` e `P&L Empresa`.

**Classificação:** resíduo de fonte com risco de regressão.

### MusicChat

- sidebar final usa ValtrenChat;
- existe alias de rota `#/crm/musicchat`;
- ainda há função alias `crmRefMusicChatPage` em fonte de fidelidade;
- estado de navegação do ValtrenChat ainda depende de `state.crmRefMusicChat.tab`.

**Classificação:** legado parcialmente acoplado; não pode ser removido por busca simples sem corrigir o estado do ValtrenChat.

### Usuários como módulo separado

- existe no submenu de Configurações;
- também existe como aba dentro da própria página Configurações;
- há ainda `Meu Perfil` separado.

**Classificação:** duplicado/mal posicionado.

### Audit Trail

- existe como submódulo de Configurações;
- possui tabela/filtros, porém não existe pipeline de auditoria real alimentando eventos.

**Classificação:** parcialmente correto funcionalmente, posicionado no lugar errado e sem backend.

### Categorias Financeiras no sidebar

Não aparece mais no sidebar final. A página/rota permanece acessível por atalho de Transações.

### Regras de Categorização no sidebar

Não aparece mais no sidebar final. A página/rota permanece acessível por atalho de Transações.

---

## 13. Dependências entre módulos atuais

### CRM → Agenda

Agenda consulta `state.crmRelContacts` para:

- participantes;
- locais/venues pessoa jurídica;
- telefone/endereço do local.

O vínculo de local usa `venueContactId`, mas participantes são armazenados por nome em texto, criando identidade frágil.

### Dashboard → Financeiro / Negócios

Dashboard apresenta dados conceitualmente pertencentes a:

- Produtos;
- Participações;
- Rateios;
- Repasses;
- Serviços;
- Financeiro consolidado.

Porém esses dados não vêm de entidades; são hardcoded no Dashboard.

### Marketing → Campanhas / Conteúdo / Tarefas

Existem campos de relação por texto, porém não há foreign keys ou entidades normalizadas. Há referências a `artista` e `projeto_musical` que não correspondem à arquitetura definitiva.

### ValtrenChat → Estrutura Organizacional

Filas, setores, responsável, supervisor e gestor são strings/IDs soltos. O futuro módulo `Administração > Estrutura Organizacional` deve se tornar a fonte de verdade desses vínculos.

### Configurações → Administração

Usuários, papéis, permissões, auditoria e integrações estão atualmente concentrados em Configurações, mas pertencem ao futuro módulo Administração.

---

## 14. Duplicidades de entidades/representações

1. **Produtos:** produtos aparecem hardcoded no Dashboard e também existem no ecossistema/site público, sem entidade interna única.
2. **Serviços:** catálogo público e resumo interno do Dashboard não compartilham uma entidade operacional única.
3. **Usuário:** `crmRefUsers`, `crmUserName`, `crmUserInitials` e telas duplicadas de usuários/perfil não compõem um modelo unificado.
4. **ValtrenChat/MusicChat:** dois nomes/estados para o mesmo domínio.
5. **Billing:** existe como aba de Configurações e como página/submódulo separado.
6. **Usuários:** existe como aba de Configurações e como página/submódulo separado.
7. **Empresa:** dados institucionais do site e dados de Empresa em Configurações não têm fonte de verdade única.
8. **Agenda/CRM:** dados do local podem ser copiados para o evento ao mesmo tempo em que existe `venueContactId`, permitindo divergência.
9. **Participantes da Agenda:** nomes são duplicados como texto em vez de relacionamentos por ID.
10. **Categorias:** Transações armazenam categorias como texto enquanto existe uma página/coleção separada de Categorias Financeiras.

---

## 15. Relacionamentos que precisam ser corrigidos na arquitetura definitiva

### CRM

- Lead → conversão real para Contact/Cliente, em vez de apenas `stage = Convertido`.
- Contact deve ser contraparte reutilizável por Jurídico, Financeiro, Agenda, Participações e Repasses.

### Agenda

- Event ↔ Contact/User como relação N:N para participantes.
- Event → Contact/Local por ID, sem depender de nomes.

### Financeiro

- Transaction → Counterparty/Contact.
- Transaction → FinancialCategory.
- Transaction → BusinessUnit.
- Transaction → Product ou Service quando aplicável.
- Transaction ↔ Invoice.
- Transaction ↔ Contract quando aplicável.
- Participation → Product/BusinessUnit + Partner/Contact + percentual + vigência.
- Rateio → origem financeira + regra + allocations.
- Repasse → Rateio/Participation + favorecido + status + pagamento/transação.

### Jurídico

- Contract → Counterparty/Contact.
- Contract → Product/Service/BusinessUnit.
- Contract → Template + Variables + documentos/assinaturas/status.

### Marketing

- Campaign/Task/Content → Product/Service/BusinessUnit por ID.
- remover dependência estrutural de `artista`/`projeto_musical` como tipo universal de contexto.

### Administração

- User → Role/Permission.
- User → OrganizationalUnit/Department/Position.
- ValtrenChat Queue/Sector → OrganizationalUnit/Team/User.
- AuditEvent → User + Entity + EntityId + Action.

---

## 16. Mapeamento da arquitetura definitiva contra o estado atual

| Destino definitivo | Estado atual | Diagnóstico |
|---|---|---|
| Dashboard | Existe | Parcial: layout correto, dados hardcoded e responsabilidades de outros domínios |
| CRM | Existe | Parcial/majoritariamente correto; falta persistência e relações normalizadas |
| Agenda | Existe | Parcial; CRUD local funciona, mas é musicalmente acoplada e depende de nomes/texto |
| Financeiro > Transações | Existe | Correto como posição; falta backend/modelo relacional |
| Financeiro > Contabilidade | Existe | Parcial; hoje apenas P&L Empresa |
| Financeiro > Notas Fiscais | Existe | Parcial; UI/modal atualizados, persistência não implementada |
| Financeiro > Rateios | Não existe | Criar |
| Financeiro > Participações | Não existe | Criar; dados conceituais estão hardcoded no Dashboard |
| Financeiro > Repasses | Não existe | Criar; dados conceituais estão hardcoded no Dashboard |
| Jurídico | Não existe | Criar integralmente |
| ValtrenChat | Existe | Parcial; remover acoplamento MusicChat e referências antigas |
| RH | Não existe | Criar |
| Marketing > Visão Geral | Existe | Parcial |
| Marketing > Campanhas | Existe | Parcial |
| Marketing > Calendário | Existe | Parcial |
| Marketing > Métricas | Existe | Parcial/placeholder |
| Marketing > Tarefas | Existe | Parcial |
| Marketing > Briefings | Existe | Fora da arquitetura definitiva; consolidar/remover como módulo independente |
| Negócios | Não existe como módulo interno | Criar integralmente; há fragmentos de Produtos/Serviços em outros lugares |
| Relatórios | Existe | Parcial; depende de backend inexistente |
| Configurações | Existe | Parcial; atualmente absorve responsabilidades de Administração |
| Administração | Não existe como grupo | Criar e mover responsabilidades existentes |

---

## 17. O que já está correto

- Dashboard, CRM, Agenda, Financeiro, Marketing, ValtrenChat e Relatórios já existem como conceitos de alto nível.
- Financeiro final já exibe apenas Transações, Contabilidade e Notas Fiscais no sidebar.
- Regras de Categorização e Categorias Financeiras já foram removidas do sidebar sem apagar suas páginas auxiliares.
- Automações Financeiras não está no runtime final.
- IA Criativa não está no sidebar como módulo independente.
- P&L Artistas e P&L Projetos não aparecem na Contabilidade final.
- ValtrenChat é o nome visível atual.

---

## 18. O que está parcialmente correto

- Dashboard: deve se tornar agregador, não fonte de dados.
- CRM: CRUD local existe, mas sem backend e sem modelo de conversão/relacionamentos normalizados.
- Agenda: CRUD local existe, mas precisa relações por ID e menor acoplamento musical.
- Financeiro: estrutura inicial correta, faltam três submódulos e modelagem.
- Marketing: cinco módulos-alvo já existem, porém Briefings excede a arquitetura e há referências musicais antigas.
- ValtrenChat: funcionalidade/configuração existe, mas estado ainda carrega `MusicChat`.
- Relatórios: UI existe, backend não.
- Configurações: existe, porém contém responsabilidades que serão de Administração.
- Audit Trail: UI existe, auditoria real não.

---

## 19. O que precisa ser movido

- `Usuários` + papéis/permissões → `Administração > Acessos e Permissões`.
- `Audit Trail` → `Administração > Auditoria`.
- `Integrações` → `Administração > Integrações`.
- setor/cargo/estrutura de usuários e filas → futura `Administração > Estrutura Organizacional`.
- dados de Participações/Rateios/Repasses hoje hardcoded no Dashboard → submódulos financeiros correspondentes.
- Produtos/Serviços hoje dispersos entre site e Dashboard → `Negócios` como fonte interna de verdade.
- lógica/menções de Contratos hoje espalhadas em Dashboard/Configurações → futuro `Jurídico > Contratos`.
- Meu Perfil deve permanecer como ação de conta, não como submódulo estrutural de Configurações.

---

## 20. O que precisa ser renomeado

- `Audit Trail` → `Auditoria`.
- `Usuários` como domínio administrativo → `Acessos e Permissões` após consolidação.
- estado/funções `MusicChat` → `ValtrenChat` após migração segura.
- chrome visível `CRM Integrado` é tecnicamente inadequado para um sistema que contém Financeiro, Jurídico, RH, Negócios e Administração; deve ser substituído por uma denominação do Sistema Interno na fase de arquitetura visual.
- rotas inglesas/mistas devem ser normalizadas posteriormente, com aliases de compatibilidade durante migração.

---

## 21. O que deve ser removido

- resíduos de fonte de `Automações Financeiras` depois que a arquitetura canônica for estabilizada;
- alias legado de `IA Criativa` depois de janela de compatibilidade;
- resíduos `P&L Artistas` / `P&L Projetos` na fonte intermediária;
- alias/nome `MusicChat` depois de migrar `crmRefMusicChat.tab`;
- `Briefings` como módulo independente, pois não existe na arquitetura definitiva;
- `Billing` como módulo/submódulo atual: é duplicado e contém conteúdo de planos/labels/publishers incompatível com o Sistema Interno definitivo;
- duplicação de `Usuários` entre aba e submódulo;
- duplicação de `Billing` entre aba e submódulo;
- `Cadastro Público` orientado a artistas, salvo se futuramente houver requisito explícito compatível com o novo modelo.

---

## 22. O que deve ser consolidado

- Usuários + papéis + permissões + segurança administrativa → Acessos e Permissões.
- Auditoria visual + geração real de eventos → Auditoria.
- Integrações hoje em Configurações → Administração > Integrações.
- Produtos/Serviços de múltiplas representações → entidades canônicas de Negócios.
- Regras/Categorias Financeiras → recursos auxiliares do domínio financeiro, não módulos principais de sidebar.
- dados de participação/distribuição do Dashboard → entidades de Participações/Rateios/Repasses.
- Company/organization data espalhados → Company + OrganizationalStructure bem definidos.

---

## 23. O que ainda precisa ser criado

### Financeiro

- Rateios;
- Participações;
- Repasses.

### Jurídico

- Assuntos Jurídicos;
- Contratos;
- Templates;
- Variáveis;
- Compliance e Políticas;
- Propriedade Intelectual;
- Societário.

### RH

- módulo inteiro.

### Negócios

- Produtos;
- Serviços;
- Unidades de Negócio.

### Administração

- Estrutura Organizacional;
- Patrimônio e Licenças;
- Acessos e Permissões como módulo real;
- Auditoria real;
- Integrações como módulo administrativo real.

### Infraestrutura transversal

- persistência/banco;
- models/entities canônicos;
- services/repositories;
- API/backend;
- autorização real;
- auditoria real;
- route metadata/breadcrumbs;
- camada de relacionamento entre domínios;
- source of truth única para dados mestres.

---

## 24. Principais riscos de regressão

1. **Ordem do materializador:** o resultado final depende da sequência de patches em `materialize.py`.
2. **Fonte x runtime divergentes:** módulos removidos no runtime continuam em arquivos intermediários e podem reaparecer se um patch deixar de executar.
3. **Regex/string replacements frágeis:** mudanças pequenas no texto das funções podem fazer patches falharem ou não encontrarem o alvo.
4. **Funções duplicadas/sobrescritas:** `crmRelSidebar`, páginas de referência e versões fidelity coexistem em etapas diferentes.
5. **Rotas duplicadas em dois renders:** alterações devem atingir todas as rotinas de renderização.
6. **MusicChat/ValtrenChat:** remover `crmRefMusicChat` sem migrar a aba ativa quebra ValtrenChat.
7. **Agenda → CRM:** alterar Contact IDs/estrutura quebra participantes/locais da Agenda.
8. **Financeiro auxiliar:** apagar Rules/Categories sem remover atalhos/links causa rotas quebradas.
9. **Header de usuário:** mover Perfil/Configurações/Usuários exige revisar ações do menu global.
10. **CSS global com `!important`:** novos componentes podem herdar regras não desejadas.
11. **Dashboard hardcoded:** criar Participações/Rateios/Repasses sem retirar depois os mocks gera duas fontes de verdade.
12. **Sem backend:** novas telas podem parecer funcionais sem persistência real.
13. **Deploy estático:** não há runtime server-side para lógica financeira, permissões, auditoria ou integrações.
14. **Invoice refactor tardio:** a UI final de Notas depende de patch executado por último; a fonte intermediária ainda contém o dropdown antigo.
15. **P&L residual:** fontes intermediárias ainda contêm Artistas/Projetos e podem ressurgir caso o override de Contabilidade falhe.

---

## 25. Regra para as próximas etapas

A próxima implementação deve tratar este documento como baseline técnico e evitar adicionar novos módulos diretamente sobre as fontes intermediárias sem antes definir qual camada será a fonte canônica.

A ordem segura para evolução é:

1. estabilizar navegação/route metadata e source-of-truth do shell;
2. definir entidades e relacionamentos canônicos;
3. definir persistência/backend/service layer;
4. migrar módulos existentes sem quebrar aliases/dependências;
5. criar os módulos faltantes;
6. retirar mocks e fontes duplicadas;
7. eliminar patches/aliases legados somente depois de comprovar ausência de regressão.

**Nenhuma refatoração funcional foi realizada nesta auditoria. Este arquivo é somente documentação técnica de referência.**
