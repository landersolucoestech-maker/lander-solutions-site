const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const materialized = process.argv.includes('--materialized');
const fail = (message) => { throw new Error(message); };
const must = (condition, message) => { if (!condition) fail(message); };

const review = fs.readFileSync(path.join(__dirname, 'crm_product_system_review.py'), 'utf8');
const runner = fs.readFileSync(path.join(__dirname, 'crm_product_system_review_runner.py'), 'utf8');
const dashboard = fs.readFileSync(path.join(__dirname, 'crm_dashboard_module.py'), 'utf8');
const dashboardCore = fs.readFileSync(path.join(__dirname, 'crm_dashboard_core.js'), 'utf8');
const dashboardParticipationCore = fs.readFileSync(path.join(__dirname, 'crm_dashboard_participation_core.js'), 'utf8');
const dashboardBrowser = fs.readFileSync(path.join(__dirname, 'crm_dashboard_browser.js'), 'utf8');
const dashboardCss = fs.readFileSync(path.join(__dirname, 'crm_dashboard.css'), 'utf8');
const header = fs.readFileSync(path.join(__dirname, 'crm_global_header.py'), 'utf8');

must(header.includes('Autenticação desativada'), 'Header owner must keep authentication explicitly disabled');
must(header.includes('Nenhuma identidade é simulada'), 'Header owner must prohibit fake logged-in identity');
must(!review.includes('HEADER_HELPERS'), 'global review must not own Header implementation');
must(review.includes("state.crmRelContacts = []"), 'legacy CRM contacts must start empty');
must(review.includes("state.crmRelLeads = []"), 'legacy CRM leads must start empty');
must(review.includes("EMPTY_USERS = r'''  function crmFullUsers(){\n    return [];"), 'global review must remove fake current-user options');
must(!review.includes('DASHBOARD = r'), 'global review must not own crmDashboardPage implementation');
must(!review.includes('"crmDashboardPage"'), 'global replacement table must not replace crmDashboardPage');
must(!review.includes('source.find("\\n  function ",'), 'generic next-function replacement must not survive');
must(review.includes('_replace_between'), 'global review must use explicit named boundaries');

