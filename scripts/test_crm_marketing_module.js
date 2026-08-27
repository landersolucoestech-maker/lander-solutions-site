'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const browser=fs.readFileSync(path.resolve(__dirname,'crm_marketing_module.js'),'utf8');
const materializer=fs.readFileSync(path.resolve(__dirname,'crm_marketing_module.py'),'utf8');
for(const token of ['Visão Geral','Campanhas','Calendário','Métricas','Briefings','Tarefas','Nenhuma métrica é simulada','crmMarketingSave','crmMarketingPage'])assert(browser.includes(token),`ausente: ${token}`);
assert(browser.includes("localStorage.setItem(CRM_MARKETING_KEY"));
assert(!browser.includes('Math.random()*100'));
assert(materializer.includes("crmMarketingPage(path)"));
if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  assert(app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingPage(path);"));
  assert(!app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();"));
  assert(app.includes('Nenhuma métrica é simulada'));
}
console.log('Marketing module: PASS');
