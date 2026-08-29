const assert=require('assert');
const fs=require('fs');
const path=require('path');
const browser=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','accounting','browser.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','accounting','styles.css'),'utf8');
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${passed} ${name}`);}catch(error){console.error(`FAIL ${name}: ${error.message}`);throw error;}}

test('UI consome crmFinanceService canônico',()=>{assert(browser.includes("typeof crmFinanceService!=='function'"));assert(browser.includes('financeService:()=>crmFinanceService()'));});
test('UI usa state.crmAccounting somente como metadado contábil',()=>{assert(browser.includes('state.crmAccounting=ValtrenAccountingCore.ensureState'));assert(!browser.includes('accountingRevenues'));assert(!browser.includes('dreTransactions'));});
test('views internas são DRE Lançamentos e Classificações',()=>{for(const label of ["['dre','DRE']","['entries','Lançamentos']","['classifications','Classificações']"])assert(browser.includes(label));});
test('seletor distingue Competência e Caixa',()=>{assert(browser.includes('>Competência</option>'));assert(browser.includes('>Caixa</option>'));});
test('filtro Produto/Sistema inclui Corporativo',()=>{assert(browser.includes('Todos os Produtos/Sistemas'));assert(browser.includes('>Corporativo</option>'));assert(browser.includes('crmAccountingProducts()'));});
test('Serviço não possui catálogo financeiro hardcoded',()=>{assert(browser.includes('crmAccountingServices()'));assert(browser.includes('Sem serviços cadastrados'));});
test('Unidade não possui catálogo financeiro hardcoded',()=>{assert(browser.includes('crmAccountingUnits()'));assert(browser.includes('Sem unidades cadastradas'));});
test('competência pode ser ajustada inline',()=>{assert(browser.includes('data-action="crm-acct-recognition"'));assert(browser.includes('setTransactionAccounting(t.dataset.id,{recognitionDate:t.value})'));});
test('override contábil pode ser ajustado inline',()=>{assert(browser.includes('crm-acct-classification-override'));assert(browser.includes('{classificationId:t.value}'));});
test('categoria financeira é somente leitura em lançamentos',()=>{assert(browser.includes('<th>Categoria Financeira</th>'));assert(!browser.includes('data-action="crm-acct-category"'));});
test('mapeamento Categoria para Classificação fica interno',()=>{assert(browser.includes('Mapeamento Categoria → Classificação'));assert(browser.includes('data-action="crm-acct-mapping"'));});
test('pendências contábeis são visíveis',()=>{assert(browser.includes('movimentação'));assert(browser.includes('sem classificação'));assert(browser.includes('sem competência'));});
test('DRE possui linhas gerenciais obrigatórias',()=>{for(const label of ['Receita Bruta','Receita Líquida','Custos','Resultado Bruto','Despesas Operacionais','Resultado Operacional','Resultado Final'])assert(browser.includes(label));});
test('margens são apresentadas sem gráfico substituindo DRE',()=>{assert(browser.includes('Margem Bruta'));assert(browser.includes('Margem Operacional'));assert(browser.includes('<table>'));});
test('comparação com período anterior é opcional',()=>{assert(browser.includes('Comparar período anterior'));assert(browser.includes('previousPeriod'));});
test('drill-down consulta linhas e oferece Ver transação',()=>{assert(browser.includes('service.drillDown(target,f)'));assert(browser.includes('Ver transação'));assert(browser.includes('crm-acct-drawer'));});
test('lançamentos oferecem Ver em Transações sem editor financeiro duplicado',()=>{assert(browser.includes('Ver em Transações'));assert(!browser.includes('crmFinanceOpenTransactionModal'));});
test('estado vazio não inventa números',()=>{assert(browser.includes('Nenhum dado contábil para este período.'));assert(browser.includes("has?crmAccountingMoney(v):'—'"));});
test('P&L por dimensão não existe na nova UI',()=>{for(const label of ['P&L Empresa','P&L Projetos','P&L Artistas','P&L por Projeto','P&L por Artista'])assert(!browser.includes(label));});
test('CSS preserva DRE e classificação em larguras menores',()=>{for(const width of ['1380px','1050px','760px','520px'])assert(css.includes(`max-width:${width}`));assert(css.includes('.crm-acct-entry-table'));assert(css.includes('.crm-acct-dre-card'));});
test('drawer respeita viewport',()=>{assert(css.includes('width:min(820px,100%)'));assert(css.includes('.crm-acct-drawer-body{min-height:0;overflow:auto'));});
test('Serviço e Unidade são escondidos antes de dados essenciais',()=>{assert(css.includes('nth-child(7)'));assert(css.includes('nth-child(8)'));assert(css.includes('nth-child(4)'));});
test('estrutura não se apresenta como razão legal de partidas dobradas',()=>{assert(browser.includes('Não representa um plano legal completo de partidas dobradas.'));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
  const bundleCss=fs.readFileSync(path.join(__dirname,'..','assets','valtren-brand.css'),'utf8');
  test('UI contábil final está no bundle',()=>{assert(app.includes('function crmAccountingDreView'));assert(app.includes('function crmAccountingEntriesView'));assert(app.includes('function crmAccountingClassificationsView'));});
  test('rota efetiva de Contabilidade é canônica e nenhuma rota legada sobrevive',()=>{const canonical="if(path==='/crm/financeiro/accounting')return crmAccountingPage();";assert(app.includes(canonical));assert(!app.includes("if(path==='/crm/financeiro/accounting')return crmRefAccountingPage();"));const routeStart=app.lastIndexOf('function crmReferenceRoute');const routeEnd=app.indexOf('return null;',routeStart);assert(app.slice(routeStart,routeEnd).includes(canonical));});
  test('P&L legado não sobrevive ao bundle',()=>{for(const label of ['P&L Empresa','P&L Projetos','P&L Artistas','P&L por Projeto','P&L por Artista'])assert(!app.includes(label));});
  test('CSS responsivo Contabilidade está no bundle',()=>{assert(bundleCss.includes('/* VALTREN ACCOUNTING */'));assert(bundleCss.includes('@media(max-width:520px)'));});
}
console.log(`Accounting UI tests: ${passed} passed`);
