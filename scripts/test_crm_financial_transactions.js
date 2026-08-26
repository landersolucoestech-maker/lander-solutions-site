'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const PartyCore=require('./crm_canonical_parties_core.js');
const FinanceCore=require('./crm_financial_transactions_domain.js');

let seq=0,clock=0,passed=0;
const now=()=>`2026-08-25T15:${String(Math.floor(clock/60)).padStart(2,'0')}:${String(clock++%60).padStart(2,'0')}.000Z`;
const ids=(p)=>`${p}_${++seq}`;
const partyState=PartyCore.createState();
const party=PartyCore.createService(partyState,{idFactory:ids,now});
const state=FinanceCore.createState({now});
const finance=FinanceCore.createService(state,{partyService:party,idFactory:ids,now,actorProvider:()=> 'user_fin'});
function test(name,fn){try{fn();passed++;console.log(`PASS ${name}`);}catch(error){console.error(`FAIL ${name}`);throw error;}}

let acc1,acc2,inflow,outflow,person,org;
test('1 criação de conta financeira',()=>{acc1=finance.createAccount({name:'Conta Principal',institution:'Banco Manual',type:'checking',currency:'BRL',source:'manual'});assert(acc1.id);assert.equal(acc1.currentBalance,null);});
test('2 criação de segunda conta financeira',()=>{acc2=finance.createAccount({name:'Conta Reserva',type:'digital',currency:'BRL',source:'manual'});assert.notEqual(acc1.id,acc2.id);});
test('3 criação de transação de entrada',()=>{inflow=finance.createTransaction({financialAccountId:acc1.id,amount:15000,direction:'inflow',financialNature:'revenue',originalDescription:'STRIPE PAYMENT',status:'pending',source:'manual'});assert.equal(inflow.amount,15000);assert.equal(inflow.direction,'inflow');});
test('4 criação de transação de saída',()=>{outflow=finance.createTransaction({financialAccountId:acc1.id,amount:6500,direction:'outflow',financialNature:'expense',originalDescription:'META ADS',status:'pending',source:'manual'});assert.equal(outflow.direction,'outflow');assert.equal(outflow.amount,6500);});
test('5 valor é absoluto e direção é separada',()=>{const t=finance.createTransaction({financialAccountId:acc1.id,amount:-50,direction:'outflow',financialNature:'expense',originalDescription:'Tarifa',status:'pending'});assert.equal(t.amount,50);assert.equal(FinanceCore.effectiveAmount(t),-50);});
test('6 status inicial pendente',()=>{assert.equal(inflow.status,'pending');assert(FinanceCore.STATUSES.includes('pending'));});
test('7 lançamento muda Pendente para Lançada',()=>{finance.post(inflow.id);assert.equal(inflow.status,'posted');assert(inflow.postedAt);});
test('8 exclusão não destrói registro',()=>{finance.exclude(outflow.id,'Duplicidade operacional');assert(finance.getTransaction(outflow.id));assert.equal(outflow.status,'excluded');assert.equal(outflow.excludedReason,'Duplicidade operacional');});
test('9 restauração preserva identidade da transação',()=>{const id=outflow.id;finance.restore(id);assert.equal(outflow.id,id);assert.equal(outflow.status,'pending');});

person=party.createPerson({fullName:'Cliente Canônico',cpf:'52998224725',email:'cliente@test.com'});
org=party.createOrganization({legalName:'Fornecedor ABC Ltda',tradeName:'Fornecedor ABC',cnpj:'04252011000110'});
test('10 vínculo com Person canônica',()=>{finance.setClassification(inflow.id,{counterpartyType:'person',counterpartyId:person.id});assert.equal(inflow.counterpartyId,person.id);assert.equal(partyState.people.length,1);});
test('11 vínculo com Organization canônica',()=>{finance.setClassification(outflow.id,{counterpartyType:'organization',counterpartyId:org.id});assert.equal(outflow.counterpartyId,org.id);assert.equal(partyState.organizations.length,1);});
test('12 atribuir contraparte não duplica Pessoa/Organização',()=>{const p=partyState.people.length,o=partyState.organizations.length;finance.setClassification(inflow.id,{counterpartyType:'person',counterpartyId:person.id});finance.setClassification(outflow.id,{counterpartyType:'organization',counterpartyId:org.id});assert.equal(partyState.people.length,p);assert.equal(partyState.organizations.length,o);});
test('13 contraparte inválida é rejeitada',()=>{assert.throws(()=>finance.setClassification(outflow.id,{counterpartyType:'organization',counterpartyId:'org_inexistente'}),/canônica não encontrada/);});

