'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${name}`);}catch(error){console.error(`FAIL ${name}`);throw error;}}
const browser=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','transactions','browser.js'),'utf8');
const presentation=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','transactions','presentation.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','transactions','styles.css'),'utf8');

test('1 busca inclui contraparte/categoria/produto na resolução',()=>{assert(browser.includes('function crmFinanceSearchBlob'));assert(browser.includes('crmFinanceCounterpartyLabel(tx)'));assert(browser.includes('crmFinanceCategoryLabel(tx.categoryId)'));assert(browser.includes('crmFinanceProductLabel(tx)'));});
test('2 classificação financeira pode ser alterada inline',()=>{assert(browser.includes('data-action="crm-fin-nature"'));assert(browser.includes("service.setClassification(target.dataset.id,{financialNature:target.value}"));});
test('3 ações em massa incluem Origem/Destino',()=>{assert(browser.includes('crm-fin-bulk-counterparty'));assert(browser.includes("service.bulk(crmFinanceUi().selected,'counterparty'"));});
test('4 edição de transação existe sem sobrescrever descrição original importada',()=>{assert(browser.includes("action==='crm-fin-edit'"));assert(browser.includes('Descrição original preservada da fonte'));assert(browser.includes("tx&&tx.source!=='manual'?'readonly"));});
test('5 regras automáticas possuem interface interna em Transações',()=>{assert(browser.includes('function crmFinanceOpenRules'));assert(browser.includes('crm-fin-rule-form'));assert(browser.includes('service.createRule'));});
test('6 configuração de colunas secundárias funciona',()=>{assert(browser.includes('function crmFinanceColumnControl'));assert(browser.includes('data-fin-column'));assert(css.includes('hide-counterparty'));assert(css.includes('hide-status'));assert(css.includes('hide-indicators'));});
test('7 colunas essenciais não são configuráveis para ocultação',()=>{const start=browser.indexOf('function crmFinanceColumnControl'),end=browser.indexOf('function crmFinanceToolbar',start),block=browser.slice(start,end);for(const label of ['Data','Descrição','Valor','Categoria','Produto/Sistema','Ação'])assert(!block.includes(`'${label}'`));});
test('8 responsividade mantém Categoria e Produto/Sistema em mobile',()=>{const mobile=css.slice(css.indexOf('@media(max-width:640px)'));assert(!/nth-child\(7\)|nth-child\(8\)/.test(mobile));assert(mobile.includes('min-width:820px'));});
test('9 modais e drawer respeitam viewport',()=>{assert(css.includes('max-height:90vh'));assert(css.includes('max-height:94vh'));assert(css.includes('width:min(560px,100%)'));});
test('10 atualização não simula sincronização bancária',()=>{assert(browser.includes('Nenhuma sincronização foi simulada'));assert(!browser.includes('Sincronização concluída'));});
test('11 apresentação final unifica Saída e Entrada em Valor',()=>{assert(presentation.includes('<th class="right">Valor</th>'));assert(!presentation.includes('<th class="right">Saída</th>'));assert(!presentation.includes('<th class="right">Entrada</th>'));assert(presentation.includes('function crmFinanceSignedMoney'));assert(presentation.includes("tx?.direction==='outflow'?-amount:amount"));});
test('12 apresentação final não renderiza cards de status',()=>{const start=presentation.indexOf('function crmTransactionsPage()'),block=presentation.slice(start);assert(start>=0);assert(!block.includes('crmFinanceStatusTabs()'));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  test('13 UI operacional final está no bundle',()=>{for(const marker of ['crm-fin-bulk-counterparty','crm-fin-rule-form','crm-fin-nature','crm-fin-column-config','crmFinanceSignedMoney'])assert(app.includes(marker));});
  test('14 rota publicada continua única em Financeiro → Transações',()=>{assert(app.includes("if(path==='/crm/financeiro')return crmTransactionsPage();"));});
  test('15 apresentação materializada possui apenas a coluna monetária Valor',()=>{const start=app.indexOf('// VALTREN FINANCIAL TRANSACTIONS PRESENTATION'),end=app.indexOf('// VALTREN FINANCIAL TRANSACTIONS END',start),block=app.slice(start,end);assert(start>=0&&end>start);assert.strictEqual((block.match(/<th class="right">Valor<\/th>/g)||[]).length,1);assert(!block.includes('<th class="right">Saída</th>'));assert(!block.includes('<th class="right">Entrada</th>'));});
}
console.log(`Financial Transactions UI tests: ${passed} passed`);
