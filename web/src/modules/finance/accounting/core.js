(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.ValtrenAccountingCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const BASIS=['cash','accrual'];
  const PERIOD_STATUSES=['open','review','closed'];
  const REVERSAL_NATURES=['refund','reimbursement','reversal','chargeback'];
  const SECTION_ORDER=['gross_revenue','deductions','costs','operating_expenses','financial_result','other_results','result_taxes'];
  const SECTION_LABELS={
    gross_revenue:'Receita Bruta',
    deductions:'Deduções da Receita',
    costs:'Custos',
    operating_expenses:'Despesas Operacionais',
    financial_result:'Resultado Financeiro',
    other_results:'Outros Resultados',
    result_taxes:'Tributos sobre Resultado'
  };
  const DEFAULT_CLASSIFICATIONS=[
    ['revenue_products','3.1.01','Receita Operacional / Produtos','gross_revenue','',1,10],
    ['revenue_services','3.1.02','Receita Operacional / Serviços','gross_revenue','',1,20],
    ['deductions_taxes','3.2.01','Deduções / Tributos sobre Faturamento','deductions','',-1,30],
    ['deductions_returns','3.2.02','Deduções / Devoluções e Cancelamentos','deductions','',-1,40],
    ['deductions_discounts','3.2.03','Deduções / Abatimentos e Descontos','deductions','',-1,50],
    ['cost_direct','4.1.01','Custos / Custos Diretos','costs','',-1,60],
    ['cost_infrastructure','4.1.02','Custos / Infraestrutura Direta','costs','',-1,70],
    ['cost_third_parties','4.1.03','Custos / Terceiros Diretos','costs','',-1,80],
    ['opex_administrative','5.1.01','Despesas Operacionais / Administrativas','operating_expenses','',-1,90],
    ['opex_commercial','5.1.02','Despesas Operacionais / Comerciais','operating_expenses','',-1,100],
    ['opex_marketing','5.1.03','Despesas Operacionais / Marketing','operating_expenses','',-1,110],
    ['opex_people','5.1.04','Despesas Operacionais / Pessoal','operating_expenses','',-1,120],
    ['opex_technology','5.1.05','Despesas Operacionais / Tecnologia','operating_expenses','',-1,130],
    ['opex_legal','5.1.06','Despesas Operacionais / Jurídicas','operating_expenses','',-1,140],
    ['opex_other','5.1.99','Despesas Operacionais / Outras','operating_expenses','',-1,150],
    ['financial_income','6.1.01','Resultado Financeiro / Receitas Financeiras','financial_result','',1,160],
    ['financial_expense','6.1.02','Resultado Financeiro / Despesas Financeiras','financial_result','',-1,170],
    ['other_income','7.1.01','Outros Resultados / Receitas','other_results','',1,180],
    ['other_expense','7.1.02','Outros Resultados / Despesas','other_results','',-1,190],
    ['result_taxes','8.1.01','Tributos sobre Resultado','result_taxes','',-1,200]
  ];
  const DEFAULT_MAPPINGS=[
    ['revenue_services','revenue_services'],
    ['revenue_product','revenue_products'],
    ['marketing','opex_marketing'],
    ['marketing_paid','opex_marketing'],
    ['software','opex_technology'],
    ['payroll','opex_people'],
    ['bank_fees','financial_expense']
  ];

  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const num=(value)=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0;};
  const roundMoney=(value)=>Math.round((num(value)+Number.EPSILON)*100)/100;
  const iso=(value)=>/^\d{4}-\d{2}-\d{2}$/.test(String(value||''))?String(value):'';
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}
  function defaultClassifications(now){return DEFAULT_CLASSIFICATIONS.map(([id,code,name,section,parentId,sign,order])=>({id,code,name,section,parentId,sign,order,status:'active',system:true,createdAt:now(),updatedAt:now()}));}
  function defaultMappings(now){return DEFAULT_MAPPINGS.map(([categoryId,classificationId],index)=>({id:`amap_${categoryId}`,categoryId,classificationId,active:true,system:true,order:index+1,createdAt:now(),updatedAt:now()}));}
  function createState(options={}){const now=options.now||(()=>new Date().toISOString());return {schemaVersion:SCHEMA_VERSION,classifications:defaultClassifications(now),mappings:defaultMappings(now),transactionMeta:[],history:[],periods:[],metadata:{createdAt:now()}};}
  function ensureState(input,options={}){const data=input&&typeof input==='object'?input:createState(options),template=createState(options);for(const key of ['classifications','mappings','transactionMeta','history','periods'])if(!Array.isArray(data[key]))data[key]=[];if(!data.classifications.length)data.classifications=template.classifications;if(!data.mappings.length)data.mappings=template.mappings;if(!data.metadata||typeof data.metadata!=='object')data.metadata={};data.schemaVersion=SCHEMA_VERSION;return data;}

  function previousPeriod(from,to){
    if(!iso(from)||!iso(to)||from>to)return null;
    const start=new Date(`${from}T00:00:00Z`),end=new Date(`${to}T00:00:00Z`),span=Math.round((end-start)/86400000)+1;
    const prevEnd=new Date(start);prevEnd.setUTCDate(prevEnd.getUTCDate()-1);
    const prevStart=new Date(prevEnd);prevStart.setUTCDate(prevStart.getUTCDate()-span+1);
    return {from:prevStart.toISOString().slice(0,10),to:prevEnd.toISOString().slice(0,10)};
  }

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const data=ensureState(store,{now});
    const finance=()=>typeof options.financeService==='function'?options.financeService():options.financeService;
    const financeData=()=>{const service=finance();if(!service||!service.data||!Array.isArray(service.data.transactions))throw new Error('Fonte financeira canônica indisponível');return service.data;};
    const getTransaction=(id)=>{const service=finance();if(service&&typeof service.getTransaction==='function')return service.getTransaction(id);return financeData().transactions.find((row)=>row.id===id)||null;};
    const getCategory=(id)=>{const service=finance();if(service&&typeof service.getCategory==='function')return service.getCategory(id);return financeData().categories?.find((row)=>row.id===id)||null;};
    const getClassification=(id)=>data.classifications.find((row)=>row.id===id)||null;
    const getMapping=(categoryId)=>data.mappings.find((row)=>row.categoryId===categoryId&&row.active!==false)||null;
    const getTransactionMeta=(transactionId)=>data.transactionMeta.find((row)=>row.transactionId===transactionId)||null;
    const history=(action,transactionId,before,after,metadata={})=>{const row={id:idFactory('achist'),action,transactionId:transactionId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(row);return row;};

    function upsertClassification(input={}){
      const id=text(input.id)||idFactory('aclass'),existing=getClassification(id),before=clone(existing);
      const section=text(input.section||existing?.section);if(!SECTION_ORDER.includes(section))throw new Error('Grupo contábil inválido');
      const sign=Number(input.sign??existing?.sign);if(![-1,1].includes(sign))throw new Error('Natureza contábil inválida');
      const payload={id,code:text(input.code??existing?.code),name:text(input.name??existing?.name),section,parentId:text(input.parentId??existing?.parentId),sign,order:num(input.order??existing?.order??999),status:text(input.status??existing?.status??'active')||'active',system:existing?.system===true,createdAt:existing?.createdAt||now(),updatedAt:now()};
      if(!payload.name)throw new Error('Classificação contábil requer nome');
      if(payload.parentId&&!getClassification(payload.parentId))throw new Error('Classificação contábil pai não encontrada');
      if(existing)Object.assign(existing,payload);else data.classifications.push(payload);
      history('classification.changed','',before,payload,{classificationId:id});return payload;
    }

    function setMapping(categoryId,classificationId,active=true){
      if(!getCategory(categoryId))throw new Error('Categoria financeira não encontrada');
      if(classificationId&&!getClassification(classificationId))throw new Error('Classificação contábil não encontrada');
      let row=data.mappings.find((item)=>item.categoryId===categoryId)||null;const before=clone(row);
      if(!row){row={id:idFactory('amap'),categoryId,classificationId:text(classificationId),active:active!==false,system:false,createdAt:now(),updatedAt:now()};data.mappings.push(row);}else{row.classificationId=text(classificationId);row.active=active!==false;row.updatedAt=now();row.updatedBy=actor()||null;}
      history('mapping.changed','',before,row,{categoryId});return row;
    }

    function upsertPeriod(input={}){
      const periodId=text(input.id||input.period);if(!periodId)throw new Error('Período contábil requer identificador');
      const status=PERIOD_STATUSES.includes(input.status)?input.status:'open';let row=data.periods.find((item)=>item.id===periodId)||null;const before=clone(row);
      if(!row){row={id:periodId,status,label:text(input.label||periodId),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.periods.push(row);}else{row.status=status;if('label'in input)row.label=text(input.label);row.updatedAt=now();row.updatedBy=actor()||null;}
      history('period.changed','',before,row,{periodId});return row;
    }

    function setTransactionAccounting(transactionId,input={}){
      const tx=getTransaction(transactionId);if(!tx)throw new Error('Transação financeira não encontrada');
      let row=getTransactionMeta(transactionId),before=clone(row);
      if(!row){row={transactionId,recognitionDate:'',classificationId:'',serviceId:'',businessUnitId:'',createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.transactionMeta.push(row);}
      if('classificationId'in input){const classificationId=text(input.classificationId);if(classificationId&&!getClassification(classificationId))throw new Error('Classificação contábil não encontrada');row.classificationId=classificationId;}
      if('recognitionDate'in input){const value=text(input.recognitionDate);if(value&&!iso(value))throw new Error('Data de competência inválida');row.recognitionDate=value;}
      if('serviceId'in input)row.serviceId=text(input.serviceId);
      if('businessUnitId'in input)row.businessUnitId=text(input.businessUnitId);
      row.updatedAt=now();row.updatedBy=actor()||null;
      history('transaction.accounting.changed',transactionId,before,row,{source:'manual'});return row;
    }

    function resolveClassification(tx,seen=new Set()){
      if(!tx)return {classification:null,source:'unclassified'};
      const meta=getTransactionMeta(tx.id);if(meta?.classificationId){const classification=getClassification(meta.classificationId);if(classification&&classification.status!=='inactive')return {classification,source:'override'};}
      const mapping=getMapping(tx.categoryId);if(mapping?.classificationId){const classification=getClassification(mapping.classificationId);if(classification&&classification.status!=='inactive')return {classification,source:'mapping'};}
      if(REVERSAL_NATURES.includes(tx.financialNature)&&tx.relatedTransactionId&&!seen.has(tx.id)){
        seen.add(tx.id);const original=getTransaction(tx.relatedTransactionId),resolved=resolveClassification(original,seen);if(resolved.classification)return {classification:resolved.classification,source:'related'};
      }
      return {classification:null,source:'unclassified'};
    }

    function resolveDate(tx,basis='accrual'){
      if(basis==='cash')return iso(tx.settlementDate)||iso(tx.transactionDate)||iso(String(tx.postedAt||'').slice(0,10));
      const meta=getTransactionMeta(tx.id),fromTx=tx.metadata?.recognitionDate||tx.metadata?.competenceDate||'';
      return iso(meta?.recognitionDate)||iso(fromTx);
    }

    function dimensionAmount(tx,filters={}){
      const dimension=filters.dimension||'',productId=filters.productId||'';
      if(!dimension&&!productId)return roundMoney(tx.amount);
      const allocations=Array.isArray(tx.allocations)?tx.allocations:[];
      if(allocations.length){
        const amount=allocations.reduce((sum,item)=>{
          const matches=dimension==='corporate'?item.dimension==='corporate':productId?item.dimension==='product'&&item.productId===productId:false;
          if(!matches)return sum;
          if(item.amount!=null)return sum+num(item.amount);
          if(item.percentage!=null)return sum+(num(tx.amount)*num(item.percentage)/100);
          return sum;
        },0);
        return roundMoney(amount);
      }
      if(dimension==='corporate')return tx.businessDimension==='corporate'?roundMoney(tx.amount):0;
      if(productId)return tx.businessDimension==='product'&&tx.productId===productId?roundMoney(tx.amount):0;
      return roundMoney(tx.amount);
    }

    function accountingIssues(tx,basis='accrual'){
      if(!tx||tx.status!=='posted'||tx.isDemo||tx.financialNature==='transfer')return [];
      const issues=[],resolved=resolveClassification(tx),meta=getTransactionMeta(tx.id);
      if(!resolved.classification)issues.push('unclassified');
      if(basis==='accrual'&&!resolveDate(tx,'accrual'))issues.push('missing_competence');
      if(tx.businessDimension==='product'&&!tx.productId)issues.push('missing_product_reference');
      if((tx.allocations||[]).some((item)=>item.dimension==='product'&&!item.productId))issues.push('invalid_allocation_reference');
      if(meta?.classificationId&&!getClassification(meta.classificationId))issues.push('invalid_classification_reference');
      return issues;
    }

    function transactionContribution(tx,classification,amount){
      if(!classification||tx.financialNature==='transfer')return 0;
      if(REVERSAL_NATURES.includes(tx.financialNature)&&tx.relatedTransactionId){
        const original=getTransaction(tx.relatedTransactionId),resolved=resolveClassification(original);
        if(original&&resolved.classification)return roundMoney(amount*(-resolved.classification.sign));
      }
      return roundMoney(amount*classification.sign);
    }

    function baseTransactions(){return financeData().transactions.filter((tx)=>tx&&tx.status==='posted'&&!tx.isDemo&&tx.financialNature!=='transfer');}

    function rowFor(tx,filters={},includeUndated=false){
      const basis=BASIS.includes(filters.basis)?filters.basis:'accrual',resolved=resolveClassification(tx),date=resolveDate(tx,basis),meta=getTransactionMeta(tx.id)||{transactionId:tx.id,recognitionDate:'',classificationId:'',serviceId:'',businessUnitId:''};
      if(!resolved.classification)return null;
      if(!date&&!includeUndated)return null;
      if(date&&filters.from&&date<filters.from)return null;if(date&&filters.to&&date>filters.to)return null;
      if(filters.categoryId&&tx.categoryId!==filters.categoryId)return null;
      if(filters.classificationId&&resolved.classification.id!==filters.classificationId&&resolved.classification.section!==filters.classificationId)return null;
      if(filters.serviceId&&meta.serviceId!==filters.serviceId)return null;
      if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId)return null;
      const amount=dimensionAmount(tx,filters);if(!(amount>0))return null;
      const contribution=transactionContribution(tx,resolved.classification,amount);
      return {transaction:tx,accounting:meta,classification:resolved.classification,classificationSource:resolved.source,date,amount,contribution,issues:accountingIssues(tx,basis)};
    }

    function analyze(filters={}){const rows=[];for(const tx of baseTransactions()){const row=rowFor(tx,filters,false);if(row)rows.push(row);}return rows;}

    function listEntries(filters={}){
      const basis=BASIS.includes(filters.basis)?filters.basis:'accrual',rows=[];
      for(const tx of baseTransactions()){
        const resolved=resolveClassification(tx),date=resolveDate(tx,basis),meta=getTransactionMeta(tx.id)||{transactionId:tx.id,recognitionDate:'',classificationId:'',serviceId:'',businessUnitId:''};
        if(filters.categoryId&&tx.categoryId!==filters.categoryId)continue;
        if(filters.classificationId&&resolved.classification?.id!==filters.classificationId&&resolved.classification?.section!==filters.classificationId)continue;
        if(filters.serviceId&&meta.serviceId!==filters.serviceId)continue;
        if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId)continue;
        const amount=dimensionAmount(tx,filters);if(!(amount>0))continue;
        const undated=!date;if(!undated&&filters.from&&date<filters.from)continue;if(!undated&&filters.to&&date>filters.to)continue;
        const issues=accountingIssues(tx,basis);if(filters.onlyPending&&issues.length===0)continue;
        rows.push({transaction:tx,accounting:meta,classification:resolved.classification,classificationSource:resolved.source,date,amount,contribution:resolved.classification?transactionContribution(tx,resolved.classification,amount):0,issues});
      }
      rows.sort((a,b)=>String(b.date||b.transaction.transactionDate||'').localeCompare(String(a.date||a.transaction.transactionDate||''))||String(b.transaction.createdAt||'').localeCompare(String(a.transaction.createdAt||'')));
      return rows;
    }

    function pendencies(filters={}){
      const basis=BASIS.includes(filters.basis)?filters.basis:'accrual',rows=listEntries({...filters,from:'',to:''}),counts={unclassified:0,missing_competence:0,missing_product_reference:0,invalid_allocation_reference:0,invalid_classification_reference:0,total:0};
      const pending=[];for(const row of rows){const issues=accountingIssues(row.transaction,basis);if(!issues.length)continue;pending.push({...row,issues});for(const issue of issues)counts[issue]=(counts[issue]||0)+1;}counts.total=pending.length;return {counts,rows:pending};
    }

    function buildDre(filters={}){
      const rows=analyze(filters),sectionTotals=Object.fromEntries(SECTION_ORDER.map((id)=>[id,0])),breakdown={};
      for(const row of rows){sectionTotals[row.classification.section]=roundMoney(sectionTotals[row.classification.section]+row.contribution);const id=row.classification.id;if(!breakdown[id])breakdown[id]={classification:row.classification,contribution:0,count:0};breakdown[id].contribution=roundMoney(breakdown[id].contribution+row.contribution);breakdown[id].count++;}
      const grossRevenue=roundMoney(sectionTotals.gross_revenue),deductions=roundMoney(-sectionTotals.deductions),netRevenue=roundMoney(grossRevenue-deductions),costs=roundMoney(-sectionTotals.costs),grossResult=roundMoney(netRevenue-costs),operatingExpenses=roundMoney(-sectionTotals.operating_expenses),operatingResult=roundMoney(grossResult-operatingExpenses),financialResult=roundMoney(sectionTotals.financial_result),otherResults=roundMoney(sectionTotals.other_results),preTaxResult=roundMoney(operatingResult+financialResult+otherResults),resultTaxes=roundMoney(-sectionTotals.result_taxes),finalResult=roundMoney(preTaxResult-resultTaxes);
      const grossMargin=netRevenue===0?null:(grossResult/netRevenue)*100,operatingMargin=netRevenue===0?null:(operatingResult/netRevenue)*100,finalMargin=netRevenue===0?null:(finalResult/netRevenue)*100;
      const sectionBreakdown={};for(const section of SECTION_ORDER){sectionBreakdown[section]=Object.values(breakdown).filter((item)=>item.classification.section===section).sort((a,b)=>a.classification.order-b.classification.order).map((item)=>({...item,displayAmount:['deductions','costs','operating_expenses','result_taxes'].includes(section)?roundMoney(-item.contribution):item.contribution}));}
      return {filters:{...filters,basis:BASIS.includes(filters.basis)?filters.basis:'accrual'},rows,rowCount:rows.length,sectionTotals,breakdown:sectionBreakdown,summary:{grossRevenue,deductions,netRevenue,costs,grossResult,operatingExpenses,operatingResult,financialResult,otherResults,preTaxResult,resultTaxes,finalResult,grossMargin,operatingMargin,finalMargin}};
    }

    function drillDown(target,filters={}){
      const rows=analyze(filters),sectionSets={gross_revenue:['gross_revenue'],deductions:['deductions'],net_revenue:['gross_revenue','deductions'],costs:['costs'],gross_result:['gross_revenue','deductions','costs'],operating_expenses:['operating_expenses'],operating_result:['gross_revenue','deductions','costs','operating_expenses'],financial_result:['financial_result'],other_results:['other_results'],pretax_result:['gross_revenue','deductions','costs','operating_expenses','financial_result','other_results'],result_taxes:['result_taxes'],final_result:SECTION_ORDER};
      let selected;if(sectionSets[target])selected=rows.filter((row)=>sectionSets[target].includes(row.classification.section));else selected=rows.filter((row)=>row.classification.id===target);
      const signedTotal=roundMoney(selected.reduce((sum,row)=>sum+row.contribution,0));
      const positiveDisplay=['deductions','costs','operating_expenses','result_taxes'].includes(target)||selected.length&&selected.every((row)=>['deductions','costs','operating_expenses','result_taxes'].includes(row.classification.section));
      return {target,rows:selected,signedTotal,displayTotal:positiveDisplay?roundMoney(-signedTotal):signedTotal};
    }

    return {data,getClassification,getMapping,getTransactionMeta,upsertClassification,setMapping,upsertPeriod,setTransactionAccounting,resolveClassification,resolveDate,dimensionAmount,accountingIssues,transactionContribution,analyze,listEntries,pendencies,buildDre,drillDown,history,previousPeriod};
  }

  return {SCHEMA_VERSION,BASIS,PERIOD_STATUSES,REVERSAL_NATURES,SECTION_ORDER,SECTION_LABELS,DEFAULT_CLASSIFICATIONS,DEFAULT_MAPPINGS,createState,ensureState,createService,previousPeriod,roundMoney,iso,text};
});