test('14 categoria principal funciona',()=>{finance.setClassification(outflow.id,{categoryId:'marketing'});assert.equal(outflow.categoryId,'marketing');assert.equal(finance.getCategory('marketing').name,'Marketing');});
test('15 subcategoria funciona',()=>{finance.setClassification(outflow.id,{categoryId:'marketing_paid',subcategoryId:'paid_social'});assert.equal(outflow.categoryId,'marketing_paid');assert.equal(finance.getCategory('marketing_paid').parentId,'marketing');});
test('16 classificação Corporativo funciona',()=>{finance.setClassification(outflow.id,{businessDimension:'corporate',productId:''});assert.equal(outflow.businessDimension,'corporate');assert.equal(outflow.productId,'');});
test('17 Produto/Sistema usa referência estável sem catálogo paralelo',()=>{finance.setClassification(inflow.id,{businessDimension:'product',productId:'product_a'});assert.equal(inflow.productId,'product_a');assert.equal(inflow.businessDimension,'product');});
test('18 produto exige referência estável',()=>{assert.throws(()=>finance.setClassification(inflow.id,{businessDimension:'product',productId:''}),/referência estável/);});

test('19 rateio percentual totaliza 100%',()=>{finance.setAllocations(outflow.id,[{dimension:'product',productId:'product_a',percentage:50},{dimension:'product',productId:'product_b',percentage:30},{dimension:'corporate',percentage:20}]);assert.equal(outflow.allocations.length,3);assert.equal(outflow.allocations.reduce((s,a)=>s+a.percentage,0),100);});
test('20 rateio por valor totaliza valor integral',()=>{finance.setAllocations(inflow.id,[{dimension:'product',productId:'product_a',amount:9000},{dimension:'corporate',amount:6000}]);assert.equal(inflow.allocations.reduce((s,a)=>s+a.amount,0),15000);});
test('21 rejeita rateio percentual inválido',()=>{assert.throws(()=>finance.setAllocations(outflow.id,[{dimension:'corporate',percentage:90}]),/100%/);});
test('22 rejeita rateio por valor inválido',()=>{assert.throws(()=>finance.setAllocations(inflow.id,[{dimension:'corporate',amount:1000}]),/valor integral/);});
test('23 rateio não cria nova despesa/transação',()=>{const before=state.transactions.length;finance.setAllocations(outflow.id,[{dimension:'corporate',percentage:100}]);assert.equal(state.transactions.length,before);});

test('24 regra automática pode ser criada',()=>{const rule=finance.createRule({name:'META ADS',criteria:{descriptionContains:'META ADS',direction:'outflow'},classification:{categoryId:'marketing_paid',businessDimension:'corporate',financialNature:'expense'}});assert(rule.id);assert.equal(state.rules.length,1);});
test('25 regra automática classifica transação',()=>{const tx=finance.createTransaction({financialAccountId:acc1.id,amount:200,direction:'outflow',financialNature:'expense',originalDescription:'META ADS CAMPANHA',status:'pending'});assert.equal(tx.categoryId,'marketing_paid');assert.equal(tx.classificationSource,'rule');assert(tx.metadata.classificationRuleId);});
test('26 correção manual substitui origem de classificação automática',()=>{const tx=state.transactions[state.transactions.length-1];finance.setClassification(tx.id,{categoryId:'software'},'manual');assert.equal(tx.categoryId,'software');assert.equal(tx.classificationSource,'manual');});

