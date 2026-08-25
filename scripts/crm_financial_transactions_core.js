(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.ValtrenFinanceCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const STATUSES=['pending','posted','excluded'];
  const DIRECTIONS=['inflow','outflow'];
  const NATURES=['revenue','expense','transfer','refund','reimbursement','reversal','chargeback','other'];
  const RECONCILIATION_STATUSES=['unreconciled','matched','reconciled'];
  const ACCOUNT_TYPES=['bank','checking','digital','card','gateway','acquirer','wallet','other'];
  const SOURCES=['manual','import','integration'];
  const DEFAULT_CATEGORIES=[
    ['revenue_services','Receita de Serviços','','revenue'],
    ['revenue_product','Receita de Produto','','revenue'],
    ['marketing','Marketing','','expense'],
    ['marketing_paid','Tráfego Pago','marketing','expense'],
    ['software','Software','','expense'],
    ['infrastructure','Infraestrutura','','expense'],
    ['infrastructure_cloud','Cloud','infrastructure','expense'],
    ['taxes','Impostos','','expense'],
    ['fees_professional','Honorários','','expense'],
    ['payroll','Folha','','expense'],
    ['commission','Comissão','','expense'],
    ['refund','Reembolso','','other'],
    ['bank_fees','Tarifas Bancárias','','expense'],
    ['internal_transfer','Transferência entre Contas','','transfer']
  ];

  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const num=(value)=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0;};
  const absoluteAmount=(value)=>Math.round(Math.abs(num(value))*100)/100;
  const moneyEqual=(a,b)=>Math.abs(num(a)-num(b))<0.005;
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}
  function defaultCategories(now){return DEFAULT_CATEGORIES.map(([id,name,parentId,nature])=>({id,name,parentId,nature,status:'active',system:true,createdAt:now(),updatedAt:now()}));}
  function createState(options={}){const now=options.now||(()=>new Date().toISOString());return {schemaVersion:SCHEMA_VERSION,accounts:[],transactions:[],categories:defaultCategories(now),rules:[],matches:[],history:[],imports:[],metadata:{legacyMigrated:false}};}
  function ensureState(input,options={}){const data=input&&typeof input==='object'?input:createState(options);const template=createState(options);for(const [key,value] of Object.entries(template)){if(Array.isArray(value)&&!Array.isArray(data[key]))data[key]=[];}if(!data.metadata||typeof data.metadata!=='object')data.metadata={};if(!data.categories.length)data.categories=template.categories;data.schemaVersion=SCHEMA_VERSION;return data;}

  function normalizeStatus(value){const key=fold(value).replace(/[^a-z0-9]+/g,'_');if(key==='pendente'||key==='pending')return 'pending';if(['lancada','posted','pago','paga'].includes(key))return 'posted';if(key==='excluida'||key==='excluded')return 'excluded';return key;}
  function normalizeDirection(value){const key=fold(value);if(['entrada','inflow','credit','credito','receita'].includes(key))return 'inflow';if(['saida','outflow','debit','debito','despesa'].includes(key))return 'outflow';return key;}
  function normalizeNature(value,direction=''){
    const key=fold(value).replace(/[^a-z0-9]+/g,'_');
    if(key==='receita'||key==='revenue')return 'revenue';
    if(key==='despesa'||key==='expense')return 'expense';
    if(key==='transferencia'||key==='transfer')return 'transfer';
    if(key==='reembolso'||key==='reimbursement')return 'reimbursement';
    if(key==='estorno'||key==='reversal')return 'reversal';
    if(key==='refund'||key==='devolucao')return 'refund';
    if(key==='chargeback')return 'chargeback';
    if(key==='outro'||key==='other')return 'other';
    return direction==='inflow'?'revenue':direction==='outflow'?'expense':'other';
  }
  function effectiveAmount(tx){return tx.direction==='inflow'?tx.amount:-tx.amount;}
  function contributesToResult(tx){return tx.status==='posted'&&!tx.isDemo&&['revenue','expense'].includes(tx.financialNature);}
  function stableImportKey(input){if(input.externalId)return `${input.financialAccountId||''}|${text(input.externalId)}`;return [input.financialAccountId||'',input.transactionDate||'',normalizeDirection(input.direction),absoluteAmount(input.amount).toFixed(2),fold(input.originalDescription||input.description)].join('|');}

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const party=options.partyService||null;
    const data=ensureState(store,{now});
    const getAccount=(id)=>data.accounts.find((row)=>row.id===id)||null;
    const getTransaction=(id)=>data.transactions.find((row)=>row.id===id)||null;
    const getCategory=(id)=>data.categories.find((row)=>row.id===id)||null;
    const history=(action,transactionId,before,after,metadata={})=>{const event={id:idFactory('finhist'),action,transactionId:transactionId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(event);return event;};
    const touch=(row)=>{row.updatedAt=now();row.updatedBy=actor()||null;return row;};
    const assertAccount=(id)=>{const account=getAccount(id);if(!account)throw new Error('Conta financeira não encontrada');return account;};
    function assertParty(type,id){if(!id)return true;if(type==='financial_account'){assertAccount(id);return true;}if(!['person','organization'].includes(type))throw new Error('Tipo de contraparte inválido');if(!party||!party.getEntity(type,id))throw new Error('Pessoa/Organização canônica não encontrada');return true;}

    function createAccount(input={}){
      const name=text(input.name);if(!name)throw new Error('Conta requer nome');
      const row={id:input.id||idFactory('facc'),name,institution:text(input.institution),type:ACCOUNT_TYPES.includes(input.type)?input.type:'other',currency:text(input.currency||'BRL')||'BRL',currentBalance:input.currentBalance==null||input.currentBalance===''?null:num(input.currentBalance),bookedBalance:input.bookedBalance==null||input.bookedBalance===''?null:num(input.bookedBalance),status:text(input.status||'active')||'active',source:SOURCES.includes(input.source)?input.source:'manual',integrationId:text(input.integrationId),integrationValidated:!!input.integrationValidated,lastUpdatedAt:input.lastUpdatedAt||null,isDemo:!!input.isDemo,metadata:clone(input.metadata||{}),createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null};
      if(row.integrationValidated&&!row.integrationId)throw new Error('Integração validada requer integrationId');
      data.accounts.push(row);return row;
    }
    function updateAccount(id,input={}){const row=assertAccount(id),before=clone(row);for(const key of ['name','institution','currency','status','integrationId'])if(key in input)row[key]=text(input[key]);if('type'in input&&ACCOUNT_TYPES.includes(input.type))row.type=input.type;if('currentBalance'in input)row.currentBalance=input.currentBalance==null||input.currentBalance===''?null:num(input.currentBalance);if('bookedBalance'in input)row.bookedBalance=input.bookedBalance==null||input.bookedBalance===''?null:num(input.bookedBalance);if('integrationValidated'in input)row.integrationValidated=!!input.integrationValidated;if(row.integrationValidated&&!row.integrationId)throw new Error('Integração validada requer integrationId');touch(row);history('account.updated','',before,row,{accountId:id});return row;}

    function normalizeTransactionInput(input={},existing=null){
      const direction=normalizeDirection(input.direction||existing?.direction);if(!DIRECTIONS.includes(direction))throw new Error('Direção financeira inválida');
      const amount=absoluteAmount(input.amount??existing?.amount);if(!(amount>0))throw new Error('Valor da transação deve ser maior que zero');
      const financialAccountId=input.financialAccountId||existing?.financialAccountId;assertAccount(financialAccountId);
      const financialNature=normalizeNature(input.financialNature||existing?.financialNature,direction);if(!NATURES.includes(financialNature))throw new Error('Natureza financeira inválida');
      const status=normalizeStatus(input.status||existing?.status||'pending');if(!STATUSES.includes(status))throw new Error('Status operacional inválido');
      const counterpartyType=input.counterpartyType??existing?.counterpartyType??'';
      const counterpartyId=input.counterpartyId??existing?.counterpartyId??'';
      if(counterpartyId)assertParty(counterpartyType,counterpartyId);
      const categoryId=input.categoryId??existing?.categoryId??'';if(categoryId&&!getCategory(categoryId))throw new Error('Categoria financeira não encontrada');
      const businessDimension=input.businessDimension??existing?.businessDimension??'unassigned';if(!['unassigned','corporate','product'].includes(businessDimension))throw new Error('Dimensão de negócio inválida');
      const productId=('productId'in input)?text(input.productId):text(existing?.productId);if(businessDimension==='product'&&!productId)throw new Error('Produto/Sistema requer referência estável');
      const source=input.source||existing?.source||'manual';if(!SOURCES.includes(source))throw new Error('Origem da transação inválida');
      const reconciliationStatus=input.reconciliationStatus||existing?.reconciliationStatus||'unreconciled';if(!RECONCILIATION_STATUSES.includes(reconciliationStatus))throw new Error('Status de conciliação inválido');
      return {financialAccountId,externalId:text(input.externalId??existing?.externalId),transactionDate:input.transactionDate||existing?.transactionDate||now().slice(0,10),settlementDate:input.settlementDate??existing?.settlementDate??'',importedAt:input.importedAt??existing?.importedAt??null,postedAt:input.postedAt??existing?.postedAt??null,originalDescription:text(input.originalDescription??input.description??existing?.originalDescription),normalizedDescription:text(input.normalizedDescription??existing?.normalizedDescription),amount,currency:text(input.currency||existing?.currency||getAccount(financialAccountId).currency||'BRL'),direction,financialNature,counterpartyType,counterpartyId,categoryId,subcategoryId:text(input.subcategoryId??existing?.subcategoryId),businessDimension,productId:businessDimension==='product'?productId:'',unitReferenceId:text(input.unitReferenceId??existing?.unitReferenceId),allocations:clone(input.allocations??existing?.allocations??[]),source,sourceReference:text(input.sourceReference??existing?.sourceReference),status,reconciliationStatus,attachments:clone(input.attachments??existing?.attachments??[]),notes:text(input.notes??existing?.notes),relatedTransactionId:text(input.relatedTransactionId??existing?.relatedTransactionId),classificationSource:input.classificationSource||existing?.classificationSource||'manual',isDemo:!!(input.isDemo??existing?.isDemo),metadata:{...(existing?.metadata||{}),...(input.metadata||{})}};
    }
    function createTransaction(input={}){const payload=normalizeTransactionInput(input);if(payload.relatedTransactionId&&!getTransaction(payload.relatedTransactionId))throw new Error('Transação relacionada não encontrada');const row={id:input.id||idFactory('ftx'),...payload,excludedAt:null,excludedReason:'',reconciledAt:null,reconciledBy:null,createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null};data.transactions.push(row);history('transaction.created',row.id,null,row,{source:row.source});applyRules(row.id);return row;}
    function updateTransaction(id,input={}){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');const before=clone(row),payload=normalizeTransactionInput(input,row);Object.assign(row,payload);touch(row);history('transaction.updated',id,before,row);return row;}
    function setClassification(id,input={},source='manual'){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');const before=clone(row),payload=normalizeTransactionInput({...input,classificationSource:source},row);Object.assign(row,payload,{classificationSource:source});touch(row);history('transaction.classification.changed',id,before,row,{source});return row;}
    function post(id){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');if(row.status==='excluded')throw new Error('Restaure a transação antes de lançar');if(row.status==='posted')return row;const before=clone(row);row.status='posted';row.postedAt=now();touch(row);history('transaction.posted',id,before,row);return row;}
    function exclude(id,reason=''){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');if(row.status==='excluded')return row;const before=clone(row);row.status='excluded';row.excludedAt=now();row.excludedReason=text(reason);touch(row);history('transaction.excluded',id,before,row,{reason:row.excludedReason});return row;}
    function restore(id){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');if(row.status!=='excluded')return row;const before=clone(row);row.status='pending';row.excludedAt=null;row.excludedReason='';touch(row);history('transaction.restored',id,before,row);return row;}

    function validateAllocations(transactionId,allocations){
      const tx=getTransaction(transactionId);if(!tx)throw new Error('Transação não encontrada');if(!Array.isArray(allocations)||!allocations.length)return [];
      const normalized=allocations.map((item)=>({dimension:item.dimension==='corporate'?'corporate':'product',productId:item.dimension==='corporate'?'':text(item.productId),percentage:item.percentage==null||item.percentage===''?null:num(item.percentage),amount:item.amount==null||item.amount===''?null:absoluteAmount(item.amount)}));
      if(normalized.some((item)=>item.dimension==='product'&&!item.productId))throw new Error('Rateio por produto requer productId');
      const hasPercent=normalized.every((item)=>item.percentage!=null),hasAmount=normalized.every((item)=>item.amount!=null);
      if(hasPercent===hasAmount)throw new Error('Use percentual em todas as linhas ou valor em todas as linhas');
      if(hasPercent&&!moneyEqual(normalized.reduce((sum,item)=>sum+item.percentage,0),100))throw new Error('Rateio percentual deve totalizar 100%');
      if(hasAmount&&!moneyEqual(normalized.reduce((sum,item)=>sum+item.amount,0),tx.amount))throw new Error('Rateio por valor deve totalizar o valor integral da transação');
      return normalized;
    }
    function setAllocations(id,allocations){const row=getTransaction(id);if(!row)throw new Error('Transação não encontrada');const before=clone(row);row.allocations=validateAllocations(id,allocations);touch(row);history('transaction.allocations.changed',id,before,row);return row;}

    function createRule(input={}){const rule={id:input.id||idFactory('frule'),name:text(input.name||'Regra'),active:input.active!==false,criteria:{descriptionContains:text(input.criteria?.descriptionContains),counterpartyId:text(input.criteria?.counterpartyId),direction:normalizeDirection(input.criteria?.direction),accountId:text(input.criteria?.accountId),minAmount:input.criteria?.minAmount==null?null:absoluteAmount(input.criteria.minAmount),maxAmount:input.criteria?.maxAmount==null?null:absoluteAmount(input.criteria.maxAmount)},classification:{categoryId:text(input.classification?.categoryId),businessDimension:input.classification?.businessDimension||'',productId:text(input.classification?.productId),financialNature:input.classification?.financialNature||''},createdAt:now(),updatedAt:now()};data.rules.push(rule);return rule;}
    function ruleMatches(rule,tx){if(!rule.active)return false;const criteria=rule.criteria||{};if(criteria.descriptionContains&&!fold(tx.originalDescription).includes(fold(criteria.descriptionContains)))return false;if(criteria.counterpartyId&&tx.counterpartyId!==criteria.counterpartyId)return false;if(criteria.direction&&DIRECTIONS.includes(criteria.direction)&&tx.direction!==criteria.direction)return false;if(criteria.accountId&&tx.financialAccountId!==criteria.accountId)return false;if(criteria.minAmount!=null&&tx.amount<criteria.minAmount)return false;if(criteria.maxAmount!=null&&tx.amount>criteria.maxAmount)return false;return true;}
    function applyRules(id){const tx=getTransaction(id);if(!tx)throw new Error('Transação não encontrada');const rule=data.rules.find((candidate)=>ruleMatches(candidate,tx));if(!rule)return null;const change={};for(const key of ['categoryId','businessDimension','productId','financialNature'])if(rule.classification?.[key])change[key]=rule.classification[key];if(Object.keys(change).length){setClassification(id,change,'rule');tx.metadata={...(tx.metadata||{}),classificationRuleId:rule.id};}return rule;}

    function addMatch(id,input={}){const tx=getTransaction(id);if(!tx)throw new Error('Transação não encontrada');const targetType=text(input.targetType),targetId=text(input.targetId);if(!targetType||!targetId)throw new Error('Correspondência requer tipo e referência');let match=data.matches.find((row)=>row.transactionId===id&&row.targetType===targetType&&row.targetId===targetId&&row.status==='active');if(match)return match;match={id:idFactory('fmatch'),transactionId:id,targetType,targetId,amount:input.amount==null?tx.amount:absoluteAmount(input.amount),status:'active',createdAt:now(),createdBy:actor()||null};data.matches.push(match);const before=clone(tx);tx.reconciliationStatus='matched';touch(tx);history('transaction.match.added',id,before,tx,{matchId:match.id,targetType,targetId});return match;}
    function removeMatch(matchId){const match=data.matches.find((row)=>row.id===matchId&&row.status==='active');if(!match)return false;match.status='inactive';const tx=getTransaction(match.transactionId);if(tx){const before=clone(tx),remaining=data.matches.some((row)=>row.transactionId===tx.id&&row.status==='active');if(!remaining&&tx.reconciliationStatus==='matched')tx.reconciliationStatus='unreconciled';touch(tx);history('transaction.match.removed',tx.id,before,tx,{matchId});}return true;}
    function reconcile(id){const tx=getTransaction(id);if(!tx)throw new Error('Transação não encontrada');if(tx.status!=='posted')throw new Error('Apenas transações lançadas podem ser conciliadas');if(tx.reconciliationStatus==='reconciled')return tx;const before=clone(tx);tx.reconciliationStatus='reconciled';tx.reconciledAt=now();tx.reconciledBy=actor()||null;touch(tx);history('transaction.reconciled',id,before,tx,{matches:data.matches.filter((row)=>row.transactionId===id&&row.status==='active').map((row)=>row.id)});return tx;}
    function unreconcile(id){const tx=getTransaction(id);if(!tx)throw new Error('Transação não encontrada');const before=clone(tx),hasMatch=data.matches.some((row)=>row.transactionId===id&&row.status==='active');tx.reconciliationStatus=hasMatch?'matched':'unreconciled';tx.reconciledAt=null;tx.reconciledBy=null;touch(tx);history('transaction.unreconciled',id,before,tx);return tx;}

    function createInternalTransfer(input={}){const from=assertAccount(input.fromAccountId),to=assertAccount(input.toAccountId);if(from.id===to.id)throw new Error('Transferência exige contas diferentes');const amount=absoluteAmount(input.amount);if(!(amount>0))throw new Error('Valor inválido');const common={amount,currency:input.currency||from.currency,financialNature:'transfer',categoryId:'internal_transfer',transactionDate:input.transactionDate||now().slice(0,10),originalDescription:text(input.originalDescription||'Transferência entre contas'),source:input.source||'manual',status:input.status||'pending'};const outflow=createTransaction({...common,financialAccountId:from.id,direction:'outflow'});const inflow=createTransaction({...common,financialAccountId:to.id,direction:'inflow'});outflow.relatedTransactionId=inflow.id;inflow.relatedTransactionId=outflow.id;history('transfer.linked',outflow.id,null,{relatedTransactionId:inflow.id});history('transfer.linked',inflow.id,null,{relatedTransactionId:outflow.id});return {outflow,inflow};}
    function createRelatedMovement(originalId,input={}){const original=getTransaction(originalId);if(!original)throw new Error('Transação original não encontrada');const nature=normalizeNature(input.financialNature||'reversal');if(!['refund','reimbursement','reversal','chargeback'].includes(nature))throw new Error('Natureza de reversão inválida');return createTransaction({...input,financialAccountId:input.financialAccountId||original.financialAccountId,amount:input.amount||original.amount,direction:input.direction||(original.direction==='inflow'?'outflow':'inflow'),financialNature:nature,relatedTransactionId:original.id,status:input.status||'pending'});}

    function importTransactions(records=[],options={}){const financialAccountId=options.financialAccountId;assertAccount(financialAccountId);const batch={id:idFactory('fimport'),source:options.source||'import',financialAccountId,createdAt:now(),createdBy:actor()||null,created:[],duplicates:[]};for(const record of records){const candidate={...record,financialAccountId,source:options.source||'import',importedAt:now(),status:'pending'};const key=stableImportKey(candidate),existing=data.transactions.find((row)=>stableImportKey(row)===key);if(existing){batch.duplicates.push(existing.id);continue;}const tx=createTransaction(candidate);tx.metadata={...(tx.metadata||{}),importKey:key,importBatchId:batch.id};batch.created.push(tx.id);}data.imports.push(batch);return batch;}
    function migrateLegacy(rows=[]){if(data.metadata.legacyMigrated)return 0;let count=0;for(const legacy of rows||[]){if(!legacy||!legacy.id||data.transactions.some((row)=>row.metadata?.legacyId===String(legacy.id)))continue;let account=data.accounts.find((row)=>row.metadata?.legacyAccount===true);if(!account)account=createAccount({name:'Conta legada',type:'other',source:'manual',metadata:{legacyAccount:true},status:'inactive'});const raw=Number(legacy.value||0);let direction=normalizeDirection(legacy.type);if(!DIRECTIONS.includes(direction))direction=raw<0?'outflow':'inflow';createTransaction({financialAccountId:account.id,amount:Math.abs(raw)||0.01,direction,financialNature:normalizeNature(legacy.type,direction),originalDescription:legacy.description||'Movimentação legada',transactionDate:legacy.date||now().slice(0,10),status:normalizeStatus(legacy.status||'pending'),source:'manual',metadata:{legacyId:String(legacy.id),legacySnapshot:clone(legacy)},isDemo:!!legacy.isDemo});count++;}data.metadata.legacyMigrated=true;data.metadata.legacyMigratedAt=now();return count;}

    function query(filters={}){let rows=data.transactions.slice();if(!filters.includeDemo)rows=rows.filter((row)=>!row.isDemo);if(filters.status)rows=rows.filter((row)=>row.status===filters.status);if(filters.accountId&&filters.accountId!=='all')rows=rows.filter((row)=>row.financialAccountId===filters.accountId);if(filters.direction)rows=rows.filter((row)=>row.direction===filters.direction);if(filters.nature)rows=rows.filter((row)=>row.financialNature===filters.nature);if(filters.categoryId)rows=rows.filter((row)=>row.categoryId===filters.categoryId);if(filters.businessDimension==='corporate')rows=rows.filter((row)=>row.businessDimension==='corporate'||(row.allocations||[]).some((item)=>item.dimension==='corporate'));if(filters.productId)rows=rows.filter((row)=>row.productId===filters.productId||(row.allocations||[]).some((item)=>item.productId===filters.productId));if(filters.reconciliationStatus)rows=rows.filter((row)=>row.reconciliationStatus===filters.reconciliationStatus);if(filters.from)rows=rows.filter((row)=>row.transactionDate>=filters.from);if(filters.to)rows=rows.filter((row)=>row.transactionDate<=filters.to);if(filters.search){const needle=fold(filters.search);rows=rows.filter((row)=>fold([row.originalDescription,row.normalizedDescription,row.notes,row.externalId,row.categoryId,row.counterpartyId,row.productId,row.amount].join(' ')).includes(needle));}rows.sort((a,b)=>String(b.transactionDate).localeCompare(String(a.transactionDate))||String(b.createdAt).localeCompare(String(a.createdAt)));const total=rows.length,offset=Math.max(0,Number(filters.offset)||0);if(filters.limit===0)return {total,rows};const limit=Math.max(1,Number(filters.limit)||50);return {total,rows:rows.slice(offset,offset+limit)};}
    function totals(filter={}){const rows=query({...filter,status:filter.status||'posted',includeDemo:false,limit:0}).rows;let revenue=0,expense=0;for(const tx of rows){if(!contributesToResult(tx))continue;if(tx.financialNature==='revenue')revenue+=tx.amount;if(tx.financialNature==='expense')expense+=tx.amount;}return {revenue,expense,result:revenue-expense};}
    function accountSummary(id){const account=getAccount(id),rows=data.transactions.filter((row)=>row.financialAccountId===id&&row.status!=='excluded'&&!row.isDemo);return {account,pending:rows.filter((row)=>row.status==='pending').length,currentBalance:account?.currentBalance??null,bookedBalance:account?.bookedBalance??null};}
    function allAccountsSummary(){const accounts=data.accounts.filter((row)=>row.status!=='inactive'&&!row.isDemo),knownCurrent=accounts.filter((row)=>row.currentBalance!=null),knownBooked=accounts.filter((row)=>row.bookedBalance!=null);return {account:null,pending:data.transactions.filter((row)=>row.status==='pending'&&!row.isDemo).length,currentBalance:accounts.length&&knownCurrent.length===accounts.length?knownCurrent.reduce((sum,row)=>sum+row.currentBalance,0):null,bookedBalance:accounts.length&&knownBooked.length===accounts.length?knownBooked.reduce((sum,row)=>sum+row.bookedBalance,0):null};}
    function bulk(ids=[],action,payload={}){const changed=[];for(const id of [...new Set(ids)].filter((candidate)=>getTransaction(candidate))){if(action==='post')changed.push(post(id));else if(action==='exclude')changed.push(exclude(id,payload.reason));else if(action==='restore')changed.push(restore(id));else if(action==='classify')changed.push(setClassification(id,payload,'manual'));else if(action==='counterparty')changed.push(setClassification(id,{counterpartyType:payload.counterpartyType,counterpartyId:payload.counterpartyId},'manual'));}return changed;}

    return {data,getAccount,getTransaction,getCategory,createAccount,updateAccount,createTransaction,updateTransaction,setClassification,post,exclude,restore,validateAllocations,setAllocations,createRule,applyRules,addMatch,removeMatch,reconcile,unreconcile,createInternalTransfer,createRelatedMovement,importTransactions,migrateLegacy,query,totals,accountSummary,allAccountsSummary,bulk,history,stableImportKey,effectiveAmount,contributesToResult};
  }

  return {SCHEMA_VERSION,STATUSES,DIRECTIONS,NATURES,RECONCILIATION_STATUSES,ACCOUNT_TYPES,SOURCES,DEFAULT_CATEGORIES,createState,ensureState,createService,normalizeStatus,normalizeDirection,normalizeNature,stableImportKey,effectiveAmount,contributesToResult,fold,text,absoluteAmount,moneyEqual};
});