must(dashboard.includes('DASHBOARD_START'), 'Dashboard owner must mark its own materialized block');
must(dashboard.includes('DASHBOARD_END'), 'Dashboard owner must close its own materialized block');
must(dashboard.includes('crm_dashboard_core.js'), 'Dashboard owner must load calculation core');
must(dashboard.includes('crm_dashboard_participation_core.js'), 'Dashboard owner must load participation integrity core');
must(dashboard.includes('crm_dashboard_browser.js'), 'Dashboard owner must load browser components');
must(dashboard.includes('crm_dashboard.css'), 'Dashboard owner must load dedicated CSS');
must(dashboard.includes('REMOVED_DASHBOARD_COPY'), 'Dashboard owner must declare the removed-copy hierarchy contract');
must(dashboard.includes('_dashboard_browser_source'), 'Dashboard owner must normalize its own browser source before materialization');
must(dashboard.includes('function contactPage(query)'), 'Dashboard migration must use explicit contactPage boundary');
must(!dashboard.includes('source.find("\\n  function ",'), 'Dashboard owner must not use generic next-function slicing');
must(dashboardBrowser.includes('function crmDashboardPage(query)'), 'Dashboard browser owner must emit crmDashboardPage');
for (const fn of ['buildUnitPerformance','consolidatedFromDre','buildProductsVsServices','buildTrend','buildFiscalSummary','buildCostStructure','buildRankings','buildDashboard']) {
  must(dashboardCore.includes(`function ${fn}`), `Dashboard calculation core missing ${fn}`);
}
must(dashboardCore.includes("legalEntity:'Valtren Solutions'"), 'Dashboard must preserve Valtren Solutions as the legal entity');
must(dashboardCore.includes("dimensionModel:'single_legal_entity_with_internal_business_dimensions'"), 'Dashboard must model products/services as internal economic dimensions');
must(dashboardCore.includes('operatingResult-thirdPartyParticipation'), 'Dashboard Result Valtren formula missing');
must(dashboardParticipationCore.includes('participatingKeys'), 'Participation integrity core must deduplicate participating units');
must(dashboardParticipationCore.includes('participatingUnits'), 'Participation integrity core must aggregate unit result once');
for (const token of ['Faturamento Bruto','Deduções e Impostos','Receita Líquida','Custos Diretos','Despesas Operacionais','Resultado Operacional','Participações / Repasses','Resultado Valtren']) {
  must(dashboardBrowser.includes(token), `Executive Dashboard missing KPI ${token}`);
}
for (const legacy of ["kpi('Contatos'","kpi('Leads'","kpi('Clientes'",'Indicadores essenciais de CRM e Financeiro','O que precisa de atenção','Revisar pipeline comercial','Acessos principais']) {
  must(!dashboardBrowser.includes(legacy), `Executive Dashboard still contains legacy CRM structure: ${legacy}`);
}
[
  'Receita Consolidada',
  'R$ 275.000',
  'Music OS 360</h3><p>SaaS / Plataforma',
  '23 novas vendas',
  'R$ 18.500 recebido',
  'Protótipo · dados ilustrativos',
  'Empresa: Visa Fácil'
].forEach((token)=>must(!dashboardBrowser.includes(token), `Dashboard canonical browser still contains fake/demo token: ${token}`));
must(dashboardBrowser.includes('Visão financeira-gerencial consolidada da Valtren Solutions e performance das suas unidades econômicas internas.'), 'Dashboard canonical Page Header description must be preserved');
must(dashboardBrowser.includes('Nenhum número foi inventado'), 'Dashboard error state must explicitly prohibit invented numbers');
must(dashboardCss.includes('/* VALTREN EXECUTIVE DASHBOARD */'), 'Executive Dashboard CSS marker missing');
must(dashboardCss.includes('grid-template-columns:repeat(4,minmax(0,1fr))'), 'Executive Dashboard desktop KPI grid missing');
must(runner.includes('Dashboard materializer idempotence: PASS'), 'materialization runner must enforce Dashboard idempotence');
must(runner.includes('Sidebar Architecture materializer idempotence: PASS'), 'materialization runner must enforce Sidebar Architecture idempotence');
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
    'R$ 18.500 recebido',
    'Empresa: Visa Fácil'
  ];
  forbidden.forEach((token) => must(!app.includes(token), `materialized app still contains fake/demo UI token: ${token}`));
  ['Autenticação desativada','Nenhuma identidade é simulada','Não configurado','Faturamento Bruto','Resultado Valtren','Performance por Unidade de Negócio'].forEach((token)=>must(app.includes(token), `materialized app missing canonical token: ${token}`));
  must((app.match(/VALTREN CRM DASHBOARD START/g)||[]).length === 1, 'Dashboard start marker must exist exactly once');
  must((app.match(/function crmDashboardPage\(/g)||[]).length === 1, 'crmDashboardPage must exist exactly once');
  const dashboardStart = app.indexOf('VALTREN CRM DASHBOARD START');
  const dashboardEnd = app.indexOf('VALTREN CRM DASHBOARD END', dashboardStart);
  must(dashboardStart >= 0 && dashboardEnd > dashboardStart, 'materialized Dashboard block boundaries must be valid');
  const materializedDashboard = app.slice(dashboardStart, dashboardEnd);
  for (const removed of [
    'Sistema Interno',
    'Visão Econômica Consolidada',
    'Empresa: Valtren Solutions · Produtos, SaaS, Serviços e Unidades de Negócio são dimensões gerenciais internas.'
  ]) {
    must(!materializedDashboard.includes(removed), `materialized Dashboard route re-emitted removed hierarchy copy: ${removed}`);
  }
  must(materializedDashboard.includes('Visão financeira-gerencial consolidada da Valtren Solutions e performance das suas unidades econômicas internas.'), 'materialized Dashboard must preserve canonical Page Header description');
  for (const kpi of ['Faturamento Bruto','Deduções e Impostos','Receita Líquida','Custos Diretos','Despesas Operacionais','Resultado Operacional','Participações / Repasses','Resultado Valtren']) {
    must(materializedDashboard.includes(kpi), `materialized Dashboard missing KPI after hierarchy cleanup: ${kpi}`);
  }
  must((app.match(/function crmHeaderActions\(/g)||[]).length === 1, 'crmHeaderActions must exist exactly once');
  must(app.includes('ValtrenDashboardParticipationCore'), 'Participation integrity core missing from materialized dashboard');
  must(app.includes('__participationIntegrityWrapped'), 'Participation double-count protection missing from materialized dashboard');
  must(app.includes("if(path==='/crm/juridico')return crmLegalMattersPage();"), 'Legal Matters owner route changed');
  must(app.includes("if(path==='/crm/juridico/contratos')return crmLegalContractsPage();"), 'Legal Contracts owner route changed');
  must(app.includes("if(path==='/crm/juridico/compliance')return crmCompliancePage();"), 'Compliance owner route changed');
  must(app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmIntellectualPropertyPage();"), 'IP owner route changed');
  must(app.includes("if(path==='/crm/juridico/societario')return crmCorporateGovernancePage();"), 'Corporate Governance owner route changed');
  must(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"), 'Economic Participations route changed');
  must(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"), 'Payouts route changed');
  must(css.includes('/* VALTREN EXECUTIVE DASHBOARD */'), 'Executive Dashboard CSS owner block missing');
  must(css.includes('/* VALTREN PRODUCT SYSTEM REVIEW */'), 'global design-system patch missing');
  must(css.includes('--crm-surface:'), 'centralized CRM visual tokens missing');
  must(css.includes('@media(max-width:760px)'), 'tablet/mobile responsive rules missing');
  must(css.includes('@media(max-width:480px)'), 'mobile responsive rules missing');
}

console.log(`product-system-review: PASS${materialized ? ' (materialized)' : ''}`);
