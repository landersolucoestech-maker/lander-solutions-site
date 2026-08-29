'use strict';
const __partFs=require('fs');
const __partPath=require('path');
const __partDir=__partPath.join(__dirname,'parts','tests','economic_participations');
const __partPrefix=__partPath.basename(__filename)+'.part';
let __partSource=__partFs.readdirSync(__partDir).filter((name)=>name.startsWith(__partPrefix)).sort().map((name)=>__partFs.readFileSync(__partPath.join(__partDir,name),'utf8')).join('');
if(process.argv.includes('--materialized')){
  const replaceExactly=(oldText,newText,expected,label)=>{
    const occurrences=__partSource.split(oldText).length-1;
    if(occurrences!==expected)throw new Error(`${label} esperada ${expected} vez(es) em Participações UI; encontrada ${occurrences}`);
    __partSource=__partSource.split(oldText).join(newText);
  };
  const oldAdministration=`test('Administração preserva dois itens atuais',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);hasAll(admin,["['structure','Estrutura Organizacional','#/crm/administracao']","['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']"]);});`;
  const newAdministration=String.raw`test('Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  replaceExactly(oldAdministration,newAdministration,1,'Assertion materializada histórica de Administração');
  const oldBoundary=`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`;
  const newBoundary=`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`;
  replaceExactly(oldBoundary,newBoundary,2,'Boundary materializado histórico da Sidebar');
}
new Function('require','__dirname','__filename',__partSource)(require,__dirname,__filename);
