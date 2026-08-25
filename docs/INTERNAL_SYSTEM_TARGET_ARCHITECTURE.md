# Valtren Solutions — Estrutura Definitiva do Sistema Interno

Este documento é a fonte de referência da estrutura de módulos do Sistema Interno a partir de 25/08/2026 e prevalece sobre estruturas-alvo anteriores registradas em documentos de auditoria.

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
├── Configurações
├── Meu Perfil
├── Integrações
├── Audit Trail
├── Usuários
└── Billing

ADMINISTRAÇÃO
├── Estrutura Organizacional
└── Patrimônio e Licenças
```

## Regras estruturais

- A ordem acima é a ordem oficial do sidebar.
- `Briefings` não é submódulo do Marketing.
- `Regras de Categorização` e `Categorias Financeiras` não são itens do sidebar financeiro; permanecem, quando necessárias, como recursos auxiliares acessíveis a partir do Financeiro.
- `Automações Financeiras` não faz parte da arquitetura.
- `IA Criativa` não é módulo independente.
- `P&L Artistas` e `P&L Projetos` não fazem parte da Contabilidade.
- O nome visível é `ValtrenChat`; `MusicChat` é apenas compatibilidade legada até sua remoção segura.
- `Integrações`, `Audit Trail`, `Usuários` e `Billing` pertencem a `Configurações`.
- `Administração` possui apenas `Estrutura Organizacional` e `Patrimônio e Licenças` nesta arquitetura.