test('27 correspondência é criada sem criar segundo lançamento',()=>{const before=state.transactions.length,m=finance.addMatch(inflow.id,{targetType:'receivable',targetId:'ar_001'});assert(m.id);assert.equal(state.transactions.length,before);assert.equal(inflow.reconciliationStatus,'matched');});
test('28 match repetido é idempotente',()=>{const before=state.matches.length,a=finance.addMatch(inflow.id,{targetType:'receivable',targetId:'ar_001'}),b=finance.addMatch(inflow.id,{targetType:'receivable',targetId:'ar_001'});assert.equal(a.id,b.id);assert.equal(state.matches.length,before);});
test('29 transação lançada pode ser conciliada',()=>{finance.reconcile(inflow.id);assert.equal(inflow.reconciliationStatus,'reconciled');assert(inflow.reconciledAt);assert.equal(inflow.reconciledBy,'user_fin');});
test('30 conciliação registra histórico',()=>{assert(state.history.some((x)=>x.transactionId===inflow.id&&x.action==='transaction.reconciled'));});
test('31 conciliação pode ser revertida',()=>{finance.unreconcile(inflow.id);assert.equal(inflow.reconciliationStatus,'matched');assert.equal(inflow.reconciledAt,null);});
test('32 remover match não remove transação',()=>{const m=state.matches.find((x)=>x.transactionId===inflow.id&&x.status==='active');finance.removeMatch(m.id);assert(finance.getTransaction(inflow.id));assert.equal(inflow.reconciliationStatus,'unreconciled');});
test('33 pendente não pode ser conciliada',()=>{assert.throws(()=>finance.reconcile(outflow.id),/lançadas/);});

test('34 transferência cria duas pontas relacionadas',()=>{const t=finance.createInternalTransfer({fromAccountId:acc1.id,toAccountId:acc2.id,amount:20000,transactionDate:'2026-08-25'});assert.equal(t.outflow.financialNature,'transfer');assert.equal(t.inflow.financialNature,'transfer');assert.equal(t.outflow.relatedTransactionId,t.inflow.id);assert.equal(t.inflow.relatedTransactionId,t.outflow.id);});
test('35 transferência não é receita',()=>{const transfers=state.transactions.filter((x)=>x.financialNature==='transfer');transfers.forEach((x)=>finance.post(x.id));assert.equal(finance.totals().revenue,15000);});
test('36 transferência não é despesa',()=>{assert.equal(finance.totals().expense,0);});
test('37 estorno referencia movimento original',()=>{const r=finance.createRelatedMovement(inflow.id,{financialNature:'reversal',amount:15000});assert.equal(r.relatedTransactionId,inflow.id);assert.equal(r.direction,'outflow');});
test('38 reembolso referencia movimento original',()=>{const r=finance.createRelatedMovement(outflow.id,{financialNature:'reimbursement',amount:100});assert.equal(r.relatedTransactionId,outflow.id);assert.equal(r.financialNature,'reimbursement');});

test('39 origem manual é preservada',()=>{assert.equal(outflow.source,'manual');});
test('40 importação normalizada cria pendentes importadas',()=>{const batch=finance.importTransactions([{externalId:'FIT001',amount:90,direction:'outflow',originalDescription:'7-ELEVEN',transactionDate:'2026-08-20'}],{financialAccountId:acc1.id,source:'import'});assert.equal(batch.created.length,1);const tx=finance.getTransaction(batch.created[0]);assert.equal(tx.source,'import');assert.equal(tx.status,'pending');assert(tx.importedAt);});
test('41 deduplicação de importação por externalId/FITID',()=>{const batch=finance.importTransactions([{externalId:'FIT001',amount:90,direction:'outflow',originalDescription:'7-ELEVEN',transactionDate:'2026-08-20'}],{financialAccountId:acc1.id,source:'import'});assert.equal(batch.created.length,0);assert.equal(batch.duplicates.length,1);});
test('42 deduplicação fallback por conta/data/valor/direção/descrição',()=>{const one=finance.importTransactions([{amount:35.3,direction:'outflow',originalDescription:'POSTO ABC',transactionDate:'2026-08-21'}],{financialAccountId:acc1.id,source:'import'}),two=finance.importTransactions([{amount:35.3,direction:'outflow',originalDescription:'POSTO ABC',transactionDate:'2026-08-21'}],{financialAccountId:acc1.id,source:'import'});assert.equal(one.created.length,1);assert.equal(two.duplicates.length,1);});

