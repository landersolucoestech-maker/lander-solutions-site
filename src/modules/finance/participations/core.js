(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenParticipationCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const WORKFLOW_STATUSES=['draft','review','approved','rejected','superseded'];
  const CALCULATION_STATUSES=['pending','calculated','blocked'];
  const CONSISTENCY_STATUSES=['consistent','source_changed','rule_changed','conflict','needs_review'];
  const BASIS_TYPES=['gross_revenue','net_revenue','distributable_base','product_result','service_result','custom_reference'];
  const RULE_TYPES=['percentage','fixed','tiered','custom'];
  const PARTY_TYPES=['person','organization'];
  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const isoDate=(value)=>/^\d{4}-\d{2}-\d{2}$/.test(text(value))?text(value):'';
  const num=(value)=>{const n=Number(value);return Number.isFinite(n)?n:null;};
  const toCents=(value)=>{const n=num(value);if(n==null)throw new Error('Valor monetário inválido');return Math.round((n+Number.EPSILON)*100);};
  const fromCents=(value)=>Math.round(Number(value)||0)/100;
  const money=(value)=>fromCents(toCents(value));
  const percent=(value)=>{const n=num(value);return n==null?null:Math.round(n*1000000)/1000000;};
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}
  function addDays(value,days){const d=new Date(`${value}T00:00:00Z`);d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10);}
  const dayAfter=(value)=>addDays(value,1);
  const dayBefore=(value)=>addDays(value,-1);
  const maxDate=(a,b)=>!a?b:!b?a:(a>b?a:b);
  const minDate=(a,b)=>!a?b:!b?a:(a<b?a:b);
  function dateSpan(from,to){if(!isoDate(from)||!isoDate(to)||to<from)return 0;return Math.round((new Date(`${to}T00:00:00Z`)-new Date(`${from}T00:00:00Z`))/86400000)+1;}
  function stable(value){
    if(value===null||typeof value!=='object')return JSON.stringify(value);
    if(Array.isArray(value))return `[${value.map(stable).join(',')}]`;
    return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${stable(value[key])}`).join(',')}}`;
  }
  function deterministicHash(value){const source=stable(value);let hash=2166136261;for(let i=0;i<source.length;i++){hash^=source.charCodeAt(i);hash=Math.imul(hash,16777619)>>>0;}return `fnv1a32:${hash.toString(16).padStart(8,'0')}`;}
  function dimensionKey(rule={}){return rule.productId?`product:${rule.productId}`:rule.serviceId?`service:${rule.serviceId}`:rule.businessUnitId?`business_unit:${rule.businessUnitId}`:'global';}
  function ruleFamilyKey(rule={}){return [rule.contractId,rule.participantPartyType,rule.participantPartyId,rule.basisType,dimensionKey(rule),String(rule.currency||'BRL').toUpperCase()].join('|');}
  function ruleWindow(rule,from,to){return {from:maxDate(from,isoDate(rule.effectiveFrom)||from),to:minDate(to,isoDate(rule.effectiveUntil)||to)};}
  function permissionCode(value){const f=fold(value);if(/impost|tribut/.test(f))return 'taxes';if(/rateio|alocac/.test(f))return 'allocations';if(/comiss/.test(f))return 'commissions';if(/taxa|fee/.test(f))return 'fees';if(/custo/.test(f))return 'costs';return f.replace(/[^a-z0-9]+/g,'_');}

  function createState(options={}){
    const now=options.now||(()=>new Date().toISOString());
    return {schemaVersion:SCHEMA_VERSION,calculations:[],calculationSegments:[],baseComponents:[],deductions:[],approvals:[],history:[],sourceSnapshots:[],legacyBindings:[],metadata:{createdAt:now(),legacyReviewed:false,legacySkipped:[]}};
  }
  function ensureState(input,options={}){
    const data=input&&typeof input==='object'?input:createState(options);
    for(const key of ['calculations','calculationSegments','baseComponents','deductions','approvals','history','sourceSnapshots','legacyBindings'])if(!Array.isArray(data[key]))data[key]=[];
    if(!data.metadata||typeof data.metadata!=='object')data.metadata={};
    if(!Array.isArray(data.metadata.legacySkipped))data.metadata.legacySkipped=[];
    data.schemaVersion=SCHEMA_VERSION;return data;
  }

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const data=ensureState(store,{now});
    const contractFeed=options.contractRulesFeed;
    const contractResolver=options.contractRuleResolver||null;
    const accountingOption=options.accountingService;
    const fiscalOption=options.fiscalService;
    const allocationOption=options.costAllocationService;
    const partyOption=options.partyService;
    const customBaseResolver=options.customBaseResolver||null;
    const customRuleResolver=options.customRuleResolver||null;
    const defaultAccountingBasis=options.defaultAccountingBasis||'accrual';

    const dependency=(option,label,required=true)=>{const value=typeof option==='function'?option():option;if(required&&!value)throw new Error(`${label} indisponível`);return value||null;};
    const rules=(filters={})=>{const fn=typeof contractFeed==='function'?contractFeed:null;if(!fn)throw new Error('Feed econômico de Contratos indisponível');const rows=fn(filters);return Array.isArray(rows)?clone(rows):[];};
    const accounting=()=>dependency(accountingOption,'Contabilidade canônica');
    const fiscal=()=>dependency(fiscalOption,'Notas Fiscais canônicas',false);
    const allocations=()=>dependency(allocationOption,'Rateios canônicos',false);
    const parties=()=>dependency(partyOption,'Pessoas/Organizações canônicas');
    const getCalculation=(id)=>data.calculations.find((row)=>row.id===id)||null;
    const getSegments=(id)=>data.calculationSegments.filter((row)=>row.calculationId===id).sort((a,b)=>a.periodStart.localeCompare(b.periodStart));
    const getBaseComponents=(id,segmentId='')=>data.baseComponents.filter((row)=>row.calculationId===id&&(!segmentId||row.segmentId===segmentId));
    const getDeductions=(id,segmentId='')=>data.deductions.filter((row)=>row.calculationId===id&&(!segmentId||row.segmentId===segmentId));
    const getSourceSnapshot=(id)=>data.sourceSnapshots.find((row)=>row.calculationId===id)||null;
    const history=(action,calculationId,before,after,metadata={})=>{const row={id:idFactory('parthist'),action,calculationId:calculationId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(row);return row;};
    const approval=(action,row,metadata={})=>{const event={id:idFactory('partapproval'),calculationId:row.id,action,revisionNumber:row.revisionNumber,at:now(),actorId:actor()||null,metadata:clone(metadata)};data.approvals.push(event);return event;};

    function assertParty(type,id){if(!PARTY_TYPES.includes(type)||!text(id))throw new Error('Participante econômico canônico inválido');const svc=parties();if(typeof svc.getEntity!=='function'||!svc.getEntity(type,id))throw new Error('Participante econômico canônico não encontrado');return true;}
    function partySnapshot(type,id){const svc=parties(),entity=svc.getEntity(type,id);if(!entity)return null;let document='';if(typeof svc.documentFor==='function'){const doc=type==='person'?svc.documentFor('person',id,'cpf'):svc.documentFor('organization',id,'cnpj');document=doc?.value||'';}return {partyType:type,partyId:id,name:type==='person'?(entity.fullName||id):(entity.legalName||entity.tradeName||entity.name||id),document};}
    function normalizedRule(raw={}){
      return {contractId:text(raw.contractId),contractNumber:text(raw.contractNumber),versionId:text(raw.versionId||raw.contractVersionId),versionNumber:Number(raw.versionNumber)||0,ruleId:text(raw.ruleId||raw.economicRuleId),ruleName:text(raw.ruleName||raw.name||'Regra econômica'),participantPartyType:text(raw.participantPartyType),participantPartyId:text(raw.participantPartyId),basisType:text(raw.basisType),type:text(raw.type||raw.ruleType),percentage:raw.percentage==null?null:percent(raw.percentage),fixedValue:raw.fixedValue==null?null:money(raw.fixedValue),deductions:[...new Set((raw.deductions||[]).map(text).filter(Boolean))],effectiveFrom:isoDate(raw.effectiveFrom),effectiveUntil:isoDate(raw.effectiveUntil),productId:text(raw.productId),serviceId:text(raw.serviceId),businessUnitId:text(raw.businessUnitId),currency:text(raw.currency||'BRL').toUpperCase()||'BRL',metadata:clone(raw.metadata||{})};
    }
    function ruleSnapshot(rule){return {contractId:rule.contractId,contractVersionId:rule.versionId,contractVersionNumber:rule.versionNumber,economicRuleId:rule.ruleId,ruleName:rule.ruleName,participantPartyType:rule.participantPartyType,participantPartyId:rule.participantPartyId,basisType:rule.basisType,ruleType:rule.type,percentage:rule.percentage,fixedValue:rule.fixedValue,deductions:clone(rule.deductions),effectiveFrom:rule.effectiveFrom,effectiveUntil:rule.effectiveUntil,productId:rule.productId,serviceId:rule.serviceId,businessUnitId:rule.businessUnitId,currency:rule.currency,metadata:clone(rule.metadata||{})};}

    function familyRules(input={}){
      const from=isoDate(input.periodStart||input.from),to=isoDate(input.periodEnd||input.to)||from;if(!from||!to||to<from)throw new Error('Período fechado válido é obrigatório');
      let rows=rules({from,to,includeHistorical:true,contractId:text(input.contractId),participantPartyType:text(input.participantPartyType),participantPartyId:text(input.participantPartyId)}).map(normalizedRule);
      if(input.economicRuleId){const seed=rows.find((r)=>r.ruleId===input.economicRuleId)||normalizedRule(rules({from,to,includeHistorical:true}).find((r)=>String(r.ruleId||r.economicRuleId)===String(input.economicRuleId))||{});if(!seed.ruleId)return {from,to,rows:[],familyKey:'',seed:null};const key=ruleFamilyKey(seed);rows=rows.filter((r)=>ruleFamilyKey(r)===key);return {from,to,rows,familyKey:key,seed};}
      if(input.familyKey)rows=rows.filter((r)=>ruleFamilyKey(r)===input.familyKey);
      else if(input.basisType)rows=rows.filter((r)=>r.basisType===input.basisType);
      if(input.productId)rows=rows.filter((r)=>r.productId===input.productId);
      if(input.serviceId)rows=rows.filter((r)=>r.serviceId===input.serviceId);
      if(input.businessUnitId)rows=rows.filter((r)=>r.businessUnitId===input.businessUnitId);
      const seed=rows[0]||null;return {from,to,rows,familyKey:seed?ruleFamilyKey(seed):'',seed};
    }

    function resolveSegments(input={}){
      const info=familyRules(input),{from,to}=info,rows=info.rows;
      if(!rows.length)return {status:'none',message:'Nenhuma regra econômica contratual elegível para o período.',familyKey:info.familyKey,rules:[],segments:[]};
      const boundaries=new Set([from,dayAfter(to)]);
      for(const rule of rows){const w=ruleWindow(rule,from,to);if(w.to<w.from)continue;boundaries.add(w.from);boundaries.add(dayAfter(w.to));}
      const sorted=[...boundaries].sort(),segments=[];
      for(let i=0;i<sorted.length-1;i++){
        const start=sorted[i],end=minDate(to,dayBefore(sorted[i+1]));if(end<from||start>to||end<start)continue;
        const active=rows.filter((rule)=>{const w=ruleWindow(rule,from,to);return w.from<=start&&w.to>=end;});
        if(active.length===0)return {status:'gap',message:'Período possui intervalo sem regra econômica contratual vigente.',familyKey:info.familyKey,rules:rows,segments};
        if(active.length>1)return {status:'conflict',message:'Conflito contratual de vigência.',familyKey:info.familyKey,rules:rows,segments:[...segments,{periodStart:start,periodEnd:end,rules:clone(active)}]};
        const rule=active[0];let resolverStatus='';
        if(typeof contractResolver==='function'){
          try{const resolved=contractResolver({from:start,to:end,contractId:rule.contractId,participantPartyType:rule.participantPartyType,participantPartyId:rule.participantPartyId,basisType:rule.basisType});resolverStatus=resolved?.status||'';}catch{resolverStatus='error';}
        }
        segments.push({periodStart:start,periodEnd:end,rule,resolverStatus});
      }
      if(!segments.length)return {status:'none',message:'Nenhuma regra econômica contratual elegível para o período.',familyKey:info.familyKey,rules:rows,segments:[]};
      return {status:'resolved',familyKey:info.familyKey,rules:rows,segments};
    }

    function accountingFilters(rule,segment){
      const metadata=rule.metadata||{},basis=['cash','accrual'].includes(metadata.accountingBasis)?metadata.accountingBasis:defaultAccountingBasis;
      const filters={from:segment.periodStart,to:segment.periodEnd,basis};if(rule.productId)filters.productId=rule.productId;if(rule.serviceId)filters.serviceId=rule.serviceId;if(rule.businessUnitId)filters.businessUnitId=rule.businessUnitId;return filters;
    }
    function accountingRows(rule,segment){const svc=accounting(),filters=accountingFilters(rule,segment),dre=svc.buildDre(filters),entries=typeof svc.listEntries==='function'?svc.listEntries(filters):dre.rows;const incompatible=dre.rows.filter((row)=>String(row.transaction?.currency||rule.currency||'BRL').toUpperCase()!==rule.currency);if(incompatible.length)return {blocked:`Moeda incompatível nas fontes contábeis: ${[...new Set(incompatible.map((r)=>r.transaction?.currency||''))].join(', ')}`,filters,dre,entries};const pending=(entries||[]).filter((row)=>Array.isArray(row.issues)&&row.issues.length);return {filters,dre,entries,pending};}
    function componentFromAccounting(row,rule,segment,kind='accounting'){
      const section=row.classification?.section||'',amount=money(row.contribution||0),id=text(row.transaction?.id),dim=dimensionKey(rule);return {id:idFactory('basecomp'),type:section||kind,sourceType:'transaction',sourceId:id,description:row.classification?.name||row.transaction?.originalDescription||'Movimentação contábil',amount:Math.abs(amount),signedAmount:amount,sign:amount<0?-1:1,periodStart:segment.periodStart,periodEnd:segment.periodEnd,dimension:dim,currency:String(row.transaction?.currency||rule.currency).toUpperCase(),sourceKey:`accounting:${id}:${section}:${dim}`,metadata:{classificationId:row.classification?.id||'',financialNature:row.transaction?.financialNature||'',accountingDate:row.date||'',accountingBasis:accountingFilters(rule,segment).basis}};}

    function resolveBasis(rule,segment,basisType=rule.basisType,depth=0){
      if(depth>2)return {blocked:'Referência circular de base econômica.'};
      if(!BASIS_TYPES.includes(basisType))return {blocked:'Base econômica contratual inválida.'};
      if(basisType==='custom_reference'){
        if(typeof customBaseResolver!=='function')return {blocked:'Base personalizada requer configuração explícita.'};
        const result=customBaseResolver({rule:clone(rule),periodStart:segment.periodStart,periodEnd:segment.periodEnd});if(!result||num(result.amount)==null)return {blocked:'Base personalizada não pôde ser resolvida de forma determinística.'};const currency=String(result.currency||rule.currency).toUpperCase();if(currency!==rule.currency)return {blocked:'Moeda incompatível na base personalizada.'};return {basisType,amount:money(result.amount),grossBase:money(result.amount),components:(result.components||[]).map((c)=>({...clone(c),id:c.id||idFactory('basecomp'),currency,periodStart:segment.periodStart,periodEnd:segment.periodEnd})),includedSourceKeys:new Set((result.components||[]).map((c)=>c.sourceKey).filter(Boolean)),accountingBasis:null,metadata:clone(result.metadata||{})};
      }
      if(basisType==='distributable_base'){
        const source=text(rule.metadata?.baseSource);
        if(!['gross_revenue','net_revenue','product_result','service_result'].includes(source))return {blocked:'Base distribuível requer origem explícita na regra contratual.'};
        const result=resolveBasis(rule,segment,source,depth+1);if(result.blocked)return result;return {...result,basisType:'distributable_base',metadata:{...(result.metadata||{}),baseSource:source}};
      }
      if(basisType==='product_result'&&!rule.productId)return {blocked:'Resultado do Produto requer productId contratual.'};
      if(basisType==='service_result'&&!rule.serviceId)return {blocked:'Resultado do Serviço requer serviceId contratual.'};
      const source=accountingRows(rule,segment);if(source.blocked)return {blocked:source.blocked};if(source.pending.length)return {blocked:'Fontes contábeis possuem pendências que exigem revisão.',consistencyStatus:'needs_review',pending:clone(source.pending)};
      let selected=[],amount=0;
      if(basisType==='gross_revenue'){selected=source.dre.rows.filter((r)=>r.classification?.section==='gross_revenue');amount=source.dre.summary.grossRevenue;}
      else if(basisType==='net_revenue'){selected=source.dre.rows.filter((r)=>['gross_revenue','deductions'].includes(r.classification?.section));amount=source.dre.summary.netRevenue;}
      else if(basisType==='product_result'||basisType==='service_result'){selected=source.dre.rows;amount=source.dre.summary.finalResult;}
      const components=selected.map((row)=>componentFromAccounting(row,rule,segment));return {basisType,amount:money(amount),grossBase:money(amount),components,includedSourceKeys:new Set(components.map((c)=>c.sourceKey)),accountingBasis:source.filters.basis,accountingRows:source.dre.rows,metadata:{rowCount:selected.length}};
    }

    function allocationComponentForRow(row,rule){
      const svc=allocations();if(!svc||typeof svc.accountingProjection!=='function')return null;const txId=row.transaction?.id;if(!txId)return null;const projection=svc.accountingProjection(txId);if(!projection?.allocation||projection.allocation.status!=='posted')return null;if(projection.allocation.consistencyStatus!=='consistent')return {blocked:true,allocation:projection.allocation};const targetType=rule.productId?'product':rule.serviceId?'service':rule.businessUnitId?'business_unit':'';const targetId=rule.productId||rule.serviceId||rule.businessUnitId||'';if(!targetType)return null;const lines=(projection.lines||[]).filter((line)=>(line.destinationType||line.dimension)===targetType&&(line.destinationId||line.productId||line.serviceId||line.businessUnitId)===targetId);if(!lines.length)return null;return {allocation:projection.allocation,lines};
    }

    function resolveContractDeductions(rule,segment,basis){
      const permissions=[...new Set((rule.deductions||[]).map(permissionCode).filter(Boolean))],deductions=[],seen=new Set(),svc=accounting(),filters=accountingFilters(rule,segment),rows=svc.analyze(filters);
      const included=basis.includedSourceKeys||new Set();
      const add=(item)=>{const unique=item.economicKey||`${item.sourceType}:${item.sourceId}:${item.deductionType}`;if(seen.has(unique))return;seen.add(unique);const alreadyIncluded=!!item.sourceKey&&included.has(item.sourceKey);deductions.push({...item,id:item.id||idFactory('deduct'),amount:money(item.amount),appliedAmount:alreadyIncluded?0:money(item.amount),alreadyIncludedInBase:alreadyIncluded,contractPermission:item.contractPermission||item.deductionType,periodStart:segment.periodStart,periodEnd:segment.periodEnd,currency:rule.currency});};
      const taxAllowed=permissions.includes('taxes'),costAllowed=permissions.includes('costs'),allocationAllowed=permissions.includes('allocations'),commissionAllowed=permissions.includes('commissions'),feeAllowed=permissions.includes('fees');
      for(const row of rows){const section=row.classification?.section||'',name=fold(row.classification?.name||''),signed=Number(row.contribution||0),amount=Math.abs(signed);if(!(amount>0))continue;let type='';if(taxAllowed&&section==='deductions'&&/tribut|impost/.test(name))type='taxes';else if(costAllowed&&section==='costs')type='costs';else if(commissionAllowed&&/comiss/.test(name))type='commissions';else if(feeAllowed&&/taxa|fee/.test(name))type='fees';const allocationInfo=section==='costs'?allocationComponentForRow(row,rule):null;if(allocationInfo?.blocked&&allocationAllowed)return {blocked:'Rateio necessário ao cálculo está inconsistente.',consistencyStatus:'needs_review',deductions};if(!type&&allocationAllowed&&allocationInfo?.allocation)type='allocations';if(!type)continue;let sourceType='transaction',sourceId=row.transaction.id,description=row.classification?.name||row.transaction?.originalDescription||type,economicKey=`tx:${row.transaction.id}:${dimensionKey(rule)}:${type}`;if(allocationInfo?.allocation){sourceType='cost_allocation';sourceId=allocationInfo.allocation.id;description=`Rateio ${allocationInfo.allocation.name||allocationInfo.allocation.id}`;economicKey=`tx:${row.transaction.id}:${dimensionKey(rule)}:${type}`;}const comp=componentFromAccounting(row,rule,segment);add({deductionType:type,sourceType,sourceId,description,amount,sourceKey:comp.sourceKey,economicKey,metadata:{transactionId:row.transaction.id,classificationId:row.classification?.id||'',allocationLineIds:allocationInfo?.lines?.map((x)=>x.id).filter(Boolean)||[]}});}

      if(taxAllowed){const fiscalSvc=fiscal();if(fiscalSvc&&typeof fiscalSvc.accountingFeed==='function'){
        const docs=fiscalSvc.accountingFeed({from:segment.periodStart,to:segment.periodEnd,productId:rule.productId||'',serviceId:rule.serviceId||'',businessUnitId:rule.businessUnitId||''});
        const accountedTxIds=new Set(rows.filter((row)=>row.classification?.section==='deductions'&&/tribut|impost/.test(fold(row.classification?.name||''))).map((row)=>row.transaction?.id).filter(Boolean));
        for(const doc of docs){if(doc.isDemo||['cancelled','rejected','archived','draft'].includes(doc.status))continue;if(String(doc.currency||rule.currency).toUpperCase()!==rule.currency)return {blocked:'Moeda incompatível em documento fiscal usado como dedução.',deductions};const linked=(doc.transactionIds||[]).some((id)=>accountedTxIds.has(id));for(const tax of doc.taxes||[]){if(!(Number(tax.amount)>0))continue;const key=`fiscal:${doc.fiscalDocumentId}:tax:${tax.id||tax.taxType}`;if(linked){deductions.push({id:idFactory('deduct'),deductionType:'taxes',sourceType:'fiscal_document',sourceId:doc.fiscalDocumentId,description:tax.taxType||'Tributo',amount:money(tax.amount),appliedAmount:0,alreadyIncludedInBase:true,contractPermission:'taxes',periodStart:segment.periodStart,periodEnd:segment.periodEnd,currency:rule.currency,economicKey:key,metadata:{linkedAccountingTransaction:true,taxId:tax.id||''}});continue;}add({deductionType:'taxes',sourceType:'fiscal_document',sourceId:doc.fiscalDocumentId,description:tax.taxType||'Tributo',amount:tax.amount,economicKey:key,metadata:{taxId:tax.id||'',transactionIds:clone(doc.transactionIds||[])}});}}
      }}
      const totalCents=deductions.reduce((sum,row)=>sum+toCents(row.appliedAmount||0),0);return {deductions,total:fromCents(totalCents),permissions};
    }

    function calculateRule(rule,segment){
      assertParty(rule.participantPartyType,rule.participantPartyId);
      if(!BASIS_TYPES.includes(rule.basisType))return {blocked:'Base econômica contratual inválida.'};if(!RULE_TYPES.includes(rule.type))return {blocked:'Tipo de regra econômica inválido.'};
      const basis=resolveBasis(rule,segment);if(basis.blocked)return {blocked:basis.blocked,consistencyStatus:basis.consistencyStatus||'needs_review',pending:basis.pending||[]};
      const deductionResult=resolveContractDeductions(rule,segment,basis);if(deductionResult.blocked)return {blocked:deductionResult.blocked,consistencyStatus:deductionResult.consistencyStatus||'needs_review'};
      const initialCents=toCents(basis.amount),deductionsCents=toCents(deductionResult.total),distributableCents=initialCents-deductionsCents;let participationCents=0,ruleDetail={};
      if(rule.type==='percentage'){
        if(rule.percentage==null||rule.percentage<=0||rule.percentage>100)return {blocked:'Percentual contratual inválido.'};participationCents=Math.round(distributableCents*rule.percentage/100);ruleDetail={percentage:rule.percentage};
      }else if(rule.type==='fixed'){
        if(rule.fixedValue==null||rule.fixedValue<0)return {blocked:'Valor fixo contratual incompleto.'};const policy=text(rule.metadata?.prorationPolicy),frequency=text(rule.metadata?.fixedFrequency||rule.metadata?.frequency);if(frequency&&['monthly','month','mensal'].includes(fold(frequency))){const monthStart=`${segment.periodStart.slice(0,7)}-01`,monthEnd=dayBefore(`${addDays(monthStart,32).slice(0,7)}-01`),full=segment.periodStart===monthStart&&segment.periodEnd===monthEnd;if(!full&&!policy)return {blocked:'Regra fixa parcial requer política explícita de prorrata.'};if(!full&&policy==='daily'){participationCents=Math.round(toCents(rule.fixedValue)*dateSpan(segment.periodStart,segment.periodEnd)/dateSpan(monthStart,monthEnd));}else if(!full&&policy!=='none'&&policy!=='full')return {blocked:'Política de prorrata fixa não suportada de forma determinística.'};else participationCents=toCents(rule.fixedValue);}else participationCents=toCents(rule.fixedValue);ruleDetail={fixedValue:rule.fixedValue,prorationPolicy:policy||null,frequency:frequency||null};
      }else if(rule.type==='tiered'){
        const tiers=Array.isArray(rule.metadata?.tiers)?rule.metadata.tiers:[];if(!tiers.length)return {blocked:'Regra por faixas requer tiers completos e explícitos.'};const sorted=clone(tiers).sort((a,b)=>Number(a.from||0)-Number(b.from||0));let matched=null;const base=fromCents(distributableCents);for(const tier of sorted){const from=Number(tier.from||0),to=tier.to==null||tier.to===''?Infinity:Number(tier.to),pct=Number(tier.percentage);if(!Number.isFinite(from)||!Number.isFinite(to)&&to!==Infinity||!Number.isFinite(pct)||pct<0||pct>100||to<from)return {blocked:'Tiers contratuais incompletos ou ambíguos.'};if(base>=from&&base<=to){if(matched)return {blocked:'Tiers contratuais sobrepostos.'};matched={from,to,percentage:pct};}}if(!matched)return {blocked:'Nenhuma faixa contratual cobre a base calculada.'};participationCents=Math.round(distributableCents*matched.percentage/100);ruleDetail={tier:matched};
      }else if(rule.type==='custom'){
        if(typeof customRuleResolver!=='function')return {blocked:'Regra personalizada requer resolver formal e determinístico.'};const result=customRuleResolver({rule:clone(rule),periodStart:segment.periodStart,periodEnd:segment.periodEnd,distributableBase:fromCents(distributableCents),baseComponents:clone(basis.components),deductions:clone(deductionResult.deductions)});if(!result||num(result.amount)==null)return {blocked:'Regra personalizada não pôde ser resolvida de forma determinística.'};if(String(result.currency||rule.currency).toUpperCase()!==rule.currency)return {blocked:'Moeda incompatível no resolver personalizado.'};participationCents=toCents(result.amount);ruleDetail={resolverReference:text(result.resolverReference||rule.metadata?.resolverReference)};
      }
      return {grossBase:fromCents(initialCents),calculationBase:fromCents(initialCents),deductionsTotal:fromCents(deductionsCents),distributableBase:fromCents(distributableCents),participationAmount:fromCents(participationCents),baseComponents:basis.components,deductions:deductionResult.deductions,accountingBasis:basis.accountingBasis,ruleDetail,baseMetadata:basis.metadata||{}};
    }

    function preview(input={}){
      const resolved=resolveSegments(input),periodStart=isoDate(input.periodStart||input.from),periodEnd=isoDate(input.periodEnd||input.to)||periodStart;
      if(resolved.status!=='resolved')return {workflowStatus:'draft',calculationStatus:'blocked',consistencyStatus:resolved.status==='conflict'?'conflict':'needs_review',periodStart,periodEnd,familyKey:resolved.familyKey||'',message:resolved.message,segments:clone(resolved.segments||[]),baseComponents:[],deductions:[],participationAmount:null};
      const segmentResults=[],baseComponents=[],deductions=[];let totalParticipation=0,totalInitial=0,totalDeductions=0,totalDistributable=0;
      for(const segment of resolved.segments){const rule=segment.rule,result=calculateRule(rule,segment);if(result.blocked)return {workflowStatus:'draft',calculationStatus:'blocked',consistencyStatus:result.consistencyStatus||'needs_review',periodStart,periodEnd,familyKey:resolved.familyKey,message:result.blocked,segments:[...segmentResults,{periodStart:segment.periodStart,periodEnd:segment.periodEnd,rule:ruleSnapshot(rule),blocked:result.blocked}],baseComponents,deductions,participationAmount:null};const segmentId=idFactory('partsegpreview'),row={id:segmentId,periodStart:segment.periodStart,periodEnd:segment.periodEnd,contractId:rule.contractId,contractNumber:rule.contractNumber,contractVersionId:rule.versionId,contractVersionNumber:rule.versionNumber,economicRuleId:rule.ruleId,ruleName:rule.ruleName,basisType:rule.basisType,ruleType:rule.type,percentage:rule.percentage,fixedAmount:rule.fixedValue,currency:rule.currency,productId:rule.productId,serviceId:rule.serviceId,businessUnitId:rule.businessUnitId,grossBase:result.grossBase,calculationBase:result.calculationBase,deductionsTotal:result.deductionsTotal,distributableBase:result.distributableBase,participationAmount:result.participationAmount,accountingBasis:result.accountingBasis,ruleSnapshot:ruleSnapshot(rule),ruleDetail:result.ruleDetail};segmentResults.push(row);for(const item of result.baseComponents)baseComponents.push({...clone(item),segmentId});for(const item of result.deductions)deductions.push({...clone(item),segmentId});totalParticipation+=toCents(result.participationAmount);totalInitial+=toCents(result.calculationBase);totalDeductions+=toCents(result.deductionsTotal);totalDistributable+=toCents(result.distributableBase);}
      const first=resolved.segments[0].rule,last=resolved.segments[resolved.segments.length-1].rule,ruleSnapshots=segmentResults.map((s)=>s.ruleSnapshot),sourceMemory={segments:segmentResults.map(({id,...s})=>s),baseComponents:baseComponents.map(({id,segmentId,...x})=>x),deductions:deductions.map(({id,segmentId,...x})=>x)};const sourceSnapshotHash=deterministicHash(sourceMemory),ruleSnapshotHash=deterministicHash(ruleSnapshots);
      return {workflowStatus:'draft',calculationStatus:'calculated',consistencyStatus:'consistent',periodStart,periodEnd,familyKey:resolved.familyKey,contractId:first.contractId,contractNumber:first.contractNumber,contractVersionId:first.versionId,contractVersionNumber:first.versionNumber,economicRuleId:first.ruleId,participantPartyType:first.participantPartyType,participantPartyId:first.participantPartyId,participantSnapshot:partySnapshot(first.participantPartyType,first.participantPartyId),basisType:first.basisType,ruleType:segmentResults.length===1?first.type:'segmented',percentage:segmentResults.length===1?first.percentage:null,fixedAmount:segmentResults.length===1?first.fixedValue:null,productId:first.productId,serviceId:first.serviceId,businessUnitId:first.businessUnitId,currency:first.currency,grossBase:fromCents(totalInitial),calculationBase:fromCents(totalInitial),deductionsTotal:fromCents(totalDeductions),distributableBase:fromCents(totalDistributable),participationAmount:fromCents(totalParticipation),segments:segmentResults,baseComponents,deductions,ruleSnapshots,sourceMemory,sourceSnapshotHash,ruleSnapshotHash,segmentCount:segmentResults.length,firstVersionId:first.versionId,lastVersionId:last.versionId,message:''};
    }

    function previewEligible(input={}){
      const from=isoDate(input.periodStart||input.from),to=isoDate(input.periodEnd||input.to)||from;if(!from||!to||to<from)throw new Error('Período fechado válido é obrigatório');const rows=rules({from,to,includeHistorical:true}).map(normalizedRule).filter((r)=>!input.contractId||r.contractId===input.contractId);const keys=[...new Set(rows.map(ruleFamilyKey))];return keys.map((familyKey)=>preview({periodStart:from,periodEnd:to,familyKey}));
    }

    function duplicateActive(previewResult,excludeId=''){
      return data.calculations.find((row)=>row.id!==excludeId&&row.familyKey===previewResult.familyKey&&row.periodStart===previewResult.periodStart&&row.periodEnd===previewResult.periodEnd&&['draft','review','approved'].includes(row.workflowStatus)&&!row.isDemo)||null;
    }
    function persistPreview(result,input={}){
      if(!result.periodStart||!result.periodEnd)throw new Error('Preview sem período válido');if(result.calculationStatus==='calculated')assertParty(result.participantPartyType,result.participantPartyId);const duplicate=duplicateActive(result);if(duplicate&&!input.supersedesCalculationId)throw new Error(`Já existe cálculo ativo para a mesma obrigação econômica: ${duplicate.id}`);const id=input.id||idFactory('partcalc'),revisionNumber=Math.max(1,Number(input.revisionNumber)||1),row={id,familyKey:result.familyKey||'',contractId:result.contractId||'',contractNumber:result.contractNumber||'',contractVersionId:result.contractVersionId||'',contractVersionNumber:result.contractVersionNumber||0,economicRuleId:result.economicRuleId||'',participantPartyType:result.participantPartyType||'',participantPartyId:result.participantPartyId||'',participantSnapshot:clone(result.participantSnapshot||null),productId:result.productId||'',serviceId:result.serviceId||'',businessUnitId:result.businessUnitId||'',periodStart:result.periodStart,periodEnd:result.periodEnd,currency:result.currency||'BRL',ruleType:result.ruleType||'',basisType:result.basisType||'',percentage:result.percentage??null,fixedAmount:result.fixedAmount??null,grossBase:result.grossBase??null,calculationBase:result.calculationBase??null,deductionsTotal:result.deductionsTotal??null,distributableBase:result.distributableBase??null,participationAmount:result.participationAmount??null,workflowStatus:'draft',calculationStatus:result.calculationStatus||'pending',consistencyStatus:result.consistencyStatus||'needs_review',blockingReason:result.message||'',sourceSnapshotHash:result.sourceSnapshotHash||'',ruleSnapshotHash:result.ruleSnapshotHash||'',ruleSnapshot:clone(result.ruleSnapshots||[]),revisionNumber,supersedesCalculationId:text(input.supersedesCalculationId),supersededAt:null,supersededBy:null,submittedAt:null,submittedBy:null,approvedAt:null,approvedBy:null,rejectedAt:null,rejectedBy:null,rejectionReason:'',metadata:clone(input.metadata||{}),isDemo:!!input.isDemo,createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.calculations.push(row);
      for(const segment of result.segments||[]){const segmentId=idFactory('partseg');data.calculationSegments.push({...clone(segment),id:segmentId,calculationId:id});const oldId=segment.id;for(const comp of (result.baseComponents||[]).filter((x)=>x.segmentId===oldId))data.baseComponents.push({...clone(comp),id:idFactory('basecomp'),calculationId:id,segmentId});for(const ded of (result.deductions||[]).filter((x)=>x.segmentId===oldId))data.deductions.push({...clone(ded),id:idFactory('deduct'),calculationId:id,segmentId});}
      const source={id:idFactory('partsnapshot'),calculationId:id,hash:row.sourceSnapshotHash,ruleHash:row.ruleSnapshotHash,memory:clone(result.sourceMemory||{}),createdAt:now(),createdBy:actor()||null};data.sourceSnapshots.push(source);history(row.calculationStatus==='blocked'?'calculation.blocked':'calculation.created',id,null,row,{blockingReason:row.blockingReason});return row;
    }
    function createCalculation(input={}){return persistPreview(preview(input),input);}
    function createBatch(input={}){const results=previewEligible(input),created=[];for(const result of results){if(duplicateActive(result))continue;created.push(persistPreview(result,input));}return created;}

    function assertMutableDraft(id){const row=getCalculation(id);if(!row)throw new Error('Participação não encontrada');if(row.workflowStatus!=='draft')throw new Error('Somente cálculo em Rascunho pode ser alterado');return row;}
    function recomputeCurrent(row){return preview({periodStart:row.periodStart,periodEnd:row.periodEnd,familyKey:row.familyKey,contractId:row.contractId,participantPartyType:row.participantPartyType,participantPartyId:row.participantPartyId,basisType:row.basisType});}
    function refreshConsistency(id){const row=getCalculation(id);if(!row)throw new Error('Participação não encontrada');if(row.isDemo)return row;const current=recomputeCurrent(row),before=row.consistencyStatus;let status='consistent';if(current.calculationStatus==='blocked')status=current.consistencyStatus==='conflict'?'conflict':'needs_review';else if(current.ruleSnapshotHash!==row.ruleSnapshotHash)status='rule_changed';else if(current.sourceSnapshotHash!==row.sourceSnapshotHash)status='source_changed';row.consistencyStatus=status;if(before!==status){row.updatedAt=now();row.updatedBy=actor()||null;history(status==='source_changed'?'source.changed':status==='rule_changed'?'rule.changed':'consistency.changed',id,{consistencyStatus:before},{consistencyStatus:status},{currentSourceSnapshotHash:current.sourceSnapshotHash||'',currentRuleSnapshotHash:current.ruleSnapshotHash||''});}return row;}
    function refreshAllConsistency(){for(const row of data.calculations.filter((x)=>!x.isDemo&&['draft','review','approved'].includes(x.workflowStatus)))refreshConsistency(row.id);return data.calculations;}
    function submitToReview(id){const row=assertMutableDraft(id);if(row.calculationStatus!=='calculated')throw new Error('Cálculo bloqueado não pode ser enviado para revisão');refreshConsistency(id);if(row.consistencyStatus!=='consistent')throw new Error('Cálculo possui inconsistência e precisa ser recalculado');const before=clone(row);row.workflowStatus='review';row.submittedAt=now();row.submittedBy=actor()||null;row.updatedAt=now();row.updatedBy=actor()||null;history('calculation.sent_to_review',id,before,row);approval('submitted',row);return row;}
    function reject(id,reason=''){const row=getCalculation(id);if(!row)throw new Error('Participação não encontrada');if(row.workflowStatus!=='review')throw new Error('Somente cálculo em revisão pode ser rejeitado');const message=text(reason);if(!message)throw new Error('Motivo da rejeição é obrigatório');const before=clone(row);row.workflowStatus='rejected';row.rejectedAt=now();row.rejectedBy=actor()||null;row.rejectionReason=message;row.updatedAt=now();row.updatedBy=actor()||null;history('calculation.rejected',id,before,row,{reason:message});approval('rejected',row,{reason:message});return row;}
    function approve(id){const row=getCalculation(id);if(!row)throw new Error('Participação não encontrada');if(row.workflowStatus!=='review')throw new Error('Somente cálculo em revisão pode ser aprovado');const current=recomputeCurrent(row);if(current.calculationStatus!=='calculated'||current.consistencyStatus!=='consistent')throw new Error(current.message||'Cálculo atual não está consistente');if(current.ruleSnapshotHash!==row.ruleSnapshotHash||current.sourceSnapshotHash!==row.sourceSnapshotHash){row.consistencyStatus=current.ruleSnapshotHash!==row.ruleSnapshotHash?'rule_changed':'source_changed';history('approval.revalidation_failed',id,null,{consistencyStatus:row.consistencyStatus});throw new Error('Fontes ou regra contratual mudaram após o cálculo; crie nova revisão');}const before=clone(row);row.workflowStatus='approved';row.approvedAt=now();row.approvedBy=actor()||null;row.updatedAt=now();row.updatedBy=actor()||null;row.metadata={...(row.metadata||{}),approvedCalculationVersion:row.revisionNumber,approvedSourceSnapshotHash:row.sourceSnapshotHash,approvedRuleSnapshotHash:row.ruleSnapshotHash};history('calculation.approved',id,before,row);approval('approved',row,{sourceSnapshotHash:row.sourceSnapshotHash,ruleSnapshotHash:row.ruleSnapshotHash});if(row.supersedesCalculationId){const old=getCalculation(row.supersedesCalculationId);if(old&&old.workflowStatus==='approved'){const oldBefore=clone(old);old.workflowStatus='superseded';old.supersededAt=now();old.supersededBy=id;old.updatedAt=now();old.updatedBy=actor()||null;history('calculation.superseded',old.id,oldBefore,old,{replacementCalculationId:id});}}return row;}
    function createNewRevision(id){const old=getCalculation(id);if(!old)throw new Error('Participação não encontrada');if(!['approved','superseded'].includes(old.workflowStatus))throw new Error('Nova revisão requer cálculo aprovado ou substituído');const result=recomputeCurrent(old),nextRevision=Math.max(old.revisionNumber+1,...data.calculations.filter((x)=>x.familyKey===old.familyKey&&x.periodStart===old.periodStart&&x.periodEnd===old.periodEnd).map((x)=>x.revisionNumber+1));const row=persistPreview(result,{revisionNumber:nextRevision,supersedesCalculationId:old.workflowStatus==='approved'?old.id:(old.supersededBy||old.id),metadata:{recalculatedFrom:old.id}});history('calculation.revision_created',row.id,null,row,{sourceCalculationId:old.id});return row;}

    function query(filters={}){if(filters.refreshConsistency)refreshAllConsistency();let rows=data.calculations.filter((row)=>filters.includeDemo?true:!row.isDemo);if(filters.workflowStatus)rows=rows.filter((r)=>r.workflowStatus===filters.workflowStatus);if(filters.calculationStatus)rows=rows.filter((r)=>r.calculationStatus===filters.calculationStatus);if(filters.consistencyStatus)rows=rows.filter((r)=>r.consistencyStatus===filters.consistencyStatus);if(filters.contractId)rows=rows.filter((r)=>r.contractId===filters.contractId);if(filters.participantPartyId)rows=rows.filter((r)=>r.participantPartyId===filters.participantPartyId);if(filters.productId)rows=rows.filter((r)=>r.productId===filters.productId);if(filters.serviceId)rows=rows.filter((r)=>r.serviceId===filters.serviceId);if(filters.businessUnitId)rows=rows.filter((r)=>r.businessUnitId===filters.businessUnitId);if(filters.basisType)rows=rows.filter((r)=>r.basisType===filters.basisType);if(filters.ruleType)rows=rows.filter((r)=>r.ruleType===filters.ruleType);if(filters.from)rows=rows.filter((r)=>r.periodEnd>=filters.from);if(filters.to)rows=rows.filter((r)=>r.periodStart<=filters.to);if(filters.search){const q=fold(filters.search);rows=rows.filter((r)=>fold([r.contractNumber,r.contractId,r.participantSnapshot?.name,r.participantSnapshot?.document,r.productId,r.serviceId,r.businessUnitId,r.periodStart,r.periodEnd,r.participationAmount,r.basisType,r.ruleType].join(' ')).includes(q));}rows.sort((a,b)=>String(b.periodEnd).localeCompare(String(a.periodEnd))||b.revisionNumber-a.revisionNumber);const total=rows.length,limit=Math.min(50,Math.max(1,Number(filters.limit)||50)),page=Math.max(1,Number(filters.page)||1);return {rows:clone(rows.slice((page-1)*limit,page*limit)),total,page,limit,pages:Math.max(1,Math.ceil(total/limit))};}
    function memory(id){const row=getCalculation(id);if(!row)throw new Error('Participação não encontrada');return {calculation:clone(row),segments:clone(getSegments(id)),baseComponents:clone(getBaseComponents(id)),deductions:clone(getDeductions(id)),sourceSnapshot:clone(getSourceSnapshot(id)),history:clone(data.history.filter((x)=>x.calculationId===id)),approvals:clone(data.approvals.filter((x)=>x.calculationId===id))};}
    function obligationsFeed(filters={}){let rows=data.calculations.filter((row)=>row.workflowStatus==='approved'&&row.consistencyStatus==='consistent'&&!row.isDemo);if(filters.contractId)rows=rows.filter((r)=>r.contractId===filters.contractId);if(filters.participantPartyId)rows=rows.filter((r)=>r.participantPartyId===filters.participantPartyId);if(filters.from)rows=rows.filter((r)=>r.periodEnd>=filters.from);if(filters.to)rows=rows.filter((r)=>r.periodStart<=filters.to);return clone(rows.map((row)=>({participationCalculationId:row.id,contractId:row.contractId,contractVersionId:row.contractVersionId,economicRuleId:row.economicRuleId,participantPartyType:row.participantPartyType,participantPartyId:row.participantPartyId,periodStart:row.periodStart,periodEnd:row.periodEnd,currency:row.currency,amountDue:row.participationAmount,productId:row.productId,serviceId:row.serviceId,businessUnitId:row.businessUnitId,approvedAt:row.approvedAt,dueDate:row.metadata?.dueDate||null,sourceSnapshotHash:row.sourceSnapshotHash})));}
    function migrateLegacy(records=[]){if(data.metadata.legacyReviewed)return {migrated:0,skipped:data.metadata.legacySkipped.length};let migrated=0;for(const item of records||[]){if(!item||typeof item!=='object')continue;const hasProof=item.contractId&&item.contractVersionId&&item.economicRuleId&&item.participantPartyId&&isoDate(item.periodStart)&&isoDate(item.periodEnd)&&BASIS_TYPES.includes(item.basisType);if(!hasProof){data.metadata.legacySkipped.push({sourceId:text(item.id),reason:'insufficient_contract_traceability'});continue;}data.metadata.legacySkipped.push({sourceId:text(item.id),reason:'legacy_requires_explicit_recalculation'});}data.metadata.legacyReviewed=true;data.metadata.legacyReviewedAt=now();return {migrated,skipped:data.metadata.legacySkipped.length};}

    return {data,getCalculation,getSegments,getBaseComponents,getDeductions,getSourceSnapshot,resolveSegments,preview,previewEligible,createCalculation,createBatch,submitToReview,reject,approve,createNewRevision,refreshConsistency,refreshAllConsistency,query,memory,obligationsFeed,migrateLegacy,ruleFamilyKey,ruleSnapshot,accountingFilters};
  }

  return {SCHEMA_VERSION,WORKFLOW_STATUSES,CALCULATION_STATUSES,CONSISTENCY_STATUSES,BASIS_TYPES,RULE_TYPES,PARTY_TYPES,createState,ensureState,createService,clone,text,fold,isoDate,toCents,fromCents,money,percent,dateSpan,deterministicHash,dimensionKey,ruleFamilyKey,permissionCode};
});