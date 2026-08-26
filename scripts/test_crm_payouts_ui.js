'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_payouts_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldAdministration=`test('Administração preserva dois itens atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);hasAll(admin,["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"]);});`;
  const newAdministration=String.raw`test('Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const occurrences=source.split(oldAdministration).length-1;
  if(occurrences!==1)throw new Error(`Assertion materializada histórica de Administração esperada exatamente 1 vez em Payouts UI; encontrada ${occurrences}`);
  source=source.replace(oldAdministration,newAdministration);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
