'use strict';
const __partFs=require('fs');
const __partPath=require('path');
const __partDir=__partPath.join(__dirname,'parts','tests','economic_participations');
const __partPrefix=__partPath.basename(__filename)+'.part';
let __partSource=__partFs.readdirSync(__partDir).filter((name)=>name.startsWith(__partPrefix)).sort().map((name)=>__partFs.readFileSync(__partPath.join(__partDir,name),'utf8')).join('');
const __legacyCore="require('./crm_economic_participations_core.js')";
const __canonicalCore="require('../web/src/modules/finance/participations/core.js')";
const __coreRefs=__partSource.split(__legacyCore).length-1;
if(__coreRefs!==1)throw new Error(`Referência legacy do core de Participações esperada exatamente 1 vez; encontrada ${__coreRefs}`);
__partSource=__partSource.replace(__legacyCore,__canonicalCore);
if(process.argv.includes('--materialized')){
  const oldAdministration=`test('Administração mantém dois itens canônicos atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);for(const item of ["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"])assert(admin.includes(item));assert(!admin.includes('Auditoria'));});`;
  const newAdministration=String.raw`test('Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const occurrences=__partSource.split(oldAdministration).length-1;
  if(occurrences!==1)throw new Error(`Assertion materializada histórica de Administração esperada exatamente 1 vez em Participações; encontrada ${occurrences}`);
  __partSource=__partSource.replace(oldAdministration,newAdministration);
}
new Function('require','__dirname','__filename',__partSource)(require,__dirname,__filename);