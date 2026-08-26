'use strict';
const __partFs=require('fs');
const __partPath=require('path');
const __partPrefix=__filename+'.part';
let __partSource=__partFs.readdirSync(__dirname).filter((name)=>name.startsWith(__partPath.basename(__partPrefix))).sort().map((name)=>__partFs.readFileSync(__partPath.join(__dirname,name),'utf8')).join('');
if(process.argv.includes('--materialized')){
  const oldAdministration=`test('Administração preserva dois itens atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);hasAll(admin,["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"]);});`;
  const newAdministration=String.raw`test('Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const occurrences=__partSource.split(oldAdministration).length-1;
  if(occurrences!==1)throw new Error(`Assertion materializada histórica de Administração esperada exatamente 1 vez em Participações UI; encontrada ${occurrences}`);
  __partSource=__partSource.replace(oldAdministration,newAdministration);
}
new Function('require','__dirname','__filename',__partSource)(require,__dirname,__filename);
