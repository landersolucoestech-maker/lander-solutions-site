'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_legal_contracts.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldLegalMatters=`test('Assuntos Jurídicos permanece fora de escopo',()=>{assert(app.includes("if(path==='/crm/juridico')return crmArchitecturePlaceholderPage('legal','matters','Assuntos Jurídicos');"));});`;
  const newLegalMatters=`test('Assuntos Jurídicos é materializado pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/juridico')return crmLegalMattersPage();"));assert(app.includes('function crmLegalMattersFeed'));assert(!app.includes("if(path==='/crm/juridico')return crmArchitecturePlaceholderPage('legal','matters','Assuntos Jurídicos');"));});`;
  const oldCompliance=`test('Compliance permanece fora de escopo',()=>{assert(app.includes("if(path==='/crm/juridico/compliance')return crmArchitecturePlaceholderPage"));});`;
  const newCompliance=`test('Compliance é materializado pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/juridico/compliance')return crmCompliancePage();"));assert(app.includes('function crmComplianceObligationsFeed'));assert(!app.includes("if(path==='/crm/juridico/compliance')return crmArchitecturePlaceholderPage"));});`;
  const oldIntellectualProperty=`test('Propriedade Intelectual permanece fora de escopo',()=>{assert(app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmArchitecturePlaceholderPage"));});`;
  const newIntellectualProperty=`test('Propriedade Intelectual é materializada pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmIntellectualPropertyPage();"));assert(app.includes('function crmIntellectualPropertyFeed'));assert(!app.includes("if(path==='/crm/juridico/propriedade-intelectual')return crmArchitecturePlaceholderPage"));});`;
  const oldCorporateGovernance=`test('Societário permanece fora de escopo',()=>{assert(app.includes("if(path==='/crm/juridico/societario')return crmArchitecturePlaceholderPage"));});`;
  const newCorporateGovernance=`test('Societário é materializado pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/juridico/societario')return crmCorporateGovernancePage();"));assert(app.includes('function crmCorporateStructureFeed'));assert(app.includes('corporate_ownership_is_not_economic_participation'));assert(!app.includes("if(path==='/crm/juridico/societario')return crmArchitecturePlaceholderPage"));});`;
  const oldParticipation=`test('Participações permanece placeholder',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage"));});`;
  const newParticipation=`test('Participações é materializada pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"));assert(app.includes('function crmContractEconomicRulesFeed(filters={})'));assert(app.includes('function crmContractResolveEconomicRuleForPeriod(input={})'));});`;
  const oldPayout=`test('Repasses permanece placeholder',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  const newPayout=`test('Repasses é materializado pela etapa posterior sem alterar Contratos',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"));assert(app.includes('function crmParticipationObligationsFeed(filters={})'));assert(!app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  const oldAdministration=`test('regressão: Administração preserva os dois itens canônicos atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end),canonical=["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"];assert(start>=0&&end>start);assert.equal(canonical.filter((item)=>admin.includes(item)).length,2);for(const item of canonical)assert(admin.includes(item));assert(!admin.includes('Auditoria'));assert(!admin.includes('Integrações'));});`;
  const newAdministration=String.raw`test('regressão: Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const replacements=[
    [oldLegalMatters,newLegalMatters,'Assuntos Jurídicos'],
    [oldCompliance,newCompliance,'Compliance'],
    [oldIntellectualProperty,newIntellectualProperty,'Propriedade Intelectual'],
    [oldCorporateGovernance,newCorporateGovernance,'Societário'],
    [oldParticipation,newParticipation,'Participações'],
    [oldPayout,newPayout,'Repasses'],
    [oldAdministration,newAdministration,'Administração'],
  ];
  for(const [oldAssertion,newAssertion,label] of replacements){
    const occurrences=source.split(oldAssertion).length-1;
    if(occurrences!==1)throw new Error(`Assertion materializada obsoleta de ${label} esperada exatamente 1 vez em Legal Contracts; encontrada ${occurrences}`);
    source=source.replace(oldAssertion,newAssertion);
  }
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
