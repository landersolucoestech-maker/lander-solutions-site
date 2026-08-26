'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_legal_contracts_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldParticipation=`test('Participações não foi implementado pelo bundle contratual',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage"));});`;
  const newParticipation=`test('Participações é materializada após Contratos preservando o feed jurídico',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"));assert(app.includes('function crmContractEconomicRulesFeed(filters={})'));assert(app.includes('function crmContractResolveEconomicRuleForPeriod(input={})'));});`;
  const oldPayout=`test('Repasses não foi implementado pelo bundle contratual',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  const newPayout=`test('Repasses é materializado após Participações sem transferir ownership jurídico',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"));assert(app.includes('function crmParticipationObligationsFeed(filters={})'));assert(!app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  if(!source.includes(oldParticipation))throw new Error('Assertion materializada obsoleta de Participações não encontrada em Legal Contracts UI');
  if(!source.includes(oldPayout))throw new Error('Assertion materializada obsoleta de Repasses não encontrada em Legal Contracts UI');
  source=source.replace(oldParticipation,newParticipation).replace(oldPayout,newPayout);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
