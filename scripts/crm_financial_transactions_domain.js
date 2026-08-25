// Compatibility alias. Canonical implementation lives in crm_financial_transactions_core.js.
(function(root){
  if(typeof module==='object'&&module.exports){module.exports=require('./crm_financial_transactions_core.js');return;}
  if(root&&root.ValtrenFinanceCore)return;
  throw new Error('ValtrenFinanceCore deve ser materializado a partir de crm_financial_transactions_core.js');
})(typeof globalThis!=='undefined'?globalThis:this);
