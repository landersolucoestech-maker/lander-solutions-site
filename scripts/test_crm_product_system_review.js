const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const materialized = process.argv.includes('--materialized');
const fail = (message) => { throw new Error(message); };
const must = (condition, message) => { if (!condition) fail(message); };

const materializer = fs.readFileSync(path.join(__dirname, 'crm_product_system_review.py'), 'utf8');
must(materializer.includes('Autenticação desativada'), 'materializer must keep authentication explicitly disabled');
must(materializer.includes('Nenhuma identidade é simulada'), 'materializer must prohibit fake logged-in identity');
must(materializer.includes("state.crmRelContacts = []"), 'legacy CRM contacts must start empty');
must(materializer.includes("state.crmRelLeads = []"), 'legacy CRM leads must start empty');
must(materializer.includes("kpi('Contatos'"), 'dashboard must expose Contacts KPI');
must(materializer.includes("kpi('Leads'"), 'dashboard must expose Leads KPI');
must(materializer.includes("kpi('Clientes'"), 'dashboard must expose Clients KPI');
must(materializer.includes("kpi('Receitas'"), 'dashboard must expose Revenue KPI');
must(materializer.includes("kpi('Despesas'"), 'dashboard must expose Expenses KPI');
must(materializer.includes("kpi('Resultado'"), 'dashboard must expose Result KPI');
must(!materializer.includes("state.crmUserName || 'Administrador'"), 'materializer must not invent an Administrator user');
must(!materializer.includes("state.crmUserInitials || 'AD'"), 'materializer must not invent user initials');

if (materialized) {
  const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
  const css = fs.readFileSync(path.join(root, 'assets', 'valtren-brand.css'), 'utf8');
  const forbidden = [
    'Protótipo · dados ilustrativos',
    'Usuário logado',
    'Marina Costa',
    'Aurora Tecnologia Ltda.',
    'Grupo Horizonte',
    'Rafael Nunes',
    'Paulo Mendes',
    'Fernanda Lima',
    'Daniel Souza',
    'Receita Consolidada',
    'Music OS 360</h3><p>SaaS / Plataforma',
    '23 novas vendas',
    'R$ 18.500 recebido'
  ];
  forbidden.forEach((token) => must(!app.includes(token), `materialized app still contains fake/demo UI token: ${token}`));
  ['Autenticação desativada','Nenhuma identidade é simulada','Contatos','Leads','Clientes','Receitas','Despesas','Resultado','Não configurado'].forEach((token)=>must(app.includes(token), `materialized app missing canonical token: ${token}`));
  must(app.includes("if(path==='/crm/juridico')return crmLegalMattersPage();"), 'Legal Matters owner route changed');
  must(app.includes("if(path==='/crm/juridico/contratos')return crmLegalContractsPage();"), 'Legal Contracts owner route changed');
  must(app.includes("if(path==='/crm/juridico/compliance')return crmCompliancePage();"), 'Compliance owner route changed');
  must(app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmIntellectualPropertyPage();"), 'IP owner route changed');
  must(app.includes("if(path==='/crm/juridico/societario')return crmCorporateGovernancePage();"), 'Corporate Governance owner route changed');
  must(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"), 'Economic Participations route changed');
  must(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"), 'Payouts route changed');
  must(css.includes('/* VALTREN PRODUCT SYSTEM REVIEW */'), 'global design-system patch missing');
  must(css.includes('--crm-surface:'), 'centralized CRM visual tokens missing');
  must(css.includes('@media(max-width:760px)'), 'tablet/mobile responsive rules missing');
  must(css.includes('@media(max-width:480px)'), 'mobile responsive rules missing');
}

console.log(`product-system-review: PASS${materialized ? ' (materialized)' : ''}`);