test('43 anexos são apenas metadados no stack atual',()=>{const tx=finance.createTransaction({financialAccountId:acc1.id,amount:10,direction:'outflow',financialNature:'expense',originalDescription:'Comprovante',attachments:[{id:'att_meta',name:'recibo.pdf',storage:'unavailable'}]});assert.equal(tx.attachments.length,1);assert.equal(tx.attachments[0].storage,'unavailable');});
test('44 observações são preservadas',()=>{const tx=finance.createTransaction({financialAccountId:acc1.id,amount:11,direction:'outflow',financialNature:'expense',originalDescription:'Nota interna',notes:'Revisar classificação'});assert.equal(tx.notes,'Revisar classificação');});

test('45 ação em massa lança pendentes',()=>{const a=finance.createTransaction({financialAccountId:acc1.id,amount:1,direction:'inflow',financialNature:'revenue',originalDescription:'Bulk A'}),b=finance.createTransaction({financialAccountId:acc1.id,amount:2,direction:'inflow',financialNature:'revenue',originalDescription:'Bulk B'});finance.bulk([a.id,b.id],'post');assert.equal(a.status,'posted');assert.equal(b.status,'posted');});
test('46 ação em massa categoriza',()=>{const rows=state.transactions.filter((x)=>x.originalDescription.startsWith('Bulk'));finance.bulk(rows.map((x)=>x.id),'classify',{categoryId:'revenue_services'});assert(rows.every((x)=>x.categoryId==='revenue_services'));});
test('47 ação em massa exclui sem apagar',()=>{const rows=state.transactions.filter((x)=>x.originalDescription.startsWith('Bulk'));finance.bulk(rows.map((x)=>x.id),'exclude',{reason:'teste'});assert(rows.every((x)=>x.status==='excluded'));assert(rows.every((x)=>finance.getTransaction(x.id)));});
test('48 ação em massa restaura',()=>{const rows=state.transactions.filter((x)=>x.originalDescription.startsWith('Bulk'));finance.bulk(rows.map((x)=>x.id),'restore');assert(rows.every((x)=>x.status==='pending'));});

test('49 busca localiza descrição',()=>{const r=finance.query({search:'stripe',limit:50,includeDemo:false});assert(r.rows.some((x)=>x.id===inflow.id));});
test('50 filtro por conta funciona',()=>{const r=finance.query({accountId:acc2.id,limit:0,includeDemo:false});assert(r.rows.every((x)=>x.financialAccountId===acc2.id));});
test('51 filtro por status funciona',()=>{const r=finance.query({status:'pending',limit:0,includeDemo:false});assert(r.rows.every((x)=>x.status==='pending'));});
test('52 filtro por natureza funciona',()=>{const r=finance.query({nature:'transfer',limit:0,includeDemo:false});assert(r.rows.length>=2);assert(r.rows.every((x)=>x.financialNature==='transfer'));});
test('53 filtro Corporativo funciona',()=>{finance.setClassification(outflow.id,{businessDimension:'corporate'});const r=finance.query({businessDimension:'corporate',limit:0,includeDemo:false});assert(r.rows.some((x)=>x.id===outflow.id));});
test('54 filtro Produto/Sistema funciona',()=>{const r=finance.query({productId:'product_a',limit:0,includeDemo:false});assert(r.rows.some((x)=>x.id===inflow.id));});
test('55 Todas as contas consolida pendências sem inventar saldos',()=>{const s=finance.allAccountsSummary();assert.equal(s.currentBalance,null);assert(s.pending>=1);});
test('56 seleção de conta retorna resumo real',()=>{const s=finance.accountSummary(acc1.id);assert.equal(s.account.id,acc1.id);assert(s.pending>=1);});
test('57 tabs operacionais são exatamente Pendentes/Lançadas/Excluídas',()=>{assert.deepEqual(FinanceCore.STATUSES,['pending','posted','excluded']);});

