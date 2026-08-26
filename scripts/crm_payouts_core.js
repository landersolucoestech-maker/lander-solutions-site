(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenPayoutCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const OBLIGATION_STATUSES=['open','partial','paid','overdue','cancelled','superseded','blocked'];
  const RECONCILIATION_STATUSES=['unreconciled','partially_reconciled','reconciled'];
  const CONSISTENCY_STATUSES=['consistent','source_changed','source_superseded','source_superseded_with_payments','needs_review','blocked'];
  const PAYMENT_STATUSES=['active','unlinked'];
  const REVERSAL_NATURES=['refund','reimbursement','reversal','chargeback'];
  const FORBIDDEN_SETTLEMENT_NATURES=['transfer','refund','reimbursement','reversal','chargeback'];
  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const isoDate=(value)=>/^\d{4}-\d{2}-\d{2}$/.test(text(value))?text(value):'';
  const num=(value)=>{const n=Number(value);return Number.isFinite(n)?n:null;};
  const toCents=(value)=>{const n=num(value);if(n==null)throw new Error('Valor monetário inválido');return Math.round((n+Number.EPSILON)*100);};
  const fromCents=(value)=>Math.round(Number(value)||0)/100;
  const money=(value)=>fromCents(toCents(value));
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}
  function stable(value){if(value===null||typeof value!=='object')return JSON.stringify(value);if(Array.isArray(value))return `[${value.map(stable).join(',')}]`;return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${stable(value[key])}`).join(',')}}`;}
  function deterministicHash(value){const source=stable(value);let hash=2166136261;for(let i=0;i<source.length;i++){hash^=source.charCodeAt(i);hash=Math.imul(hash,16777619)>>>0;}return `fnv1a32:${hash.toString(16).padStart(8,'0')}`;}
  function todayIso(nowValue){const d=String(nowValue||new Date().toISOString());return d.slice(0,10);}

  function createState(options={}){
    const now=options.now||(()=>new Date().toISOString());
    return {schemaVersion:SCHEMA_VERSION,obligations:[],payments:[],transactionLinks:[],reconciliation:[],history:[],sourceSnapshots:[],legacyBindings:[],metadata:{createdAt:now(),legacyReviewed:false,legacySkipped:[]}};
  }
  function ensureState(input,options={}){
    const data=input&&typeof input==='object'?input:createState(options);
    for(const key of ['obligations','payments','transactionLinks','reconciliation','history','sourceSnapshots','legacyBindings'])if(!Array.isArray(data[key]))data[key]=[];
    if(!data.metadata||typeof data.metadata!=='object')data.metadata={};
    if(!Array.isArray(data.metadata.legacySkipped))data.metadata.legacySkipped=[];
    data.schemaVersion=SCHEMA_VERSION;return data;
  }

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const data=ensureState(store,{now});
    const participationFeedOption=options.participationFeed;
    const participationLookupOption=options.participationLookup||null;
    const financeOption=options.financeService;
    const partyOption=options.partyService;

    const dependency=(option,label,required=true)=>{const value=typeof option==='function'?option():option;if(required&&!value)throw new Error(`${label} indisponível`);return value||null;};
    const finance=()=>dependency(financeOption,'Financeiro → Transações canônico');
    const parties=()=>dependency(partyOption,'Pessoas/Organizações canônicas');
    const participationFeed=()=>{const fn=typeof participationFeedOption==='function'?participationFeedOption:null;if(!fn)throw new Error('Feed canônico de Participações indisponível');const rows=fn({});return Array.isArray(rows)?clone(rows):[];};
    const participationLookup=(id)=>{if(typeof participationLookupOption!=='function')return null;const row=participationLookupOption(id);return row?clone(row):null;};
    const getObligationRaw=(id)=>data.obligations.find((row)=>row.id===id)||null;
    const getPayment=(id)=>data.payments.find((row)=>row.id===id)||null;
    const paymentsFor=(id)=>data.payments.filter((row)=>row.obligationId===id&&row.status==='active');
    const history=(action,obligationId,before,after,metadata={})=>{const row={id:idFactory('payhist'),action,obligationId:obligationId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(row);return row;};
    const touch=(row)=>{row.updatedAt=now();row.updatedBy=actor()||null;return row;};

    function assertParty(type,id){if(!['person','organization'].includes(type)||!text(id))throw new Error('Beneficiário canônico inválido');const svc=parties();if(typeof svc.getEntity!=='function'||!svc.getEntity(type,id))throw new Error('Beneficiário canônico não encontrado');return true;}
    function partySnapshot(type,id){const svc=parties(),entity=svc.getEntity(type,id);if(!entity)return null;let document='';if(typeof svc.documentFor==='function'){const doc=type==='person'?svc.documentFor('person',id,'cpf'):svc.documentFor('organization',id,'cnpj');document=doc?.value||'';}return {partyType:type,partyId:id,name:type==='person'?(entity.fullName||id):(entity.legalName||entity.tradeName||entity.name||id),document};}
    function normalizeFeedRow(source={}){
      const amountDue=money(source.amountDue);if(amountDue<0)throw new Error('Obrigação de Repasse não aceita valor devido negativo');
      const participationCalculationId=text(source.participationCalculationId);if(!participationCalculationId)throw new Error('Obrigação sem Participação aprovada');
      const participantPartyType=text(source.participantPartyType),participantPartyId=text(source.participantPartyId);assertParty(participantPartyType,participantPartyId);
      const periodStart=isoDate(source.periodStart),periodEnd=isoDate(source.periodEnd);if(!periodStart||!periodEnd||periodEnd<periodStart)throw new Error('Período da Participação inválido');
      const dueDate=source.dueDate==null||source.dueDate===''?null:isoDate(source.dueDate);if(source.dueDate&&!dueDate)throw new Error('Data de vencimento inválida');
      const currency=text(source.currency||'BRL').toUpperCase();if(!currency)throw new Error('Moeda da obrigação é obrigatória');
      return {participationCalculationId,contractId:text(source.contractId),contractVersionId:text(source.contractVersionId),economicRuleId:text(source.economicRuleId),participantPartyType,participantPartyId,productId:text(source.productId),serviceId:text(source.serviceId),businessUnitId:text(source.businessUnitId),periodStart,periodEnd,currency,amountDue,dueDate,approvedAt:source.approvedAt||null,sourceSnapshotHash:text(source.sourceSnapshotHash)};
    }
    function sourceSnapshotPayload(source){return {participationCalculationId:source.participationCalculationId,contractId:source.contractId,contractVersionId:source.contractVersionId,economicRuleId:source.economicRuleId,participantPartyType:source.participantPartyType,participantPartyId:source.participantPartyId,productId:source.productId,serviceId:source.serviceId,businessUnitId:source.businessUnitId,periodStart:source.periodStart,periodEnd:source.periodEnd,currency:source.currency,amountDue:source.amountDue,dueDate:source.dueDate,approvedAt:source.approvedAt,sourceSnapshotHash:source.sourceSnapshotHash};}
    function createObligationFromFeed(source){
      const normalized=normalizeFeedRow(source),snapshot=sourceSnapshotPayload(normalized),row={id:idFactory('payoutobl'),...normalized,status:'open',consistencyStatus:'consistent',reconciliationStatus:'unreconciled',sourceStatus:'eligible',beneficiarySnapshot:partySnapshot(normalized.participantPartyType,normalized.participantPartyId),isDemo:false,createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null,metadata:{obligationSnapshotHash:deterministicHash(snapshot)}};
      data.obligations.push(row);data.sourceSnapshots.push({id:idFactory('payoutsrc'),obligationId:row.id,participationCalculationId:row.participationCalculationId,snapshot:clone(snapshot),snapshotHash:deterministicHash(snapshot),createdAt:now()});history('obligation.created',row.id,null,row,{participationCalculationId:row.participationCalculationId});return row;
    }
    function activeTransactionPayment(transactionId){return data.payments.find((row)=>row.financialTransactionId===transactionId&&row.status==='active')||null;}
    function reversalRows(payment){
      const svc=finance(),tx=svc.getTransaction(payment.financialTransactionId);if(!tx)return [];
      return (svc.data?.transactions||[]).filter((row)=>row.relatedTransactionId===tx.id&&row.status==='posted'&&!row.isDemo&&row.direction==='inflow'&&REVERSAL_NATURES.includes(row.financialNature));
    }
    function paymentEffectiveCents(payment){
      if(!payment||payment.status!=='active')return 0;const svc=finance(),tx=svc.getTransaction(payment.financialTransactionId);if(!tx||tx.status!=='posted'||tx.isDemo||tx.direction!=='outflow'||FORBIDDEN_SETTLEMENT_NATURES.includes(tx.financialNature))return 0;
      if(String(tx.currency||'BRL').toUpperCase()!==String(payment.currency||'BRL').toUpperCase())return 0;
      const base=toCents(payment.amount),txCents=Math.max(1,toCents(tx.amount)),reverseTotal=reversalRows(payment).reduce((sum,row)=>sum+toCents(row.amount),0),allocatedReversal=Math.round(reverseTotal*base/txCents);return Math.max(0,base-Math.min(base,allocatedReversal));
    }
    function paymentEffectiveAmount(payment){return fromCents(paymentEffectiveCents(payment));}
    function paidCents(obligationId){return paymentsFor(obligationId).reduce((sum,row)=>sum+paymentEffectiveCents(row),0);}
    function reconciliationStatus(obligationId){const rows=paymentsFor(obligationId).filter((row)=>paymentEffectiveCents(row)>0);if(!rows.length)return 'unreconciled';const reconciled=rows.filter((row)=>!!row.reconciledAt).length;return reconciled===0?'unreconciled':reconciled===rows.length?'reconciled':'partially_reconciled';}
    function derivedStatus(row,paid,open){
      if(row.status==='cancelled')return 'cancelled';
      if(row.sourceStatus==='superseded'&&paid<=0)return 'superseded';
      if(['blocked','needs_review','source_changed'].includes(row.consistencyStatus)&&paid<=0)return 'blocked';
      if(open<=0)return 'paid';if(paid>0)return 'partial';if(row.dueDate&&row.dueDate<todayIso(now()))return 'overdue';return 'open';
    }
    function viewObligation(row){if(!row)return null;const paid=paidCents(row.id),due=toCents(row.amountDue),open=Math.max(0,due-paid),status=derivedStatus(row,paid,open),recon=reconciliationStatus(row.id);return {...clone(row),amountPaid:fromCents(paid),openBalance:fromCents(open),status,reconciliationStatus:recon};}
    function getObligation(id){return viewObligation(getObligationRaw(id));}
    function detectPaymentSourceChanges(row){
      let changed=false;for(const payment of paymentsFor(row.id)){const tx=finance().getTransaction(payment.financialTransactionId);const invalid=!tx||tx.status!=='posted'||tx.isDemo||tx.direction!=='outflow'||FORBIDDEN_SETTLEMENT_NATURES.includes(tx.financialNature)||String(tx.currency||'BRL').toUpperCase()!==row.currency;if(invalid){changed=true;continue;}if(tx.counterpartyId&&tx.counterpartyId!==row.participantPartyId)changed=true;
        const rev=reversalRows(payment),hash=deterministicHash(rev.map((x)=>({id:x.id,amount:x.amount,status:x.status,nature:x.financialNature,direction:x.direction})));if(payment.lastReversalHash!==hash){const before=payment.lastReversalHash||'';payment.lastReversalHash=hash;payment.lastReversalAt=now();touch(payment);if(before)history('payment.reversal_detected',row.id,{reversalHash:before},{reversalHash:hash},{paymentId:payment.id,transactionId:payment.financialTransactionId,reversalIds:rev.map((x)=>x.id)});}
      }return changed;
    }
    function refreshConsistency(id){
      const row=getObligationRaw(id);if(!row)throw new Error('Obrigação de Repasse não encontrada');const before={consistencyStatus:row.consistencyStatus,sourceStatus:row.sourceStatus,status:row.status};let next=row.consistencyStatus;
      const source=participationLookup(row.participationCalculationId);if(source){if(source.workflowStatus==='superseded'){row.sourceStatus='superseded';next=paidCents(id)>0?'source_superseded_with_payments':'source_superseded';}else if(source.workflowStatus!=='approved'||source.consistencyStatus!=='consistent'||source.isDemo){row.sourceStatus='ineligible';next='source_changed';}else{row.sourceStatus='eligible';const sourceHash=text(source.sourceSnapshotHash),amount=money(source.participationAmount??source.amountDue??row.amountDue),currency=text(source.currency||row.currency).toUpperCase();if((sourceHash&&sourceHash!==row.sourceSnapshotHash)||amount!==row.amountDue||currency!==row.currency)next='source_changed';else if(['source_changed','needs_review','blocked'].includes(next))next='consistent';}}
      if(detectPaymentSourceChanges(row)&&next==='consistent')next='source_changed';row.consistencyStatus=next;const view=viewObligation(row);row.status=view.status;row.reconciliationStatus=view.reconciliationStatus;touch(row);if(before.consistencyStatus!==row.consistencyStatus||before.sourceStatus!==row.sourceStatus||before.status!==row.status)history('obligation.consistency_changed',id,before,{consistencyStatus:row.consistencyStatus,sourceStatus:row.sourceStatus,status:row.status});return getObligation(id);
    }
    function refreshAll(){for(const row of data.obligations)refreshConsistency(row.id);return data.obligations.map(viewObligation);}

    function syncObligations(){
      const feed=participationFeed(),seen=new Set(),created=[],updated=[];
      for(const sourceRaw of feed){if(sourceRaw?.isDemo)continue;const source=normalizeFeedRow(sourceRaw),key=source.participationCalculationId;seen.add(key);let row=data.obligations.find((x)=>x.participationCalculationId===key);if(!row){row=createObligationFromFeed(source);created.push(row.id);continue;}
        const current=sourceSnapshotPayload(source),original={participationCalculationId:row.participationCalculationId,contractId:row.contractId,contractVersionId:row.contractVersionId,economicRuleId:row.economicRuleId,participantPartyType:row.participantPartyType,participantPartyId:row.participantPartyId,productId:row.productId,serviceId:row.serviceId,businessUnitId:row.businessUnitId,periodStart:row.periodStart,periodEnd:row.periodEnd,currency:row.currency,amountDue:row.amountDue,dueDate:row.dueDate,approvedAt:row.approvedAt,sourceSnapshotHash:row.sourceSnapshotHash};if(deterministicHash(current)!==deterministicHash(original)){const before=clone(row);row.consistencyStatus='source_changed';row.sourceStatus='changed';row.metadata={...(row.metadata||{}),latestSourceSnapshot:clone(current),latestSourceSnapshotHash:deterministicHash(current)};touch(row);history('obligation.source_changed',row.id,before,row,{preservedOriginal:true});updated.push(row.id);}else if(row.sourceStatus!=='eligible'||row.consistencyStatus!=='consistent'){row.sourceStatus='eligible';if(!detectPaymentSourceChanges(row))row.consistencyStatus='consistent';touch(row);updated.push(row.id);}refreshConsistency(row.id);
      }
      for(const row of data.obligations){if(seen.has(row.participationCalculationId)||row.status==='cancelled')continue;const source=participationLookup(row.participationCalculationId);const before=clone(row);if(source?.workflowStatus==='superseded'){row.sourceStatus='superseded';row.consistencyStatus=paidCents(row.id)>0?'source_superseded_with_payments':'source_superseded';if(paidCents(row.id)<=0)row.status='superseded';}else if(source){row.sourceStatus='ineligible';row.consistencyStatus='source_changed';if(paidCents(row.id)<=0)row.status='blocked';}else{row.sourceStatus='missing';row.consistencyStatus='needs_review';if(paidCents(row.id)<=0)row.status='blocked';}touch(row);if(before.sourceStatus!==row.sourceStatus||before.consistencyStatus!==row.consistencyStatus||before.status!==row.status){history(source?.workflowStatus==='superseded'?'obligation.participation_superseded':'obligation.source_unavailable',row.id,before,row,{participationCalculationId:row.participationCalculationId});updated.push(row.id);}refreshConsistency(row.id);}
      return {created:created.length,updated:[...new Set(updated)].length,total:data.obligations.length,obligationIds:created};
    }

    function assertSettlementEligible(row,tx){
      if(!tx)throw new Error('Transação de pagamento não encontrada');if(tx.status!=='posted')throw new Error('Somente transação lançada pode liquidar Repasse');if(tx.isDemo)throw new Error('Transação demo não pode liquidar Repasse');if(tx.direction!=='outflow')throw new Error('Repasse requer transação de saída');if(FORBIDDEN_SETTLEMENT_NATURES.includes(tx.financialNature))throw new Error('Transferência/estorno/reembolso não pode ser usado como pagamento principal');if(String(tx.currency||'BRL').toUpperCase()!==row.currency)throw new Error('Moeda da transação é incompatível com a obrigação');if(tx.counterpartyId&&(tx.counterpartyId!==row.participantPartyId||tx.counterpartyType!==row.participantPartyType))throw new Error('Contraparte da transação não corresponde ao beneficiário canônico');return true;
    }
    function linkPayment(obligationId,transactionId,input={}){
      const row=getObligationRaw(obligationId);if(!row)throw new Error('Obrigação de Repasse não encontrada');refreshConsistency(obligationId);const view=getObligation(obligationId);if(['cancelled','superseded','blocked'].includes(view.status)||row.consistencyStatus!=='consistent')throw new Error('Obrigação não está apta a receber pagamento');const svc=finance(),tx=svc.getTransaction(transactionId);assertSettlementEligible(row,tx);
      const existing=activeTransactionPayment(transactionId);if(existing){if(existing.obligationId===obligationId)return clone(existing);throw new Error('Transação já vinculada a outro Repasse');}
      const amount=input.amount==null||input.amount===''?money(tx.amount):money(input.amount);if(!(amount>0))throw new Error('Valor do pagamento deve ser maior que zero');if(toCents(amount)>toCents(tx.amount))throw new Error('Valor vinculado excede a transação');if(toCents(amount)>toCents(view.openBalance))throw new Error('Pagamento excede o saldo da obrigação');
      const match=typeof svc.addMatch==='function'?svc.addMatch(transactionId,{targetType:'payout',targetId:obligationId,amount}):null;
      const payment={id:idFactory('payoutpay'),obligationId,financialTransactionId:transactionId,amount,currency:row.currency,status:'active',matchId:match?.id||'',linkedAt:now(),linkedBy:actor()||null,reconciledAt:null,reconciledBy:null,notes:text(input.notes),lastReversalHash:'',metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.payments.push(payment);data.transactionLinks.push({id:idFactory('payoutlink'),obligationId,paymentId:payment.id,financialTransactionId:transactionId,matchId:payment.matchId,status:'active',createdAt:now(),createdBy:actor()||null});history('payment.linked',obligationId,null,payment,{transactionId,amount});refreshConsistency(obligationId);return clone(payment);
    }
    function unlinkPayment(paymentId,reason=''){
      const payment=getPayment(paymentId);if(!payment||payment.status!=='active')throw new Error('Pagamento vinculado não encontrado');if(payment.reconciledAt)throw new Error('Desconcilie o pagamento antes de desvincular');const row=getObligationRaw(payment.obligationId),before=clone(payment);payment.status='unlinked';payment.unlinkedAt=now();payment.unlinkedBy=actor()||null;payment.unlinkedReason=text(reason);touch(payment);const link=data.transactionLinks.find((x)=>x.paymentId===payment.id&&x.status==='active');if(link){link.status='inactive';link.updatedAt=now();}if(payment.matchId&&typeof finance().removeMatch==='function')finance().removeMatch(payment.matchId);history('payment.unlinked',payment.obligationId,before,payment,{reason:text(reason)});refreshConsistency(row.id);return clone(payment);
    }
    function reconcilePayment(paymentId){
      const payment=getPayment(paymentId);if(!payment||payment.status!=='active')throw new Error('Pagamento não encontrado');if(paymentEffectiveCents(payment)<=0)throw new Error('Pagamento sem efeito financeiro não pode ser conciliado');if(payment.reconciledAt)return clone(payment);const row=getObligationRaw(payment.obligationId);assertSettlementEligible(row,finance().getTransaction(payment.financialTransactionId));if(typeof finance().reconcile==='function')finance().reconcile(payment.financialTransactionId);const before=clone(payment);payment.reconciledAt=now();payment.reconciledBy=actor()||null;touch(payment);data.reconciliation.push({id:idFactory('payoutrecon'),obligationId:payment.obligationId,paymentId:payment.id,transactionId:payment.financialTransactionId,action:'reconciled',amount:paymentEffectiveAmount(payment),at:payment.reconciledAt,actorId:payment.reconciledBy});history('payment.reconciled',payment.obligationId,before,payment,{transactionId:payment.financialTransactionId,amount:paymentEffectiveAmount(payment)});refreshConsistency(payment.obligationId);return clone(payment);
    }
    function unreconcilePayment(paymentId){
      const payment=getPayment(paymentId);if(!payment||payment.status!=='active')throw new Error('Pagamento não encontrado');if(!payment.reconciledAt)return clone(payment);if(typeof finance().unreconcile==='function')finance().unreconcile(payment.financialTransactionId);const before=clone(payment),at=now(),by=actor()||null;payment.reconciledAt=null;payment.reconciledBy=null;touch(payment);data.reconciliation.push({id:idFactory('payoutrecon'),obligationId:payment.obligationId,paymentId:payment.id,transactionId:payment.financialTransactionId,action:'unreconciled',amount:paymentEffectiveAmount(payment),at,actorId:by});history('payment.unreconciled',payment.obligationId,before,payment,{transactionId:payment.financialTransactionId});refreshConsistency(payment.obligationId);return clone(payment);
    }
    function cancelObligation(id,reason=''){
      const row=getObligationRaw(id);if(!row)throw new Error('Obrigação não encontrada');const message=text(reason);if(!message)throw new Error('Motivo do cancelamento é obrigatório');if(paymentsFor(id).length)throw new Error('Obrigação com pagamento vinculado não pode ser cancelada diretamente');if(row.status==='cancelled')return getObligation(id);const before=clone(row);row.status='cancelled';row.cancelledAt=now();row.cancelledBy=actor()||null;row.cancellationReason=message;touch(row);history('obligation.cancelled',id,before,row,{reason:message});return getObligation(id);
    }
    function suggestTransactions(obligationId,limit=8){
      const row=getObligationRaw(obligationId);if(!row)throw new Error('Obrigação não encontrada');const view=getObligation(obligationId),svc=finance(),partyName=fold(row.beneficiarySnapshot?.name||'');let rows=svc.query({status:'posted',direction:'outflow',includeDemo:false,limit:0}).rows.filter((tx)=>!FORBIDDEN_SETTLEMENT_NATURES.includes(tx.financialNature)&&String(tx.currency||'BRL').toUpperCase()===row.currency&&!activeTransactionPayment(tx.id));
      rows=rows.map((tx)=>{let score=0;const reasons=[];if(tx.counterpartyId===row.participantPartyId&&tx.counterpartyType===row.participantPartyType){score+=50;reasons.push('Beneficiário compatível');}else if(tx.counterpartyId){score-=40;reasons.push('Contraparte diferente');}if(Math.abs(toCents(tx.amount)-toCents(view.openBalance))<=1){score+=35;reasons.push('Valor igual ao saldo');}else if(toCents(tx.amount)<=toCents(view.openBalance)){score+=15;reasons.push('Valor cabe no saldo');}const blob=fold([tx.originalDescription,tx.normalizedDescription].join(' '));if(partyName&&blob.includes(partyName)){score+=10;reasons.push('Descrição menciona beneficiário');}if(row.dueDate&&tx.transactionDate){const days=Math.abs((new Date(`${tx.transactionDate}T00:00:00Z`)-new Date(`${row.dueDate}T00:00:00Z`))/86400000);if(days<=7){score+=8;reasons.push('Data próxima ao vencimento');}}return {...clone(tx),matchScore:score,matchReasons:reasons};}).filter((tx)=>tx.matchScore>=0).sort((a,b)=>b.matchScore-a.matchScore||Math.abs(toCents(a.amount)-toCents(view.openBalance))-Math.abs(toCents(b.amount)-toCents(view.openBalance)));return rows.slice(0,Math.max(1,Number(limit)||8));
    }
    function query(filters={}){
      refreshAll();let rows=data.obligations.map(viewObligation);if(!filters.includeDemo)rows=rows.filter((r)=>!r.isDemo);if(filters.status)rows=rows.filter((r)=>r.status===filters.status);if(filters.reconciliationStatus)rows=rows.filter((r)=>r.reconciliationStatus===filters.reconciliationStatus);if(filters.participantPartyId)rows=rows.filter((r)=>r.participantPartyId===filters.participantPartyId);if(filters.contractId)rows=rows.filter((r)=>r.contractId===filters.contractId);if(filters.productId)rows=rows.filter((r)=>r.productId===filters.productId);if(filters.serviceId)rows=rows.filter((r)=>r.serviceId===filters.serviceId);if(filters.businessUnitId)rows=rows.filter((r)=>r.businessUnitId===filters.businessUnitId);if(filters.from)rows=rows.filter((r)=>r.periodEnd>=filters.from);if(filters.to)rows=rows.filter((r)=>r.periodStart<=filters.to);if(filters.due==='with_due')rows=rows.filter((r)=>!!r.dueDate);if(filters.due==='without_due')rows=rows.filter((r)=>!r.dueDate);if(filters.due==='overdue')rows=rows.filter((r)=>r.status==='overdue');if(filters.search){const q=fold(filters.search);rows=rows.filter((r)=>fold([r.id,r.participationCalculationId,r.contractId,r.contractVersionId,r.economicRuleId,r.beneficiarySnapshot?.name,r.productId,r.serviceId,r.businessUnitId,r.periodStart,r.periodEnd,r.amountDue,r.amountPaid,r.openBalance].join(' ')).includes(q));}rows.sort((a,b)=>String(a.dueDate||'9999-12-31').localeCompare(String(b.dueDate||'9999-12-31'))||String(b.periodEnd).localeCompare(String(a.periodEnd)));const total=rows.length,limit=Math.min(100,Math.max(1,Number(filters.limit)||50)),page=Math.max(1,Number(filters.page)||1);return {rows:clone(rows.slice((page-1)*limit,page*limit)),total,page,limit,pages:Math.max(1,Math.ceil(total/limit))};
    }
    function payments(id){const row=getObligationRaw(id);if(!row)throw new Error('Obrigação não encontrada');return clone(paymentsFor(id).map((p)=>({...p,effectiveAmount:paymentEffectiveAmount(p),reversalTransactions:reversalRows(p).map((x)=>x.id)})));}
    function memory(id){const row=getObligationRaw(id);if(!row)throw new Error('Obrigação não encontrada');return {obligation:getObligation(id),payments:payments(id),transactionLinks:clone(data.transactionLinks.filter((x)=>x.obligationId===id)),reconciliation:clone(data.reconciliation.filter((x)=>x.obligationId===id)),sourceSnapshot:clone(data.sourceSnapshots.find((x)=>x.obligationId===id)||null),history:clone(data.history.filter((x)=>x.obligationId===id))};}
    function summaryByCurrency(filters={}){const rows=query({...filters,limit:100,page:1}).rows,all=[];let cursor=1,total=query({...filters,limit:1,page:1}).total;while(all.length<total){const pageRows=query({...filters,limit:100,page:cursor++}).rows;if(!pageRows.length)break;all.push(...pageRows);}const map={};for(const row of all){const c=row.currency||'BRL';if(!map[c])map[c]={currency:c,amountDue:0,amountPaid:0,openBalance:0,overdue:0};map[c].amountDue=fromCents(toCents(map[c].amountDue)+toCents(row.amountDue));map[c].amountPaid=fromCents(toCents(map[c].amountPaid)+toCents(row.amountPaid));map[c].openBalance=fromCents(toCents(map[c].openBalance)+toCents(row.openBalance));if(row.status==='overdue')map[c].overdue=fromCents(toCents(map[c].overdue)+toCents(row.openBalance));}return Object.values(map);}
    function migrateLegacy(records=[]){if(data.metadata.legacyReviewed)return {migrated:0,skipped:data.metadata.legacySkipped.length};let migrated=0;for(const item of records||[]){if(!item||typeof item!=='object')continue;if(!item.participationCalculationId)data.metadata.legacySkipped.push({sourceId:text(item.id),reason:'insufficient_participation_traceability'});else data.metadata.legacySkipped.push({sourceId:text(item.id),participationCalculationId:text(item.participationCalculationId),reason:'legacy_requires_canonical_obligation_sync'});}data.metadata.legacyReviewed=true;data.metadata.legacyReviewedAt=now();return {migrated,skipped:data.metadata.legacySkipped.length};}

    return {data,getObligation,getPayment,payments,memory,syncObligations,refreshConsistency,refreshAll,linkPayment,unlinkPayment,reconcilePayment,unreconcilePayment,cancelObligation,suggestTransactions,query,summaryByCurrency,paymentEffectiveAmount,migrateLegacy,deterministicHash};
  }

  return {SCHEMA_VERSION,OBLIGATION_STATUSES,RECONCILIATION_STATUSES,CONSISTENCY_STATUSES,PAYMENT_STATUSES,REVERSAL_NATURES,FORBIDDEN_SETTLEMENT_NATURES,createState,ensureState,createService,clone,text,fold,isoDate,toCents,fromCents,money,deterministicHash};
});
