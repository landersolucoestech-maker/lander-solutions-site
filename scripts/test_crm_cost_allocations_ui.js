'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_cost_allocations_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
if(process.argv.includes('--materialized')){
  const oldSidebarBoundary=`test('75 nenhum subitem de Rateios foi publicado no sidebar',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);['Direcionadores','Critérios de Rateio','Alocações','Memória de Cálculo'].forEach((x)=>assert(!sidebar.includes(x)));});`;
  const newSidebarBoundary=`test('75 nenhum subitem de Rateios foi publicado no sidebar canônico',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end);assert(start>=0&&end>start);['Direcionadores','Critérios de Rateio','Alocações','Memória de Cálculo'].forEach((x)=>assert(!sidebar.includes(x)));});`;
  const occurrences=source.split(oldSidebarBoundary).length-1;
  if(occurrences!==1)throw new Error(`Assertion materializada de boundary da Sidebar de Rateios UI esperada exatamente 1 vez; encontrada ${occurrences}`);
  source=source.replace(oldSidebarBoundary,newSidebarBoundary);
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);
