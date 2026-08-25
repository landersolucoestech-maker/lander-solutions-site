# Valtren Solutions — Estrutura Definitiva do Sistema Interno

Este documento é a fonte oficial de referência da arquitetura de módulos do Sistema Interno da Valtren e prevalece sobre estruturas anteriores registradas em auditorias ou implementações intermediárias.

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
└── Patrimônio e Licenças
```

## Configurações

`Configurações` é um único módulo principal no sidebar e não possui submenu na navegação lateral.

Ao acessar `#/crm/configuracoes`, a página contém exatamente seis abas internas, nesta ordem:

```text
Empresa
Notificações
Segurança
Integrações
Auditoria
Usuários
```

As abas `Geral` e `Preferências do Sistema` não fazem parte da arquitetura atual.

### Empresa

Concentra dados institucionais e parâmetros globais da Valtren, incluindo razão social, nome fantasia, CNPJ, inscrições aplicáveis, endereço, telefone, e-mail, site, identidade visual, logo, moeda, idioma, fuso horário e formatos institucionais.

### Notificações

Concentra canais, tipos, frequência, horários, eventos, alertas, notificações internas e notificações por e-mail em nível global.

### Segurança

Concentra políticas e parâmetros globais de segurança, como políticas de senha, MFA, duração/expiração de sessão, tentativas de acesso, bloqueios e proteção de autenticação. Configurações pessoais de senha, MFA e sessões do usuário atual continuam em `Meu Perfil`.

### Integrações

`Integrações` pertence a `Configurações` como aba interna. Não é submódulo de Administração e não existe como item independente no sidebar. Uma integração somente pode ser apresentada como conectada quando a conexão tiver sido efetivamente validada.

### Auditoria

`Auditoria` pertence a `Configurações` como aba interna e é somente leitura. `Audit Trail` permanece apenas como nomenclatura legada de código quando tecnicamente necessário e nunca como nome visível oficial.

### Usuários

`Usuários` pertence a `Configurações` como aba interna. A gestão inclui usuários, convites, papéis do sistema, permissões, escopos, restrições, unidades autorizadas, status, MFA por usuário, sessões, ativação, suspensão e revogação.

`Cargo` e `Papel do sistema` são conceitos distintos. Cargo pertence à estrutura organizacional/RH; papel define autorização dentro do sistema.

## Meu Perfil

`Meu Perfil` não aparece no sidebar. Ele permanece exclusivamente no menu do usuário/avatar e possui página própria em:

```text
#/crm/meu-perfil
```

Meu Perfil administra apenas os dados e a segurança do usuário atual, incluindo informações pessoais, senha, MFA e sessões próprias.

## Administração

`Administração` possui exatamente dois submódulos no sidebar:

```text
Administração
├── Estrutura Organizacional
└── Patrimônio e Licenças
```

`Acessos e Permissões`, `Auditoria` e `Integrações` não pertencem mais a Administração.

### Estrutura Organizacional

Abrange entidades jurídicas, departamentos, áreas, equipes, cargos, hierarquia, gestores e relações de reporte.

### Patrimônio e Licenças

Abrange computadores, notebooks, celulares, equipamentos, veículos, mobiliário, dispositivos, licenças administrativas, certificados, patrimônio, custódia, movimentações, garantias, validade e baixa.

## Billing

`Billing` não faz parte da arquitetura oficial do Sistema Interno. Não pode aparecer como módulo, submenu, aba, card de navegação ou seção de Configurações. A implementação histórica pode permanecer apenas como legado técnico quando ainda houver dependência interna.

## Rotas canônicas deste eixo

```text
Configurações
#/crm/configuracoes

Configurações / Empresa
#/crm/configuracoes?tab=empresa

Configurações / Notificações
#/crm/configuracoes?tab=notificacoes

Configurações / Segurança
#/crm/configuracoes?tab=seguranca

Configurações / Integrações
#/crm/configuracoes?tab=integracoes

Configurações / Auditoria
#/crm/configuracoes?tab=auditoria

Configurações / Usuários
#/crm/configuracoes?tab=usuarios

Meu Perfil
#/crm/meu-perfil

Administração / Estrutura Organizacional
#/crm/administracao

Administração / Patrimônio e Licenças
#/crm/administracao/patrimonio-licencas
```

## Compatibilidade legada temporária

As rotas abaixo existem somente como aliases/redirects técnicos para impedir quebra de links antigos. Não são canônicas e não podem aparecer na navegação ou breadcrumbs oficiais:

```text
#/crm/configuracoes/profile                → #/crm/meu-perfil
#/crm/configuracoes/users                  → #/crm/configuracoes?tab=usuarios
#/crm/administracao/acessos-permissoes    → #/crm/configuracoes?tab=usuarios
#/crm/configuracoes/audit                  → #/crm/configuracoes?tab=auditoria
#/crm/administracao/auditoria             → #/crm/configuracoes?tab=auditoria
#/crm/configuracoes/integracoes            → #/crm/configuracoes?tab=integracoes
#/crm/administracao/integracoes           → #/crm/configuracoes?tab=integracoes
#/crm/configuracoes/billing                → #/crm/configuracoes?tab=empresa
```

## Regras estruturais adicionais

- `Briefings` não é submódulo do Marketing.
- `Regras de Categorização` e `Categorias Financeiras` não são itens do sidebar financeiro; permanecem apenas como recursos auxiliares quando necessários.
- `Automações Financeiras` não faz parte da arquitetura.
- `IA Criativa` não é módulo independente.
- `P&L Artistas` e `P&L Projetos` não fazem parte da Contabilidade.
- O nome visível é `ValtrenChat`; `MusicChat` permanece somente como compatibilidade legada até sua remoção segura.
