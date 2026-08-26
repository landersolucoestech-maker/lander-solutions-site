'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_accounting.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldAdministration=`test('68 Administração mantém dois itens',()=>{assert(app.includes('Estrutura Organizacional'));assert(app.includes('Patrimônio e Licenças'))});`;
  const newAdministration=String.raw`test('68 Administração legacy preservada fora da Sidebar',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end),compact=app.replace(/\s+/g,'');assert(start>=0&&end>start);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));assert(compact.includes("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'"));assert(compact.includes('Áreaadministrativaaindanãoimplementadacomodomíniooperacional.'));});`;
  const occurrences=source.split(oldAdministration).length-1;
  if(occurrences!==1)throw new Error(`Assertion materializada histórica de Administração esperada exatamente 1 vez em Accounting; encontrada ${occurrences}`);
  source=source.replace(oldAdministration,newAdministration);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
