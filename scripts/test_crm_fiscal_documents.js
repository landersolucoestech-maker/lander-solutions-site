const assert=require('assert');
const fs=require('fs');
const path=require('path');
const Party=require('../web/src/modules/crm/parties/core.js');
const Finance=require('../web/src/modules/finance/transactions/core.js');
const Fiscal=require('../web/src/modules/finance/fiscal/core.js');

let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${passed} ${name}`);}catch(error){console.error(`FAIL ${name}: ${error.message}`);throw error;}}
let seq=0;
const idFactory=(prefix)=>`${prefix}_test_${++seq}`;
let tick=0;
const now=()=>`2026-08-25T12:${String(tick++%60).padStart(2,'0')}:00.000Z`;

const partyStore=Party.createState();
const party=Party.createService(partyStore,{idFactory,now,actorProvider:()=> 'user_test'});
const company=party.createOrganization({legalName:'Valtren Teste'});
const supplier=party.createOrganization({legalName:'Fornecedor Canônico'});
const customerOrg=party.createOrganization({legalName:'Cliente Organização'});
const customerPerson=party.createPerson({fullName:'Cliente Pessoa'});

const financeStore=Finance.createState({now});
const finance=Finance.createService(financeStore,{idFactory,now,partyService:party,actorProvider:()=> 'user_test'});
const account=finance.createAccount({name:'Conta Teste',type:'bank',currency:'BRL'});

const fiscalStore=Fiscal.createState();
const fiscal=Fiscal.createService(fiscalStore,{
  idFactory,now,partyService:party,financeService:finance,actorProvider:()=> 'user_test',
  companyProvider:()=>({partyType:'organization',partyId:company.id,legalName:'Valtren Teste',document:'CNPJ configurado',address:'Endereço configurado',currency:'BRL'}),
  defaultCurrencyProvider:()=> 'BRL',
  integrationValidator:()=>false
});

const item=(description='Serviço',unitPrice=1000)=>({description,quantity:1,unit:'un',unitPrice});
function outDoc(extra={}){
  return fiscal.createDocument({direction:'outgoing',documentType:'service',status:'issued',issueDate:'2026-08-25',counterpartyType:'organization',counterpartyId:customerOrg.id,currency:'BRL',number:`OUT-${seq+1}`,items:[item()],...extra});
}
function inDoc(extra={}){
  return fiscal.createDocument({direction:'incoming',documentType:'service',status:'received',issueDate:'2026-08-25',counterpartyType:'organization',counterpartyId:supplier.id,currency:'BRL',number:`IN-${seq+1}`,items:[item('Fornecedor',500)],...extra});
}
function postTx({direction='inflow',amount=1000,nature='revenue',partyType='organization',partyId=customerOrg.id,isDemo=false,status='posted',description='Liquidação',date='2026-08-25'}={}){
  const tx=finance.createTransaction({financialAccountId:account.id,amount,direction,financialNature:nature,counterpartyType:partyType,counterpartyId:partyId,transactionDate:date,originalDescription:description,status:'pending',isDemo});
  if(status==='posted')finance.post(tx.id);
  else if(status==='excluded')finance.exclude(tx.id,'teste');
  return tx;
}

test('1 criação de Nota de Entrada',()=>{const d=inDoc();assert.equal(d.direction,'incoming');assert.equal(d.status,'received');});
test('2 criação de Nota de Saída',()=>{const d=outDoc();assert.equal(d.direction,'outgoing');assert.equal(d.status,'issued');});
test('3 direção fiscal é atributo explícito',()=>{assert.throws(()=>fiscal.createDocument({direction:'saida'}),/Direção fiscal inválida/);});
test('4 fornecedor usa Organization canônica',()=>{const before=party.data.organizations.length,d=inDoc();assert.equal(d.supplierPartyId,supplier.id);assert.equal(party.data.organizations.length,before);});
test('5 cliente Organization usa identidade canônica',()=>{const before=party.data.organizations.length,d=outDoc();assert.equal(d.customerPartyId,customerOrg.id);assert.equal(party.data.organizations.length,before);});
test('6 cliente Person usa identidade canônica',()=>{const d=fiscal.createDocument({direction:'outgoing',documentType:'service',status:'draft',counterpartyType:'person',counterpartyId:customerPerson.id,items:[item('Consultoria',200)]});assert.equal(d.customerPartyId,customerPerson.id);});
test('7 parte inexistente é rejeitada',()=>{assert.throws(()=>fiscal.createDocument({direction:'incoming',counterpartyType:'organization',counterpartyId:'org_missing'}),/canônica não encontrada/);});
test('8 item único funciona',()=>{const d=outDoc({items:[item('Item A',250)]});assert.equal(fiscal.documentItems(d.id).length,1);assert.equal(d.totalAmount,250);});
test('9 múltiplos itens funcionam',()=>{const d=outDoc({items:[item('A',100),{description:'B',quantity:2,unit:'un',unitPrice:50}]});assert.equal(fiscal.documentItems(d.id).length,2);assert.equal(d.totalAmount,200);});
test('10 subtotal deriva dos itens',()=>{const d=outDoc({items:[{description:'A',quantity:2,unitPrice:125}]});assert.equal(d.subtotal,250);});
test('11 desconto de item reconcilia',()=>{const d=outDoc({items:[{description:'A',quantity:2,unitPrice:100,discountAmount:20}]});assert.equal(d.totalAmount,180);});
test('12 desconto do documento funciona',()=>{const d=outDoc({items:[item('A',500)],discountAmount:50});assert.equal(d.totalAmount,450);});
test('13 dedução funciona',()=>{const d=outDoc({items:[item('A',500)],deductionAmount:25});assert.equal(d.totalAmount,475);});
test('14 tributo explícito informativo não é inventado no total',()=>{const d=outDoc({items:[item('A',500)],taxes:[{taxType:'ISS',baseAmount:500,rate:5,amount:25,treatment:'informational'}]});assert.equal(d.taxAmount,25);assert.equal(d.totalAmount,500);});
test('15 tributo marcado added participa do total',()=>{const d=outDoc({items:[item('A',500)],taxes:[{taxType:'Taxa explícita',baseAmount:500,amount:20,treatment:'added'}]});assert.equal(d.totalAmount,520);});
test('16 retenção reduz valor líquido',()=>{const d=outDoc({items:[item('A',1000)],retentions:[{type:'IRRF',baseAmount:1000,amount:100}]});assert.equal(d.retentionAmount,100);assert.equal(d.netAmount,900);});
test('17 retenção não pode exceder base',()=>{assert.throws(()=>outDoc({retentions:[{type:'X',baseAmount:100,amount:101}]}),/excede a base/);});
test('18 moeda é preservada',()=>{const d=outDoc({currency:'USD'});assert.equal(d.currency,'USD');});
test('19 número e série são preservados',()=>{const d=outDoc({number:'1234',series:'A1'});assert.equal(d.number,'1234');assert.equal(d.series,'A1');});
test('20 chave de acesso é normalizada',()=>{const d=outDoc({accessKey:'12 34-AB'});assert.equal(d.accessKey,'1234AB');});
test('21 chave de 44 dígitos é reconhecida sem ser gerada',()=>{const d=outDoc({accessKey:'1'.repeat(44)});assert.equal(d.accessKeyValid,true);});
test('22 accessKey duplicada é bloqueio forte',()=>{const key='2'.repeat(44);outDoc({accessKey:key,number:'AK-A'});assert.throws(()=>outDoc({accessKey:key,number:'AK-B'}),/duplicado/);});
test('23 externalId duplicado é bloqueio forte',()=>{outDoc({externalId:'EXT-UNICO',number:'EX-A'});assert.throws(()=>outDoc({externalId:'EXT-UNICO',number:'EX-B'}),/duplicado/);});
test('24 emitente+número+série gera potencial duplicidade',()=>{const first=outDoc({number:'POT-1',series:'S'});const second=outDoc({number:'POT-1',series:'S'});assert.equal(first.potentialDuplicate,false);assert.equal(second.potentialDuplicate,true);});
test('25 origem manual é registrada',()=>{assert.equal(outDoc().source,'manual');});
test('26 origem import é registrada numa única coleção',()=>{const d=fiscal.createDocument({direction:'outgoing',source:'import',documentType:'other',status:'draft',counterpartyType:'organization',counterpartyId:customerOrg.id,totalAmount:50,number:'IMP-1'});assert.equal(d.source,'import');assert(fiscal.data.documents.includes(d));});
test('27 origem integration não aparece validada sem validador',()=>{const d=fiscal.createDocument({direction:'outgoing',source:'integration',sourceReference:'provider-x',documentType:'other',status:'draft',counterpartyType:'organization',counterpartyId:customerOrg.id,totalAmount:50,number:'INT-1'});assert.equal(d.integrationValidated,false);});
test('28 autorização oficial não pode ser simulada',()=>{assert.throws(()=>fiscal.createDocument({direction:'outgoing',source:'integration',sourceReference:'provider-x',authorizedAt:'2026-08-25T10:00:00Z',counterpartyType:'organization',counterpartyId:customerOrg.id}),/integração validada/);});
test('29 status fiscal não contém pagamento',()=>{for(const x of Fiscal.STATUSES)assert(!['paid','paga','pago'].includes(x));});
test('30 status Emitida é separado da liquidação',()=>{const d=outDoc();assert.equal(d.status,'issued');assert.equal(fiscal.settlement(d.id).status,'unlinked');});
test('31 criar nota não cria transação automaticamente',()=>{const before=finance.data.transactions.length;outDoc();assert.equal(finance.data.transactions.length,before);});
test('32 uma transação pode ser vinculada',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:100});fiscal.linkTransaction(d.id,tx.id);assert.equal(fiscal.documentLinks(d.id).length,1);});
test('33 múltiplas transações podem ser vinculadas',()=>{const d=outDoc({items:[item('A',100)]}),a=postTx({amount:40}),b=postTx({amount:60});fiscal.linkTransaction(d.id,a.id);fiscal.linkTransaction(d.id,b.id);assert.equal(fiscal.documentLinks(d.id).length,2);});
test('34 pagamento parcial é derivado',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:40});fiscal.linkTransaction(d.id,tx.id);const s=fiscal.settlement(d.id);assert.equal(s.status,'partial');assert.equal(s.settledAmount,40);assert.equal(s.balance,60);});
test('35 liquidação completa é derivada',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:100});fiscal.linkTransaction(d.id,tx.id);const s=fiscal.settlement(d.id);assert.equal(s.status,'settled');assert.equal(s.balance,0);});
test('36 transação excluded não conta como liquidação',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:100,status:'excluded'});fiscal.linkTransaction(d.id,tx.id);assert.equal(fiscal.settlement(d.id).settledAmount,0);});
test('37 transação demo não conta como liquidação',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:100,isDemo:true});fiscal.linkTransaction(d.id,tx.id);assert.equal(fiscal.settlement(d.id).settledAmount,0);});
test('38 transferência não conta como liquidação',()=>{const d=outDoc({items:[item('A',100)]}),tx=postTx({amount:100,nature:'transfer'});fiscal.linkTransaction(d.id,tx.id);assert.equal(fiscal.settlement(d.id).settledAmount,0);});
test('39 estorno em direção oposta reduz liquidação',()=>{const d=outDoc({items:[item('A',100)]}),a=postTx({amount:100}),b=postTx({direction:'outflow',amount:20,nature:'reversal'});fiscal.linkTransaction(d.id,a.id);fiscal.linkTransaction(d.id,b.id);assert.equal(fiscal.settlement(d.id).settledAmount,80);assert.equal(fiscal.settlement(d.id).status,'partial');});
test('40 chargeback em direção oposta reduz liquidação',()=>{const d=outDoc({items:[item('A',100)]}),a=postTx({amount:100}),b=postTx({direction:'outflow',amount:30,nature:'chargeback'});fiscal.linkTransaction(d.id,a.id);fiscal.linkTransaction(d.id,b.id);assert.equal(fiscal.settlement(d.id).settledAmount,70);});
test('41 nota de Entrada espera saída financeira',()=>{const d=inDoc({items:[item('A',100)]}),tx=postTx({direction:'outflow',amount:100,nature:'expense',partyId:supplier.id});fiscal.linkTransaction(d.id,tx.id);assert.equal(fiscal.settlement(d.id).status,'settled');});
test('42 reembolso de Entrada reduz liquidação',()=>{const d=inDoc({items:[item('A',100)]}),a=postTx({direction:'outflow',amount:100,nature:'expense',partyId:supplier.id}),b=postTx({direction:'inflow',amount:20,nature:'reimbursement',partyId:supplier.id});fiscal.linkTransaction(d.id,a.id);fiscal.linkTransaction(d.id,b.id);assert.equal(fiscal.settlement(d.id).settledAmount,80);});
test('43 desvincular transação funciona',()=>{const d=outDoc(),tx=postTx();fiscal.linkTransaction(d.id,tx.id);assert(fiscal.unlinkTransaction(d.id,tx.id));assert.equal(fiscal.documentLinks(d.id).length,0);});
test('44 match não cria duplicidade e é idempotente',()=>{const d=outDoc(),tx=postTx(),before=finance.data.transactions.length;const a=fiscal.linkTransaction(d.id,tx.id),b=fiscal.linkTransaction(d.id,tx.id);assert.equal(a.id,b.id);assert.equal(finance.data.transactions.length,before);assert.equal(fiscal.documentLinks(d.id).length,1);});
test('45 vínculo usa Match genérico de Transações',()=>{const d=outDoc(),tx=postTx();const link=fiscal.linkTransaction(d.id,tx.id);assert(finance.data.matches.some((m)=>m.id===link.matchId&&m.targetType==='fiscal_document'&&m.targetId===d.id));});
test('46 competenceDate fiscal é preservada',()=>{const d=outDoc({issueDate:'2026-08-25',competenceDate:'2026-07-31'});assert.equal(d.competenceDate,'2026-07-31');assert.equal(d.issueDate,'2026-08-25');});
test('47 competência fiscal não escreve recognitionDate',()=>{const d=outDoc({competenceDate:'2026-07-31'});assert(!('recognitionDate'in d));assert(!('recognitionDate'in fiscal.data));});
test('48 Produto é somente referência',()=>{const d=outDoc({productId:'product_123'});assert.equal(d.productId,'product_123');assert(!fiscal.data.products);});
test('49 Serviço é somente referência',()=>{const d=outDoc({serviceId:'service_123'});assert.equal(d.serviceId,'service_123');assert(!fiscal.data.services);});
test('50 Unidade é somente referência',()=>{const d=outDoc({businessUnitId:'unit_123'});assert.equal(d.businessUnitId,'unit_123');assert(!fiscal.data.businessUnits);});
test('51 Contrato é somente referência',()=>{const d=outDoc({contractId:'contract_123'});assert.equal(d.contractId,'contract_123');assert(!fiscal.data.contracts);});
test('52 XML metadata vira anexo referencial sem conteúdo falso',()=>{const d=outDoc({xmlMetadata:{fileName:'nota.xml',mimeType:'application/xml',hash:'ABC',storageReference:'store://abc'}});const a=fiscal.documentAttachments(d.id).find((x)=>x.kind==='xml');assert(a);assert.equal(a.fileName,'nota.xml');assert.equal(a.hash,'abc');assert(!('content'in a));});
test('53 PDF metadata vira referência sem DANFE falso',()=>{const d=outDoc({pdfMetadata:{fileName:'nota.pdf',mimeType:'application/pdf',storageReference:'store://pdf'}});const a=fiscal.documentAttachments(d.id).find((x)=>x.kind==='pdf');assert(a);assert.equal(a.fileName,'nota.pdf');assert(!('danfe'in a));});
test('54 anexos complementares funcionam como metadata',()=>{const d=outDoc(),a=fiscal.addAttachment(d.id,{kind:'proof',fileName:'comprovante.pdf',storageReference:'store://proof'});assert.equal(fiscal.documentAttachments(d.id).length,1);assert.equal(a.kind,'proof');});
test('55 remoção de anexo preserva histórico',()=>{const d=outDoc(),a=fiscal.addAttachment(d.id,{kind:'other',fileName:'x.txt'});fiscal.removeAttachment(a.id);assert(!fiscal.documentAttachments(d.id).some((x)=>x.id===a.id));assert(fiscal.data.history.some((x)=>x.documentId===d.id&&x.action==='document.attachment.removed'));});
test('56 cancelamento é status/histórico e não destrói documento',()=>{const d=outDoc();fiscal.markCancelled(d.id,{reference:'cancelado fora do sistema'});assert.equal(fiscal.getDocument(d.id).status,'cancelled');assert(fiscal.list({status:'cancelled',limit:0}).rows.some((x)=>x.id===d.id));});
test('57 cancelamento não é chamado de autorização oficial',()=>{const d=outDoc();fiscal.markCancelled(d.id);assert.equal(d.metadata.cancellationSource,'manual-record');});
test('58 histórico registra criação',()=>{const d=outDoc();assert(fiscal.data.history.some((x)=>x.documentId===d.id&&x.action==='document.created'));});
test('59 histórico registra vínculo e desvínculo',()=>{const d=outDoc(),tx=postTx();fiscal.linkTransaction(d.id,tx.id);fiscal.unlinkTransaction(d.id,tx.id);const actions=fiscal.data.history.filter((x)=>x.documentId===d.id).map((x)=>x.action);assert(actions.includes('document.transaction.linked'));assert(actions.includes('document.transaction.unlinked'));});
test('60 demo não aparece na consulta real',()=>{const d=outDoc({isDemo:true});assert(!fiscal.list({limit:0}).rows.some((x)=>x.id===d.id));assert(fiscal.list({includeDemo:true,limit:0}).rows.some((x)=>x.id===d.id));});
test('61 documento importado inconsistente registra divergência',()=>{const d=fiscal.createDocument({direction:'outgoing',source:'import',status:'draft',counterpartyType:'organization',counterpartyId:customerOrg.id,items:[item('A',100)],totalAmount:90,number:'IMP-MISMATCH'});assert.equal(d.reconciliationStatus,'inconsistent');assert(d.reconciliationIssues.includes('total_calculation_mismatch'));});
test('62 documento manual inconsistente é rejeitado',()=>{assert.throws(()=>outDoc({items:[item('A',100)],totalAmount:90}),/Totais não reconciliam/);});
test('63 total líquido informado divergente é rejeitado em manual',()=>{assert.throws(()=>outDoc({items:[item('A',100)],netAmount:80}),/Totais não reconciliam/);});
test('64 taxAmount importado divergente é sinalizado sem corrigir silenciosamente',()=>{const d=fiscal.createDocument({direction:'outgoing',source:'import',status:'draft',counterpartyType:'organization',counterpartyId:customerOrg.id,items:[item('A',100)],taxes:[{taxType:'X',amount:10}],taxAmount:12,number:'IMP-TAX'});assert.equal(d.taxAmount,12);assert(d.reconciliationIssues.includes('tax_total_mismatch'));});
test('65 retentionAmount importado divergente é sinalizado',()=>{const d=fiscal.createDocument({direction:'outgoing',source:'import',status:'draft',counterpartyType:'organization',counterpartyId:customerOrg.id,items:[item('A',100)],retentions:[{type:'X',baseAmount:100,amount:10}],retentionAmount:12,number:'IMP-RET'});assert.equal(d.retentionAmount,12);assert(d.reconciliationIssues.includes('retention_total_mismatch'));});
test('66 nenhuma fonte paralela incomingInvoices/outgoingInvoices/nfes/nfses',()=>{const src=fs.readFileSync(path.join(__dirname,'..','web','src','modules','finance','fiscal','core.js'),'utf8');for(const key of ['incomingInvoices','outgoingInvoices','nfes','nfses','customerInvoices','supplierInvoices'])assert(!src.includes(key));});
test('67 state fiscal canônico possui coleções únicas',()=>{for(const key of ['documents','items','taxes','retentions','links','attachments','history','imports'])assert(Array.isArray(fiscal.data[key]));});
test('68 paidAmount não é segunda fonte persistida',()=>{const d=outDoc();assert(!('paidAmount'in d));assert(!('paidAmount'in fiscal.data));});
test('69 status financeiro deriva links e não status fiscal',()=>{const d=outDoc();assert.equal(fiscal.settlement(d.id).status,'unlinked');const tx=postTx({amount:d.netAmount});fiscal.linkTransaction(d.id,tx.id);assert.equal(d.status,'issued');assert.equal(fiscal.settlement(d.id).status,'settled');});
test('70 sugestão de transação não cria vínculo automático',()=>{const d=outDoc({number:'SUG-1',items:[item('A',321)]}),tx=postTx({amount:321,description:'Pagamento SUG-1'}),before=fiscal.documentLinks(d.id).length;const suggestions=fiscal.suggestTransactions(d.id);assert(suggestions.some((x)=>x.tx.id===tx.id));assert.equal(fiscal.documentLinks(d.id).length,before);});
test('71 sugestão considera direção, valor, contraparte e número',()=>{const d=outDoc({number:'SCORE-1',items:[item('A',222)]}),tx=postTx({amount:222,description:'SCORE-1'});const s=fiscal.suggestTransactions(d.id).find((x)=>x.tx.id===tx.id);assert(s.score>=9);});
test('72 filtro por direção funciona',()=>{const result=fiscal.list({direction:'incoming',limit:0});assert(result.rows.every((x)=>x.direction==='incoming'));});
test('73 filtro por status fiscal funciona',()=>{const result=fiscal.list({status:'cancelled',limit:0});assert(result.rows.every((x)=>x.status==='cancelled'));});
test('74 filtro por Produto funciona',()=>{const d=outDoc({productId:'prod-filter'});assert(fiscal.list({productId:'prod-filter',limit:0}).rows.some((x)=>x.id===d.id));});
test('75 filtro por Serviço funciona',()=>{const d=outDoc({serviceId:'svc-filter'});assert(fiscal.list({serviceId:'svc-filter',limit:0}).rows.some((x)=>x.id===d.id));});
test('76 filtro por Unidade funciona',()=>{const d=outDoc({businessUnitId:'unit-filter'});assert(fiscal.list({businessUnitId:'unit-filter',limit:0}).rows.some((x)=>x.id===d.id));});
test('77 filtro com/sem transação funciona',()=>{const a=outDoc({number:'LINKED-A'}),b=outDoc({number:'LINKED-B'}),tx=postTx();fiscal.linkTransaction(a.id,tx.id);assert(fiscal.list({linked:'yes',limit:0}).rows.some((x)=>x.id===a.id));assert(fiscal.list({linked:'no',limit:0}).rows.some((x)=>x.id===b.id));});
test('78 busca encontra número, série e contraparte',()=>{const d=outDoc({number:'SEARCH-987',series:'ZZ'});assert(fiscal.list({search:'SEARCH-987',limit:0}).rows.some((x)=>x.id===d.id));assert(fiscal.list({search:'Cliente Organização',limit:0}).rows.some((x)=>x.id===d.id));});
test('79 accountingFeed expõe competência/tributos sem escrever Contabilidade',()=>{const d=outDoc({competenceDate:'2026-07-31',taxes:[{taxType:'ISS',amount:5}]});const feed=fiscal.accountingFeed({}).find((x)=>x.fiscalDocumentId===d.id);assert.equal(feed.competenceDate,'2026-07-31');assert.equal(feed.taxes.length,1);assert(!('recognitionDate'in feed));});
test('80 Invoice legado ambíguo não é migrado semanticamente',()=>{const isolated=Fiscal.createService(Fiscal.createState(),{idFactory,now,partyService:party,financeService:finance,companyProvider:()=>({partyType:'organization',partyId:company.id,legalName:'Valtren',document:'x',address:'y'}),defaultCurrencyProvider:()=> 'BRL'});const count=isolated.migrateLegacy([{id:'legacy-1',number:'1',customer:'Texto',value:100}]);assert.equal(count,0);assert.equal(isolated.data.metadata.legacyInvoiceUnresolvedCount,1);});
test('81 Invoice legado explicitamente fiscal exige referência canônica',()=>{const isolated=Fiscal.createService(Fiscal.createState(),{idFactory,now,partyService:party,financeService:finance,companyProvider:()=>({partyType:'organization',partyId:company.id,legalName:'Valtren',document:'x',address:'y'}),defaultCurrencyProvider:()=> 'BRL'});const count=isolated.migrateLegacy([{id:'legacy-2',canonicalFiscal:true,number:'2',counterpartyType:'organization',counterpartyId:'missing'}]);assert.equal(count,0);});
test('82 Invoice legado explicitamente fiscal pode virar adapter demo seguro',()=>{const isolated=Fiscal.createService(Fiscal.createState(),{idFactory,now,partyService:party,financeService:finance,companyProvider:()=>({partyType:'organization',partyId:company.id,legalName:'Valtren',document:'x',address:'y'}),defaultCurrencyProvider:()=> 'BRL'});const count=isolated.migrateLegacy([{id:'legacy-3',canonicalFiscal:true,direction:'outgoing',number:'3',counterpartyType:'organization',counterpartyId:customerOrg.id,totalAmount:100}]);assert.equal(count,1);const d=isolated.data.documents[0];assert.equal(d.isDemo,true);assert.equal(d.metadata.legacyInvoiceId,'legacy-3');});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
  const bundleCss=fs.readFileSync(path.join(__dirname,'..','assets','valtren-brand.css'),'utf8');
  test('83 bundle contém domínio fiscal canônico',()=>{assert(app.includes('ValtrenFiscalCore'));assert(app.includes('state.crmFiscalDocuments'));});
  test('84 rota canônica Notas Fiscais existe',()=>{assert(app.includes("if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();"));});
  test('85 alias /invoices não executa Invoice legado',()=>{assert(app.includes("if(path==='/crm/financeiro/invoices')return crmFiscalLegacyInvoicesRoute();"));assert(!app.includes('return crmRefInvoicesPage();'));});
  test('86 Invoice legado não possui página/modal executável',()=>{assert(!app.includes('function crmRefInvoicesPage()'));assert(!app.includes('function crmRefInvoiceModal()'));});
  test('87 Transações continua canônica',()=>{assert(app.includes("if(path==='/crm/financeiro')return crmTransactionsPage();"));assert(app.includes('state.crmFinancialTransactions'));});
  test('88 Contabilidade continua canônica',()=>{assert(app.includes("if(path==='/crm/financeiro/accounting')return crmAccountingPage();"));assert(app.includes('ValtrenAccountingCore'));});
  test('89 sidebar oficial permanece com seis itens',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),side=app.slice(start,end);for(const label of ['Transações','Contabilidade','Notas Fiscais','Rateios','Participações','Repasses'])assert(side.includes(label));for(const label of ['Categorias Financeiras','Regras de Categorização','Automações Financeiras'])assert(!side.includes(label));});
  test('90 CSS fiscal materializado',()=>{assert(bundleCss.includes('/* VALTREN FISCAL DOCUMENTS */'));assert(bundleCss.includes('@media(max-width:520px)'));});
  test('91 Configurações continua com seis abas',()=>{for(const label of ["['empresa','Empresa']","['notificacoes','Notificações']","['seguranca','Segurança']","['integracoes','Integrações']","['auditoria','Auditoria']","['usuarios','Usuários']"])assert(app.includes(label));});
  test('92 Administração continua com dois itens',()=>{assert(app.includes("['structure','Estrutura Organizacional'"));assert(app.includes("['assets','Patrimônio e Licenças'"));});
}
console.log(`Fiscal documents domain tests: ${passed} passed`);
