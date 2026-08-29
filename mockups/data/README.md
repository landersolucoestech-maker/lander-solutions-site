# Mock data

Esta pasta é a fonte canônica de dados mockados do Sistema Interno.

Regras:
- dados de demonstração, fixtures e populated state pertencem somente a esta pasta;
- módulos de produto não devem declarar registros mockados inline/hardcoded;
- dados daqui só podem ser carregados quando Mock Mode estiver ativo;
- produção nunca usa estes dados como fallback, seed ou verdade operacional;
- factories permanecem em `mockups/factories/`; loader, adapter e manifest permanecem na raiz de `mockups/` por serem infraestrutura.

Organização atual por domínio:
- `agenda.js`
- `crm.js`
- `business.js`
- `finance.js`
- `fiscal.js`
- `allocations.js`
- `contracts.js`
- `participations.js`
- `payouts.js`
- `legal.js`
- `compliance.js`
- `intellectual-property.js`
- `corporate.js`
- `marketing.js`
- `notifications.js`
