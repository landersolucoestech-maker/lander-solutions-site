'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_legal_contracts_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const replaceExactly=(oldText,newText,expected,label)=>{
    const occurrences=source.split(oldText).length-1;
    if(occurrences!==expected)throw new Error(`${label} esperada ${expected} vez(es) em Legal Contracts UI; encontrada ${occurrences}`);
    source=source.split(oldText).join(newText);
  };
  const oldParticipation=`test('Participações não foi implementado pelo bundle contratual',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage"));});`;
  const newParticipation=`test('Participações é materializada após Contratos preservando o feed jurídico',()=>{assert(app.includes("if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"));assert(app.includes('function crmContractEconomicRulesFeed(filters={})'));assert(app.includes('function crmContractResolveEconomicRuleForPeriod(input={})'));});`;
  const oldPayout=`test('Repasses não foi implementado pelo bundle contratual',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  const newPayout=`test('Repasses é materializado após Participações sem transferir ownership jurídico',()=>{assert(app.includes("if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"));assert(app.includes('function crmParticipationObligationsFeed(filters={})'));assert(!app.includes("if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage"));});`;
  const oldAdministration=`test('regressão: Administração mantém os dois itens canônicos atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end),canonical=["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"];assert(start>=0&&end>start);assert.equal(canonical.filter((item)=>admin.includes(item)).length,2);for(const item of canonical)assert(admin.includes(item));assert(!admin.includes('Auditoria'));assert(!admin.includes('Integrações'));});`;
  const newAdministration=String.raw`test('regressão: Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const oldLegalSidebar=`test('sidebar Jurídico mantém a arquitetura oficial',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);hasAll(sidebar,['Assuntos Jurídicos','Contratos','Templates','Variáveis','Compliance e Políticas','Propriedade Intelectual','Societário','#/crm/juridico/contratos','#/crm/juridico/contratos/templates','#/crm/juridico/contratos/variaveis']);});`;
  const newLegalSidebar=`test('sidebar Jurídico mantém cinco entradas oficiais e Contratos concentra Templates/Variáveis no header',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);hasAll(sidebar,['Assuntos Jurídicos','Contratos','Compliance e Políticas','Propriedade Intelectual','Societário','#/crm/juridico/contratos']);assert(!sidebar.includes('#/crm/juridico/contratos/templates'));assert(!sidebar.includes('#/crm/juridico/contratos/variaveis'));assert(app.includes('class="crm-legal-secondary-action" href="#/crm/juridico/contratos/templates">Templates</a>'));assert(app.includes('class="crm-legal-secondary-action" href="#/crm/juridico/contratos/variaveis">Variáveis</a>'));});`;
  replaceExactly(oldParticipation,newParticipation,1,'Assertion materializada obsoleta de Participações');
  replaceExactly(oldPayout,newPayout,1,'Assertion materializada obsoleta de Repasses');
  replaceExactly(oldAdministration,newAdministration,1,'Assertion materializada obsoleta de Administração');
  replaceExactly(oldLegalSidebar,newLegalSidebar,1,'Assertion materializada obsoleta da Sidebar Jurídico');
  const oldBoundary=`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`;
  const newBoundary=`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`;
  replaceExactly(oldBoundary,newBoundary,3,'Boundary materializado histórico da Sidebar');
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
