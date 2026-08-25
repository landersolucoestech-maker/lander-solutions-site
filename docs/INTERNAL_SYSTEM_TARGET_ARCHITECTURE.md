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
├── Patrimônio e Licenças
├── Acessos e Permissões
├── Auditoria
└── Integrações
```

## Regras estruturais obrigatórias

- A ordem acima é a ordem oficial do sidebar.
- `Configurações` é um único módulo principal e não possui submódulos no sidebar.
- A organização interna de `Configurações` pode conter apenas seções de parâmetros globais, como `Geral`, `Empresa`, `Notificações` e `Preferências do Sistema`; essas divisões não são módulos do sidebar.
- `Meu Perfil` não é módulo do sidebar. Ele pertence exclusivamente ao menu do usuário/avatar e possui rota própria.
- `Usuários` não é módulo principal nem submódulo de Configurações. Usuários, convites, papéis, permissões, escopos, restrições, MFA, sessões e status de acesso pertencem a `Administração > Acessos e Permissões`.
- `Audit Trail` é nomenclatura legada. O nome oficial e visível é `Administração > Auditoria`.
- `Integrações` pertence exclusivamente a `Administração > Integrações`. Não deve existir implementação concorrente em Configurações.
- `Billing` não faz parte da arquitetura oficial do Sistema Interno. A implementação histórica de Billing representa cobrança/planos da própria aplicação e permanece, quando necessário, apenas como legado técnico sem exposição na navegação.
- `Briefings` não é submódulo do Marketing.
- `Regras de Categorização` e `Categorias Financeiras` não são itens do sidebar financeiro; permanecem apenas como recursos auxiliares quando necessários.
- `Automações Financeiras` não faz parte da arquitetura.
- `IA Criativa` não é módulo independente.
- `P&L Artistas` e `P&L Projetos` não fazem parte da Contabilidade.
- O nome visível é `ValtrenChat`; `MusicChat` permanece somente como compatibilidade legada até sua remoção segura.

## Rotas canônicas deste eixo

```text
Configurações
#/crm/configuracoes

Meu Perfil
#/crm/meu-perfil

Administração / Estrutura Organizacional
#/crm/administracao

Administração / Patrimônio e Licenças
#/crm/administracao/patrimonio-licencas

Administração / Acessos e Permissões
#/crm/administracao/acessos-permissoes

Administração / Auditoria
#/crm/administracao/auditoria

Administração / Integrações
#/crm/administracao/integracoes
```

## Compatibilidade legada temporária

As rotas antigas abaixo podem existir apenas como aliases/redirects técnicos para impedir quebra de links antigos. Elas não são canônicas e não podem aparecer na navegação:

```text
#/crm/configuracoes/profile      → #/crm/meu-perfil
#/crm/configuracoes/users        → #/crm/administracao/acessos-permissoes
#/crm/configuracoes/audit        → #/crm/administracao/auditoria
#/crm/configuracoes/integracoes  → #/crm/administracao/integracoes
#/crm/configuracoes/billing      → #/crm/configuracoes
```
