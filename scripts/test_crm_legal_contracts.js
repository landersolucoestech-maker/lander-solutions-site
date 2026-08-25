'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_legal_contracts.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldTest=`test('Participações permanece placeholder',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage"));});`;
  const newTest=`test('Participações é materializada pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"));assert(app.includes('function crmContractEconomicRulesFeed(filters={})'));assert(app.includes('function crmContractResolveEconomicRuleForPeriod(input={})'));});`;
  if(!source.includes(oldTest))throw new Error('Assertion materializada obsoleta de Participações não encontrada em Legal Contracts');
  source=source.replace(oldTest,newTest);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
