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

const sourceRewrites={
  'test_crm_complete.js':[
    ["require('./crm_canonical_parties_core.js')","require('../web/src/modules/crm/parties/core.js')"],
    ["require('./crm_complete_domain.js')","require('../web/src/modules/crm/workspace/domain.js')"],
    ["path.join(__dirname,'crm_complete_browser.js')","path.join(__dirname,'..','web','src','modules','crm','workspace','browser.js')"],
  ],
  'test_crm_complete_hardening.js':[
    ["path.join(__dirname,'crm_complete_hardening.js')","path.join(__dirname,'..','web','src','modules','crm','workspace','hardening.js')"],
    ["path.join(__dirname,'crm_complete_browser.js')","path.join(__dirname,'..','web','src','modules','crm','workspace','browser.js')"],
  ],
  'test_crm_financial_transactions.js':[
    ["require('./crm_canonical_parties_core.js')","require('../web/src/modules/crm/parties/core.js')"],
    ["require('./crm_financial_transactions_domain.js')","require('../web/src/modules/finance/transactions/core.js')"],
    ["path.join(__dirname,'crm_financial_transactions_browser.js')","path.join(__dirname,'..','web','src','modules','finance','transactions','browser.js')"],
    ["path.join(__dirname,'crm_financial_transactions_domain.js')","path.join(__dirname,'..','web','src','modules','finance','transactions','core.js')"],
  ],
  'test_crm_fiscal_documents_ui.js':[
    ["path.join(__dirname,'crm_fiscal_documents_browser.js')","path.join(__dirname,'..','web','src','modules','finance','fiscal','browser.js')"],
    ["path.join(__dirname,'crm_fiscal_documents.css')","path.join(__dirname,'..','web','src','modules','finance','fiscal','styles.css')"],
  ],
  'test_crm_legal_matters_ui.js':[
    ["path.resolve(__dirname,'crm_legal_matters_browser.js')","path.resolve(__dirname,'..','web','src','modules','legal','matters','browser.js')"],
    ["path.resolve(__dirname,'crm_legal_matters.css')","path.resolve(__dirname,'..','web','src','modules','legal','matters','styles.css')"],
  ],
};

const materializedRewrites={
  'test_crm_fiscal_documents_ui.js':[
    [
      "assert(app.includes('function crmTransactionsPage()'));assert(app.includes('function crmAccountingPage()'));",
      "assert(app.includes('function crmTransactionsPage()')||app.includes('crmTransactionsPage=function()'));assert(app.includes('function crmAccountingPage()'));",
      1,
    ],
  ],
};

function rewriteSources(source,targetName){
  for(const [legacy,canonical] of sourceRewrites[targetName]||[]){
    const occurrences=source.split(legacy).length-1;
    if(occurrences<1)throw new Error(`Source histórico esperado em ${targetName}: ${legacy}`);
    source=source.split(legacy).join(canonical);
  }
  return source;
}

function rewriteMaterializedContracts(source,targetName){
  for(const [legacy,canonical,expected] of materializedRewrites[targetName]||[]){
    const occurrences=source.split(legacy).length-1;
    if(occurrences!==expected)throw new Error(`Contrato materializado histórico esperado ${expected} vez(es) em ${targetName}; encontrado ${occurrences}: ${legacy}`);
    source=source.split(legacy).join(canonical);
  }
  return source;
}

function transform(source,targetName){
  const spec=specs[targetName];
  if(!spec)throw new Error(`Teste-base sem boundary materializado mapeado: ${targetName}`);
  const occurrences=source.split(spec.old).length-1;
  if(occurrences!==spec.expected)throw new Error(`Boundary materializado histórico esperado ${spec.expected} vez(es) em ${targetName}; encontrado ${occurrences}`);
  source=source.split(spec.old).join(spec.replacement);
  return rewriteMaterializedContracts(source,targetName);
}

function execute(source,targetPath){
  new Function('require','__dirname','__filename',source)(require,path.dirname(targetPath),targetPath);
}

function runBase(basePath,targetName){
  let source=rewriteSources(fs.readFileSync(basePath,'utf8'),targetName);
  if(process.argv.includes('--materialized'))source=transform(source,targetName);
  execute(source,basePath);
}

module.exports={specs,transform,runBase};

if(require.main===module){
  if(!process.argv.includes('--materialized'))throw new Error('Execução direta deste wrapper existe somente para certificação --materialized.');
  const targetArg=process.argv[2];
  if(!targetArg)throw new Error('Informe o teste-base a executar.');
  const targetPath=path.resolve(process.cwd(),targetArg);
  const targetName=path.basename(targetPath).replace('.base.js','.js');
  execute(transform(rewriteSources(fs.readFileSync(targetPath,'utf8'),targetName),targetName),targetPath);
}