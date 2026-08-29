'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${name}`);}catch(error){console.error(`FAIL ${name}`);throw error;}}
const browser=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','transactions','browser.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','transactions','styles.css'),'utf8');

test('1 busca inclui contraparte/categoria/produto na resolução',()=>{assert(browser.includes('function crmFinanceSearchBlob'));assert(browser.includes('crmFinanceCounterpartyLabel(tx)'));assert(browser.includes('crmFinanceCategoryLabel(tx.categoryId)'));assert(browser.includes('crmFinanceProductLabel(tx)'));});
test('2 classificação financeira pode ser alterada inline',()=>{assert(browser.includes('data-action="crm-fin-nature"'));assert(browser.includes("service.setClassification(target.dataset.id,{financialNature:target.value}"));});
test('3 ações em massa incluem Origem/Destino',()=>{assert(browser.includes('crm-fin-bulk-counterparty'));assert(browser.includes("service.bulk(crmFinanceUi().selected,'counterparty'"));});
test('4 edição de transação existe sem sobrescrever descrição original importada',()=>{assert(browser.includes("action==='crm-fin-edit'"));assert(browser.includes('Descrição original preservada da fonte'));assert(browser.includes("tx&&tx.source!=='manual'?'readonly"));});
test('5 regras automáticas possuem interface interna em Transações',()=>{assert(browser.includes('function crmFinanceOpenRules'));assert(browser.includes('crm-fin-rule-form'));assert(browser.includes('service.createRule'));});
test('6 configuração de colunas secundárias funciona',()=>{assert(browser.includes('function crmFinanceColumnControl'));assert(browser.includes('data-fin-column'));assert(css.includes('hide-counterparty'));assert(css.includes('hide-status'));assert(css.includes('hide-indicators'));});
test('7 colunas essenciais não são configuráveis para ocultação',()=>{const start=browser.indexOf('function crmFinanceColumnControl'),end=browser.indexOf('function crmFinanceToolbar',start),block=browser.slice(start,end);for(const label of ['Data','Descrição','Saída','Entrada','Categoria','Produto/Sistema','Ação'])assert(!block.includes(`'${label}'`));});
test('8 responsividade mantém Categoria e Produto/Sistema em mobile',()=>{const mobile=css.slice(css.indexOf('@media(max-width:640px)'));assert(!/nth-child\(7\)|nth-child\(8\)/.test(mobile));assert(mobile.includes('min-width:820px'));});
test('9 modais e drawer respeitam viewport',()=>{assert(css.includes('max-height:90vh'));assert(css.includes('max-height:94vh'));assert(css.includes('width:min(560px,100%)'));});
test('10 atualização não simula sincronização bancária',()=>{assert(browser.includes('Nenhuma sincronização foi simulada'));assert(!browser.includes('Sincronização concluída'));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  test('11 UI operacional final está no bundle',()=>{for(const marker of ['crm-fin-bulk-counterparty','crm-fin-rule-form','crm-fin-nature','crm-fin-column-config'])assert(app.includes(marker));});
  test('12 rota publicada continua única em Financeiro → Transações',()=>{assert(app.includes("if(path==='/crm/financeiro')return crmTransactionsPage();"));});
}
console.log(`Financial Transactions UI tests: ${passed} passed`);
