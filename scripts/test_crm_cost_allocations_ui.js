'use strict';
const fs=require('fs');
const path=require('path');
const basePath=path.resolve(__dirname,'test_crm_cost_allocations_ui.base.js');
let source=fs.readFileSync(basePath,'utf8');
const sourceRewrites=[
  ["path.join(__dirname,'crm_cost_allocations_browser.js')","path.join(__dirname,'..','web','src','modules','finance','allocations','browser.js')"],
  ["path.join(__dirname,'crm_cost_allocations.css')","path.join(__dirname,'..','web','src','modules','finance','allocations','styles.css')"],
  ["path.join(__dirname,'crm_cost_allocations_core.js')","path.join(__dirname,'..','web','src','modules','finance','allocations','core.js')"],
];
for(const [legacy,canonical] of sourceRewrites){
  const occurrences=source.split(legacy).length-1;
  if(occurrences!==1)throw new Error(`Source histórico de Rateios UI esperado exatamente 1 vez: ${legacy}; encontrado ${occurrences}`);
  source=source.replace(legacy,canonical);
}
if(process.argv.includes('--materialized')){
  const oldSidebarOfficial=`test('74 sidebar publicado continua oficial',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);['Transações','Contabilidade','Notas Fiscais','Rateios','Participações','Repasses'].forEach((x)=>assert(sidebar.includes(x)));});`;
  const newSidebarOfficial=`test('74 sidebar publicado continua oficial no bloco canônico',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end);assert(start>=0&&end>start);['Transações','Contabilidade','Notas Fiscais','Rateios','Participações','Repasses'].forEach((x)=>assert(sidebar.includes(x)));});`;
  const oldSidebarBoundary=`test('75 nenhum subitem de Rateios foi publicado no sidebar',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);['Direcionadores','Critérios de Rateio','Alocações','Memória de Cálculo'].forEach((x)=>assert(!sidebar.includes(x)));});`;
  const newSidebarBoundary=`test('75 nenhum subitem de Rateios foi publicado no sidebar canônico',()=>{const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start),sidebar=app.slice(start,end);assert(start>=0&&end>start);['Direcionadores','Critérios de Rateio','Alocações','Memória de Cálculo'].forEach((x)=>assert(!sidebar.includes(x)));});`;
  for(const [label,oldAssertion,newAssertion] of [
    ['74',oldSidebarOfficial,newSidebarOfficial],
    ['75',oldSidebarBoundary,newSidebarBoundary],
  ]){
    const occurrences=source.split(oldAssertion).length-1;
    if(occurrences!==1)throw new Error(`Assertion materializada ${label} de boundary da Sidebar de Rateios UI esperada exatamente 1 vez; encontrada ${occurrences}`);
    source=source.replace(oldAssertion,newAssertion);
  }
}
new Function('require','__dirname','__filename',source)(require,__dirname,__filename);