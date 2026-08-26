# Valtren Solutions — Site institucional e Sistema Interno

Projeto da **Valtren Solutions** composto pelo site institucional e pelo Sistema Interno materializado pelos scripts deste repositório.

## Regras de desenvolvimento

- Desenvolvimento exclusivamente na branch `dev`;
- Branch `main` preservada e sem escrita até liberação explícita;
- Autenticação desativada nesta etapa;
- Nenhum usuário, sessão, papel, permissão ou notificação deve ser simulado como se viesse de backend;
- Sem Supabase ou outro backend externo nesta etapa;
- Credenciais de integrações não devem ser armazenadas no frontend;
- Dados operacionais devem iniciar vazios quando não houver fonte real; demonstrações não podem ser tratadas como registros reais.

## Materialização

A aplicação final é reconstruída a partir do payload em `.bootstrap` e dos materializadores em `scripts/`.

```bash
python scripts/materialize.py
python -m http.server 4173
```

O materializador global `scripts/crm_product_system_review.py` roda por último e permanece estritamente transversal: consolida estados vazios, transparência de capacidades ainda inexistentes e tokens compartilhados, sem assumir ownership de Dashboard, Header, Sidebar ou módulos de domínio.

Artefatos locais de execução Python (`__pycache__`, `*.pyc`) não fazem parte da fonte nem da saída certificada e são ignorados para preservar uma árvore determinística.

## Ownership canônico

- Dashboard: `scripts/crm_dashboard_module.py`;
- Sidebar / navegação: `scripts/crm_sidebar_architecture.py`, único owner de `crmRelSidebar`;
- Header / Account Menu: `scripts/crm_global_header.py`;
- Agenda: `scripts/crm_agenda_module.py`, consumidora do Header e da Sidebar;
- Pessoas / Organizações: `ValtrenPartyCore`;
- CRM: `ValtrenCrmCore` sobre referências canônicas de Pessoas / Organizações;
- Transações: `ValtrenFinanceCore`;
- Contabilidade: owner próprio derivado de Transações;
- Notas Fiscais: owner próprio com referências a Pessoas / Organizações e Transações;
- Rateios: owner próprio de alocação de despesas existentes;
- Participações: owner econômico próprio;
- Repasses: owner de liquidação de participações aprovadas;
- Negócios: Produtos, Serviços e Unidades de Negócio;
- Contratos: owner jurídico próprio;
- Assuntos Jurídicos: `ValtrenLegalMatterCore`;
- Compliance e Políticas: `ValtrenComplianceCore`;
- Propriedade Intelectual: `ValtrenIntellectualPropertyCore`;
- Societário: `ValtrenCorporateGovernanceCore`;
- Configurações e compatibilidade de rotas: `scripts/crm_definitive_architecture.py`.

Materializadores de domínio que verificam a navegação validam exclusivamente o bloco delimitado por `VALTREN SIDEBAR ARCHITECTURE START/END`; nenhum domínio usa conteúdo posterior do bundle como boundary nem reescreve `crmRelSidebar`.

## Autenticação

A autenticação permanece **desativada**. Não existe senha inicial local, usuário conectado, sessão real ou fallback que finja autenticação. A interface deve comunicar esse estado de forma explícita.

Qualquer futura autenticação deverá ser ligada a um provedor real de identidade e persistência segura antes de habilitar Perfil, usuários, papéis, permissões, MFA ou sessões.

## Integrações

Integrações sem credenciais e backend seguro devem aparecer apenas como **Não configurado**. Não é permitido simular conexão, sincronização, métricas, envio ou recebimento.

## Identidade visual

A interface usa a identidade visual da Valtren Solutions, com tokens consolidados na camada materializada. Os arquivos `assets/valtren-logo.svg`, `assets/valtren-logo-light.svg` e `assets/valtren-mark.svg` permanecem como ativos oficiais do projeto.
