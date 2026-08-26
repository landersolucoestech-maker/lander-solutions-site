'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_accounting.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const replaceExactly=(oldText,newText,expected,label)=>{
    const occurrences=source.split(oldText).length-1;
    if(occurrences!==expected)throw new Error(`${label} esperada ${expected} vez(es) em Accounting; encontrada ${occurrences}`);
    source=source.split(oldText).join(newText);
  };
  const oldAdministration=`test('68 Administração mantém dois itens',()=>{assert(app.includes('Estrutura Organizacional'));assert(app.includes('Patrimônio e Licenças'))});`;
  const newAdministration=String.raw`test('68 Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  replaceExactly(oldAdministration,newAdministration,1,'Assertion materializada histórica de Administração');
  const oldBoundary=`const a=app.lastIndexOf('function crmRelSidebar'),b=app.indexOf('function crmReferenceRoute',a),s=app.slice(a,b);`;
  const newBoundary=`const a=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),b=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',a);assert(a>=0&&b>a);const s=app.slice(a,b);`;
  replaceExactly(oldBoundary,newBoundary,1,'Boundary materializado histórico da Sidebar');
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