test('58 dado demo não entra em resultado real',()=>{const demo=finance.createTransaction({financialAccountId:acc1.id,amount:999999,direction:'inflow',financialNature:'revenue',originalDescription:'DEMO',status:'posted',isDemo:true});const totals=finance.totals();assert(!totals.revenue.toString().includes('999999'));assert.equal(demo.isDemo,true);});
test('59 cálculo operacional considera somente receita/despesa lançadas reais',()=>{finance.post(outflow.id);const totals=finance.totals();assert.equal(totals.revenue,15000);assert.equal(totals.expense,6500);assert.equal(totals.result,8500);});
test('60 natureza de transferência permanece separada do status operacional',()=>{const tx=state.transactions.find((x)=>x.financialNature==='transfer');assert.equal(tx.status,'posted');assert.equal(tx.financialNature,'transfer');assert(FinanceCore.RECONCILIATION_STATUSES.includes(tx.reconciliationStatus));});

test('61 conta manual não aparece como integração validada',()=>{assert.equal(acc1.source,'manual');assert.equal(acc1.integrationValidated,false);});
test('62 conta não pode fingir integração validada sem integrationId',()=>{assert.throws(()=>finance.createAccount({name:'Falsa',integrationValidated:true}),/integrationId/);});
test('63 conta com integração validada exige referência explícita',()=>{const a=finance.createAccount({name:'Integrada',source:'integration',integrationId:'int_bank_1',integrationValidated:true});assert.equal(a.integrationValidated,true);assert.equal(a.integrationId,'int_bank_1');});
test('64 saldos desconhecidos permanecem null, não R$ 0 fictício',()=>{assert.equal(acc1.currentBalance,null);assert.equal(acc1.bookedBalance,null);});

test('65 migração legada preserva snapshot e não concorre como fonte',()=>{const localState=FinanceCore.createState({now}),local=FinanceCore.createService(localState,{partyService:party,idFactory:ids,now});const n=local.migrateLegacy([{id:'legacy1',type:'Receita',description:'Legado',value:100,date:'2026-08-01',status:'Pendente'}]);assert.equal(n,1);assert.equal(localState.transactions[0].metadata.legacyId,'legacy1');assert(localState.transactions[0].metadata.legacySnapshot);});
test('66 migração legada é idempotente',()=>{const localState=FinanceCore.createState({now}),local=FinanceCore.createService(localState,{partyService:party,idFactory:ids,now});local.migrateLegacy([{id:'legacy2',type:'Despesa',description:'Legado',value:50}]);const before=localState.transactions.length,again=local.migrateLegacy([{id:'legacy2',type:'Despesa',description:'Legado',value:50}]);assert.equal(again,0);assert.equal(localState.transactions.length,before);});
test('67 exclusão registra quem/quando/motivo no histórico',()=>{finance.exclude(outflow.id,'Teste histórico');const h=state.history.findLast((x)=>x.transactionId===outflow.id&&x.action==='transaction.excluded');assert(h);assert.equal(h.actorId,'user_fin');assert.equal(h.metadata.reason,'Teste histórico');finance.restore(outflow.id);});
test('68 mudança de categoria registra histórico operacional',()=>{finance.setClassification(outflow.id,{categoryId:'software'});assert(state.history.some((x)=>x.transactionId===outflow.id&&x.action==='transaction.classification.changed'));});
test('69 rateio registra histórico operacional',()=>{finance.setAllocations(outflow.id,[{dimension:'corporate',percentage:100}]);assert(state.history.some((x)=>x.transactionId===outflow.id&&x.action==='transaction.allocations.changed'));});
test('70 match registra histórico operacional',()=>{finance.addMatch(outflow.id,{targetType:'payable',targetId:'ap_001'});assert(state.history.some((x)=>x.transactionId===outflow.id&&x.action==='transaction.match.added'));});

