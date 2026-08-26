const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const materialized = process.argv.includes('--materialized');
const fail = (message) => { throw new Error(message); };
const must = (condition, message) => { if (!condition) fail(message); };

const review = fs.readFileSync(path.join(__dirname, 'crm_product_system_review.py'), 'utf8');
const runner = fs.readFileSync(path.join(__dirname, 'crm_product_system_review_runner.py'), 'utf8');
const dashboard = fs.readFileSync(path.join(__dirname, 'crm_dashboard_module.py'), 'utf8');

must(review.includes('Autenticação desativada'), 'global review must keep authentication explicitly disabled');
must(review.includes('Nenhuma identidade é simulada'), 'global review must prohibit fake logged-in identity');
must(review.includes("state.crmRelContacts = []"), 'legacy CRM contacts must start empty');
must(review.includes("state.crmRelLeads = []"), 'legacy CRM leads must start empty');
must(review.includes("EMPTY_USERS = r'''  function crmFullUsers(){\n    return [];"), 'global review must remove fake current-user options');
must(!review.includes('DASHBOARD = r'), 'global review must not own crmDashboardPage implementation');
must(!review.includes('"crmDashboardPage"'), 'global replacement table must not replace crmDashboardPage');
must(!review.includes('source.find("\\n  function ",'), 'generic next-function replacement must not survive');
must(review.includes('_replace_between'), 'global review must use explicit named boundaries');

must(dashboard.includes('DASHBOARD_START'), 'Dashboard owner must mark its own materialized block');
must(dashboard.includes('DASHBOARD_END'), 'Dashboard owner must close its own materialized block');
must(dashboard.includes('function crmDashboardPage(query)'), 'Dashboard owner must emit crmDashboardPage');
must(dashboard.includes('function contactPage(query)'), 'Dashboard migration must use explicit contactPage boundary');
must(!dashboard.includes('source.find("\\n  function ",'), 'Dashboard owner must not use generic next-function slicing');
['Contatos','Leads','Clientes','Receitas','Despesas','Resultado'].forEach((token)=>must(dashboard.includes(`kpi('${token}'`), `Dashboard owner missing KPI ${token}`));
[
  'Receita Consolidada',
  'R$ 275.000',
  'Music OS 360</h3><p>SaaS / Plataforma',
  '23 novas vendas',
  'R$ 18.500 recebido',
  'Protótipo · dados ilustrativos'
].forEach((token)=>must(!dashboard.includes(token), `Dashboard owner still contains fake/demo token: ${token}`));
must(runner.includes('Dashboard materializer idempotence: PASS'), 'materialization runner must enforce Dashboard idempotence');
must(runner.includes('_assert_js_syntax'), 'materialization runner must validate JS syntax incrementally');

if (materialized) {
  const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
  const css = fs.readFileSync(path.join(root, 'assets', 'valtren-brand.css'), 'utf8');
  const forbidden = [
    'Protótipo · dados ilustrativos',
    'Usuário logado',
    "state.crmUserName || 'Administrador'",
    "state.crmUserName||'Administrador'",
    "state.crmUserInitials || 'AD'",
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
  must((app.match(/VALTREN CRM DASHBOARD START/g)||[]).length === 1, 'Dashboard start marker must exist exactly once');
  must((app.match(/function crmDashboardPage\(/g)||[]).length === 1, 'crmDashboardPage must exist exactly once');
  must(app.includes("if(path==='/crm/juridico')return crmLegalMattersPage();"), 'Legal Matters owner route changed');
  must(app.includes("if(path==='/crm/juridico/contratos')return crmLegalContractsPage();"), 'Legal Contracts owner route changed');
  must(app.includes("if(path==='/crm/juridico/compliance')return crmCompliancePage();"), 'Compliance owner route changed');
  must(app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmIntellectualPropertyPage();"), 'IP owner route changed');
  must(app.includes("if(path==='/crm/juridico/societario')return crmCorporateGovernancePage();"), 'Corporate Governance owner route changed');
  must(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"), 'Economic Participations route changed');
  must(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"), 'Payouts route changed');
  must(css.includes('/* VALTREN CRM INTEGRATED */'), 'Dashboard CSS owner block missing');
  must(css.includes('/* VALTREN PRODUCT SYSTEM REVIEW */'), 'global design-system patch missing');
  must(css.includes('--crm-surface:'), 'centralized CRM visual tokens missing');
  must(css.includes('@media(max-width:760px)'), 'tablet/mobile responsive rules missing');
  must(css.includes('@media(max-width:480px)'), 'mobile responsive rules missing');
}

console.log(`product-system-review: PASS${materialized ? ' (materialized)' : ''}`);
