'use strict';
const fs=require('fs');
const path=require('path');

if(!process.argv.includes('--materialized')){
  throw new Error('Este wrapper existe somente para certificação --materialized.');
}

const targetArg=process.argv[2];
if(!targetArg)throw new Error('Informe o teste-base a executar.');
const targetPath=path.resolve(process.cwd(),targetArg);
const targetName=path.basename(targetPath);

const oldAssertions={
  'test_crm_fiscal_documents.js':`test('92 Administração continua com dois itens',()=>{assert(app.includes("['structure','Estrutura Organizacional'"));assert(app.includes("['assets','Patrimônio e Licenças'"));});`,
  'test_crm_cost_allocations.js':`test('84 Administração continua com dois itens',()=>{assert(app.includes("['structure','Estrutura Organizacional'"));assert(app.includes("['assets','Patrimônio e Licenças'"));});`,
  'test_crm_payouts.js':`test('Administração preserva dois itens atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);for(const item of ["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"])assert(admin.includes(item));});`,
  'test_crm_business.js':`test('Administração preserva dois itens canônicos',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);assert(admin.includes('Estrutura Organizacional'));assert(admin.includes('Patrimônio e Licenças'));});`,
};

const oldAssertion=oldAssertions[targetName];
if(!oldAssertion)throw new Error(`Teste-base sem contrato de Administração mapeado: ${targetName}`);

let source=fs.readFileSync(targetPath,'utf8');
const replaceExactly=(oldText,newText,expected,label)=>{
  const occurrences=source.split(oldText).length-1;
  if(occurrences!==expected)throw new Error(`${label} esperada ${expected} vez(es) em ${targetName}; encontrada ${occurrences}.`);
  source=source.split(oldText).join(newText);
};

const newAdministration=String.raw`test('Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
replaceExactly(oldAssertion,newAdministration,1,'Assertion materializada histórica de Administração');

const sidebarBoundarySpecs={
  'test_crm_fiscal_documents.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),side=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const side=app.slice(start,end);`,
    expected:1,
  },
  'test_crm_cost_allocations.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`,
    expected:2,
  },
  'test_crm_payouts.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`,
    expected:1,
  },
};
const boundary=sidebarBoundarySpecs[targetName];
if(boundary)replaceExactly(boundary.old,boundary.replacement,boundary.expected,'Boundary materializado histórico da Sidebar');

new Function('require','__dirname','__filename',source)(require,path.dirname(targetPath),targetPath);