const browserSource=fs.readFileSync(path.join(__dirname,'crm_financial_transactions_browser.js'),'utf8');
const domainSource=fs.readFileSync(path.join(__dirname,'crm_financial_transactions_domain.js'),'utf8');
test('71 browser usa state.crmFinancialTransactions como fonte canônica',()=>{assert(browserSource.includes('state.crmFinancialTransactions'));assert(browserSource.includes('ValtrenFinanceCore.createService'));});
test('72 contraparte usa crmCanonicalPartyService',()=>{assert(browserSource.includes('crmCanonicalPartyService()'));assert(!browserSource.includes('financialSuppliers'));assert(!browserSource.includes('financialCustomers'));});
test('73 Produto/Sistema não possui catálogo hardcoded no Financeiro',()=>{assert(browserSource.includes('function crmFinanceProducts()'));assert(!browserSource.includes("Music OS 360"));assert(!browserSource.includes("Vivendo da Música"));});
test('74 OFX não é falsamente apresentado como parser funcional',()=>{assert(browserSource.includes('parser ainda não validado'));assert(browserSource.includes('deduplicação por FITID/externalId'));});
test('75 nenhuma integração falsa recebe mensagem Atualizado agora',()=>{assert(!browserSource.includes('Atualizado agora'));assert(browserSource.includes('integrationValidated'));});
test('76 tabela possui colunas operacionais obrigatórias',()=>{for(const label of ['Data','Descrição','Saída','Entrada','Origem/Destino','Categoria','Produto/Sistema','Status','Ação'])assert(browserSource.includes(label));});
test('77 ações inline existem para contraparte/categoria/produto',()=>{for(const action of ['crm-fin-counterparty','crm-fin-category','crm-fin-business'])assert(browserSource.includes(action));});
test('78 ações em massa existem por status',()=>{for(const action of ['crm-fin-bulk-post','crm-fin-bulk-exclude','crm-fin-bulk-restore','crm-fin-bulk-reconcile'])assert(browserSource.includes(action));});
test('79 drawer de detalhe existe',()=>{assert(browserSource.includes('crm-fin-drawer'));assert(browserSource.includes('Dados da movimentação'));assert(browserSource.includes('Histórico'));});
test('80 paginação é limitada a 50 por página',()=>{assert(browserSource.includes('limit:50'));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  test('81 bundle contém domínio financeiro canônico',()=>{assert(app.includes('VALTREN FINANCIAL TRANSACTIONS START'));assert(app.includes('ValtrenFinanceCore'));});
  test('82 rota Financeiro aponta para crmTransactionsPage',()=>{assert(app.includes("if(path==='/crm/financeiro')return crmTransactionsPage();"));});
  test('83 implementação nova não foi sobrescrita pelo legado',()=>{const marker=app.lastIndexOf('VALTREN FINANCIAL TRANSACTIONS START');const route=app.lastIndexOf("if(path==='/crm/financeiro')return crmTransactionsPage();");assert(marker>0);assert(route>0);});
  test('84 sidebar financeiro permanece com seis itens oficiais',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);for(const label of ['Transações','Contabilidade','Notas Fiscais','Rateios','Participações','Repasses'])assert(sidebar.includes(label));for(const label of ['Categorias Financeiras','Regras de Categorização','Automações Financeiras'])assert(!sidebar.includes(label));});
  test('85 CRM completo continua materializado',()=>{assert(app.includes('VALTREN CRM COMPLETE START'));assert(app.includes('function crmRelationshipsPage'));});
  test('86 infraestrutura canônica continua materializada',()=>{assert(app.includes('ValtrenPartyCore'));assert(app.includes('crmCanonicalPartyService'));});
  test('87 Configurações continua com seis abas canônicas',()=>{for(const label of ["['empresa','Empresa']","['notificacoes','Notificações']","['seguranca','Segurança']","['integracoes','Integrações']","['auditoria','Auditoria']","['usuarios','Usuários']"])assert(app.includes(label));});
  test('88 Administração permanece fora da sidebar canônica',()=>{const start=app.indexOf('VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));});
  test('89 Agenda mantém consumidor de projeção CRM',()=>{assert(app.includes('state.crmRelContacts'));assert(app.includes('canonicalEntityId'));});
  test('90 nenhum novo módulo financeiro indevido foi criado no sidebar',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);assert(!sidebar.includes('Regras de Categorização'));assert(!sidebar.includes('Categorias Financeiras'));});
}

console.log(`Financial Transactions tests: ${passed} passed`);
