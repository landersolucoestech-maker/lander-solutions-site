'use strict';
const fs=require('fs');
const path=require('path');

const specs={
  'test_crm_complete.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar');const end=app.indexOf('function crmReferenceRoute',start);const sidebar=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START');const end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`,
    expected:2,
  },
  'test_crm_complete_hardening.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`,
    expected:1,
  },
  'test_crm_financial_transactions.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);`,
    expected:2,
  },
  'test_crm_fiscal_documents_ui.js':{
    old:`const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),side=app.slice(start,end);`,
    replacement:`const start=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const side=app.slice(start,end);`,
    expected:1,
  },
  'test_crm_legal_matters_ui.js':{
    old:`const a=app.lastIndexOf('function crmRelSidebar'),b=app.indexOf('function crmReferenceRoute',a),s=app.slice(a,b);`,
    replacement:`const a=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE START'),b=app.indexOf('// VALTREN SIDEBAR ARCHITECTURE END',a);assert(a>=0&&b>a);const s=app.slice(a,b);`,
    expected:1,
  },
};

function transform(source,targetName){
  const spec=specs[targetName];
  if(!spec)throw new Error(`Teste-base sem boundary materializado mapeado: ${targetName}`);
  const occurrences=source.split(spec.old).length-1;
  if(occurrences!==spec.expected)throw new Error(`Boundary materializado histórico esperado ${spec.expected} vez(es) em ${targetName}; encontrado ${occurrences}`);
  return source.split(spec.old).join(spec.replacement);
}

function execute(source,targetPath){
  new Function('require','__dirname','__filename',source)(require,path.dirname(targetPath),targetPath);
}

function runBase(basePath,targetName){
  let source=fs.readFileSync(basePath,'utf8');
  if(process.argv.includes('--materialized'))source=transform(source,targetName);
  execute(source,basePath);
}

module.exports={specs,transform,runBase};

if(require.main===module){
  if(!process.argv.includes('--materialized'))throw new Error('Execução direta deste wrapper existe somente para certificação --materialized.');
  const targetArg=process.argv[2];
  if(!targetArg)throw new Error('Informe o teste-base a executar.');
  const targetPath=path.resolve(process.cwd(),targetArg);
  execute(transform(fs.readFileSync(targetPath,'utf8'),path.basename(targetPath)),targetPath);
}
