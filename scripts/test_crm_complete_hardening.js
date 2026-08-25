'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');

const hardening=fs.readFileSync(path.join(__dirname,'crm_complete_hardening.js'),'utf8');
const browser=fs.readFileSync(path.join(__dirname,'crm_complete_browser.js'),'utf8');
const modulePatch=fs.readFileSync(path.join(__dirname,'crm_complete_module.py'),'utf8');
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${name}`);}catch(error){console.error(`FAIL ${name}`);throw error;}}

test('1 projeção de contato usa adapter em modo de compatibilidade sem criar organização paralela',()=>{assert(hardening.includes("crmCanonicalUpsertLegacyRecord('contacts',item,mode,{legacy:true})"));});
test('2 projeção de lead usa adapter em modo de compatibilidade sem criar organização paralela',()=>{assert(hardening.includes("crmCanonicalUpsertLegacyRecord('leads',item,mode,{legacy:true})"));});
test('3 arquivar contato/empresa remove binding legado sem destruir identidade',()=>{assert(hardening.includes("crmCanonicalRemoveLegacyRecord('contacts',legacyId)"));assert(hardening.includes('archiveEntityContext(entityType,id)'));});
test('4 arquivar lead remove projeção legada',()=>{assert(hardening.includes("crmCanonicalRemoveLegacyRecord('leads',lead.legacyId)"));});
test('5 edição de Cliente trava tipo de identidade canônica',()=>{assert(hardening.includes("form?.dataset?.kind==='customer'"));assert(hardening.includes("form?.dataset?.mode==='edit'"));assert(hardening.includes('type.disabled=true'));});
test('6 papéis técnicos internos não são exibidos como badges de negócio',()=>{const roleFn=hardening.slice(hardening.indexOf('function crmFullRoleBadges'),hardening.indexOf('function crmFullSyncLegacyContact'));assert(!roleFn.includes("'crm_contact'"));assert(!roleFn.includes("'organization_contact'"));});
test('7 status e prioridades possuem labels em português',()=>{assert(hardening.includes("active:'Ativo'"));assert(hardening.includes("converted:'Convertido'"));assert(hardening.includes("medium:'Média'"));assert(hardening.includes("strategic:'Estratégica'"));});
test('8 materializador inclui hardening no mesmo bloco do CRM',()=>{assert(modulePatch.includes('HARDENING_JS'));assert(modulePatch.includes('VALTREN CRM COMPLETE HARDENING'));});
test('9 CRM completo não cria lista independente de prospects/partners/suppliers/providers',()=>{for(const forbidden of ['state.crmProspects','state.crmPartners','state.crmSuppliers','state.crmServiceProviders'])assert(!browser.includes(forbidden));});
test('10 nenhum write direto novo em projeções legadas',()=>{const combined=browser+'\n'+hardening;assert(!/state\.crmRelContacts\s*=|state\.crmRelContacts\.(?:push|unshift|splice)/.test(combined));assert(!/state\.crmRelLeads\s*=|state\.crmRelLeads\.(?:push|unshift|splice)/.test(combined));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  test('11 hardening está no bundle materializado',()=>{assert(app.includes('VALTREN CRM COMPLETE HARDENING'));assert(app.includes("crmCanonicalUpsertLegacyRecord('contacts',item,mode,{legacy:true})"));});
  test('12 labels localizados foram aplicados ao bundle',()=>{assert(app.includes('crmFullStatusLabel(context.status'));assert(app.includes('crmFullPriorityLabel(lead.priority)'));});
  test('13 navegação oficial continua sem submenu do CRM',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);assert(sidebar.includes("nav('#/crm/relationships','CRM'"));assert(!sidebar.includes("subgroup('relationships'"));});
}

console.log(`CRM hardening tests: ${passed} passed`);
