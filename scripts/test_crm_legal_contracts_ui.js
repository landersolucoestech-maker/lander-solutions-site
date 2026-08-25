'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_legal_contracts_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldTest=`test('Participações não foi implementado pelo bundle contratual',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage"));});`;
  const newTest=`test('Participações é materializada após Contratos preservando o feed jurídico',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"));assert(app.includes('function crmContractEconomicRulesFeed(filters={})'));assert(app.includes('function crmContractResolveEconomicRuleForPeriod(input={})'));});`;
  if(!source.includes(oldTest))throw new Error('Assertion materializada obsoleta de Participações não encontrada em Legal Contracts UI');
  source=source.replace(oldTest,newTest);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
