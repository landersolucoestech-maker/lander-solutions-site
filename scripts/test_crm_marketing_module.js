'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const browser=fs.readFileSync(path.resolve(__dirname,'..','web','src','modules','marketing','module.js'),'utf8');
const materializer=fs.readFileSync(path.resolve(__dirname,'crm_marketing_module.py'),'utf8');
const forbiddenIntegration='Sound'+'charts';
for(const token of ['Visão Geral','Campanhas','Calendário','Métricas','Briefings','Tarefas','Nenhuma métrica é simulada','crmMarketingSave','crmMarketingPage'])assert(browser.includes(token),`ausente: ${token}`);
for(const channel of ['Meta / Instagram / Facebook','Google Ads','TikTok Ads','YouTube','Spotify Ads'])assert(browser.includes(channel),`canal de Marketing ausente: ${channel}`);
assert(!browser.includes(forbiddenIntegration),'integração externa proibida não pertence ao módulo Marketing');
assert(browser.includes("localStorage.setItem(CRM_MARKETING_KEY"));
assert(!browser.includes('Math.random()*100'));
assert(materializer.includes("crmMarketingPage(path)"));
if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  assert(app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingPage(path);"));
  assert(!app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();"));
  assert(app.includes('Nenhuma métrica é simulada'));
  assert(!app.includes(forbiddenIntegration),'integração externa proibida sobreviveu no bundle materializado');
}
console.log('Marketing module: PASS');
