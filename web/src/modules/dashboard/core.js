(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenDashboardCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const MONEY_SECTIONS=['gross_revenue','deductions','costs','operating_expenses'];
  const DIMENSION_KINDS=['product','service','business_unit','corporate','unassigned'];
  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const num=(value)=>{const n=Number(value);return Number.isFinite(n)?n:0;};
  const roundMoney=(value)=>Math.round((num(value)+Number.EPSILON)*100)/100;
  const sum=(rows,selector)=>roundMoney((rows||[]).reduce((total,row)=>total+num(selector(row)),0));
  const percent=(value,base)=>{const denominator=num(base);if(Math.abs(denominator)<0.005)return null;return Math.round((num(value)/denominator*100+Number.EPSILON)*100)/100;};
  const safeDate=(value)=>/^\d{4}-\d{2}-\d{2}$/.test(text(value))?text(value):'';
  const monthKey=(value)=>safeDate(value).slice(0,7);
  const dimensionKey=(kind,id='')=>`${kind}:${id||kind}`;

  function normalizeCatalog(input={}){
    const clean=(rows)=>Array.isArray(rows)?rows.filter((row)=>row&&!row.isDemo&&row.id).map(clone):[];
    return {products:clean(input.products),services:clean(input.services),businessUnits:clean(input.businessUnits)};
  }

  function findCatalogEntity(catalog,kind,id){
    const source=kind==='product'?catalog.products:kind==='service'?catalog.services:kind==='business_unit'?catalog.businessUnits:[];
    return source.find((row)=>String(row.id)===String(id))||null;
  }

  function dimensionDescriptor(catalog,kind,id=''){
    if(kind==='corporate')return {key:dimensionKey('corporate'),kind:'corporate',id:'corporate',name:'Corporativo',type:'Corporativo',businessUnitId:'',resolved:true};
    if(kind==='unassigned')return {key:dimensionKey('unassigned'),kind:'unassigned',id:'unassigned',name:'Não classificado',type:'Não classificado',businessUnitId:'',resolved:false};
    const entity=findCatalogEntity(catalog,kind,id);
    if(!entity)return {key:dimensionKey(kind,id),kind,id:String(id||''),name:id?`Referência não resolvida · ${id}`:'Não classificado',type:kind==='product'?'Produto':kind==='service'?'Serviço':'Unidade de Negócio',businessUnitId:'',resolved:false};
    const productType=fold(entity.type).includes('saas')?'SaaS':'Produto';
    return {key:dimensionKey(kind,id),kind,id:String(id),name:text(entity.name||entity.title||entity.code||id),type:kind==='product'?productType:kind==='service'?'Serviço':'Unidade de Negócio',businessUnitId:text(entity.businessUnitId),resolved:true,entity:clone(entity)};
  }

  function primaryDimension(row,catalog){
    const tx=row?.transaction||{},accounting=row?.accounting||{};
    const refs=[
      tx.productId?['product',tx.productId]:null,
      accounting.serviceId?['service',accounting.serviceId]:null,
      accounting.businessUnitId?['business_unit',accounting.businessUnitId]:null,
      tx.businessDimension==='corporate'?['corporate','corporate']:null
    ].filter(Boolean);
    const selected=refs[0]||['unassigned','unassigned'];
    return {...dimensionDescriptor(catalog,selected[0],selected[1]),conflictingReferences:refs.length>1};
  }

  function allocationSlices(row,catalog){
    const tx=row?.transaction||{},allocations=Array.isArray(tx.allocations)?tx.allocations:[];
    if(!allocations.length)return [{descriptor:primaryDimension(row,catalog),ratio:1,amount:roundMoney(row?.amount),contribution:roundMoney(row?.contribution),source:'primary'}];
    const txAmount=Math.abs(num(tx.amount));
    if(!(txAmount>0))return [{descriptor:dimensionDescriptor(catalog,'unassigned','unassigned'),ratio:1,amount:roundMoney(row?.amount),contribution:roundMoney(row?.contribution),source:'invalid_allocation'}];
    const slices=[];
    for(const item of allocations){
      let ratio=null;
      if(item.percentage!=null&&item.percentage!=='')ratio=num(item.percentage)/100;
      else if(item.amount!=null&&item.amount!=='')ratio=Math.abs(num(item.amount))/txAmount;
      if(!(ratio>0))continue;
      const kind=item.dimension==='corporate'?'corporate':'product';
      const id=kind==='corporate'?'corporate':text(item.productId);
      slices.push({descriptor:dimensionDescriptor(catalog,id?kind:'unassigned',id||'unassigned'),ratio,amount:roundMoney(num(row?.amount)*ratio),contribution:roundMoney(num(row?.contribution)*ratio),source:'allocation'});
    }
    const ratioTotal=slices.reduce((total,item)=>total+item.ratio,0);
    if(!slices.length||Math.abs(ratioTotal-1)>0.005)return [{descriptor:dimensionDescriptor(catalog,'unassigned','unassigned'),ratio:1,amount:roundMoney(row?.amount),contribution:roundMoney(row?.contribution),source:'invalid_allocation'}];
    return slices;
  }

  function emptyUnit(descriptor){
    return {...descriptor,grossRevenue:0,deductions:0,netRevenue:0,directCosts:0,operatingExpenses:0,operatingResult:0,operatingMargin:null,thirdPartyParticipation:0,valtrenResult:0,rowCount:0,issues:[]};
  }

  function applyAccountingContribution(unit,row,contribution){
    const section=row?.classification?.section||'';
    if(section==='gross_revenue')unit.grossRevenue=roundMoney(unit.grossRevenue+Math.max(0,num(contribution)));
    else if(section==='deductions')unit.deductions=roundMoney(unit.deductions+Math.abs(num(contribution)));
    else if(section==='costs')unit.directCosts=roundMoney(unit.directCosts+Math.abs(num(contribution)));
    else if(section==='operating_expenses')unit.operatingExpenses=roundMoney(unit.operatingExpenses+Math.abs(num(contribution)));
    unit.rowCount++;
  }

  function participationDimension(row,catalog){
    if(row?.productId)return dimensionDescriptor(catalog,'product',row.productId);
    if(row?.serviceId)return dimensionDescriptor(catalog,'service',row.serviceId);
    if(row?.businessUnitId)return dimensionDescriptor(catalog,'business_unit',row.businessUnitId);
    return dimensionDescriptor(catalog,'unassigned','unassigned');
  }

  function finalizeUnit(unit){
    unit.netRevenue=roundMoney(unit.grossRevenue-unit.deductions);
    unit.operatingResult=roundMoney(unit.netRevenue-unit.directCosts-unit.operatingExpenses);
    unit.operatingMargin=percent(unit.operatingResult,unit.netRevenue);
    unit.valtrenResult=roundMoney(unit.operatingResult-unit.thirdPartyParticipation);
    return unit;
  }

  function buildUnitPerformance(accountingRows=[],participations=[],catalogInput={}){
    const catalog=normalizeCatalog(catalogInput),map=new Map(),issues=[];
    const ensure=(descriptor)=>{if(!map.has(descriptor.key))map.set(descriptor.key,emptyUnit(descriptor));return map.get(descriptor.key);};
    for(const row of accountingRows||[]){
      if(!row||!MONEY_SECTIONS.includes(row.classification?.section))continue;
      for(const slice of allocationSlices(row,catalog)){
        const unit=ensure(slice.descriptor);applyAccountingContribution(unit,row,slice.contribution);
        if(slice.source==='invalid_allocation')unit.issues.push('allocation_incomplete');
        if(slice.descriptor.conflictingReferences)unit.issues.push('conflicting_dimension');
        if(!slice.descriptor.resolved&&slice.descriptor.kind!=='corporate')unit.issues.push('unresolved_dimension');
      }
    }
    for(const participation of participations||[]){
      if(!participation||participation.isDemo)continue;
      const descriptor=participationDimension(participation,catalog),unit=ensure(descriptor);
      unit.thirdPartyParticipation=roundMoney(unit.thirdPartyParticipation+Math.max(0,num(participation.participationAmount??participation.amountDue)));
      if(!descriptor.resolved)unit.issues.push('unresolved_participation_dimension');
    }
    const rows=[...map.values()].map((unit)=>{unit.issues=[...new Set(unit.issues)];return finalizeUnit(unit);}).filter((unit)=>unit.rowCount||unit.thirdPartyParticipation);
    for(const unit of rows)for(const issue of unit.issues)issues.push({unitKey:unit.key,issue});
    rows.sort((a,b)=>b.valtrenResult-a.valtrenResult||b.grossRevenue-a.grossRevenue||a.name.localeCompare(b.name,'pt-BR'));
    return {rows,issues,catalog};
  }

  function consolidatedFromDre(dreSummary={},participations=[]){
    const grossRevenue=roundMoney(dreSummary.grossRevenue),deductions=roundMoney(dreSummary.deductions),netRevenue=roundMoney(dreSummary.netRevenue),directCosts=roundMoney(dreSummary.costs),operatingExpenses=roundMoney(dreSummary.operatingExpenses),operatingResult=roundMoney(dreSummary.operatingResult);
    const thirdPartyParticipation=sum((participations||[]).filter((row)=>!row?.isDemo),(row)=>Math.max(0,num(row.participationAmount??row.amountDue)));
    return {grossRevenue,deductions,netRevenue,directCosts,operatingExpenses,operatingResult,thirdPartyParticipation,valtrenResult:roundMoney(operatingResult-thirdPartyParticipation),operatingMargin:percent(operatingResult,netRevenue)};
  }

  function comparison(current,previous){
    const result={};
    for(const key of ['grossRevenue','deductions','netRevenue','directCosts','operatingExpenses','operatingResult','thirdPartyParticipation','valtrenResult']){
      const prev=num(previous?.[key]),cur=num(current?.[key]);result[key]=Math.abs(prev)<0.005?null:Math.round(((cur-prev)/Math.abs(prev)*100+Number.EPSILON)*100)/100;
    }
    return result;
  }

  function bridge(consolidated){
    return [
      {id:'grossRevenue',label:'Faturamento Bruto',kind:'total',value:consolidated.grossRevenue},
      {id:'deductions',label:'Deduções e Impostos',kind:'subtract',value:consolidated.deductions},
      {id:'netRevenue',label:'Receita Líquida',kind:'subtotal',value:consolidated.netRevenue},
      {id:'directCosts',label:'Custos Diretos',kind:'subtract',value:consolidated.directCosts},
      {id:'operatingExpenses',label:'Despesas Operacionais',kind:'subtract',value:consolidated.operatingExpenses},
      {id:'operatingResult',label:'Resultado Operacional',kind:'subtotal',value:consolidated.operatingResult},
      {id:'thirdPartyParticipation',label:'Participações / Repasses',kind:'subtract',value:consolidated.thirdPartyParticipation},
      {id:'valtrenResult',label:'Resultado Valtren',kind:'result',value:consolidated.valtrenResult}
    ];
  }

  function groupSummary(units,kind,grossTotal){
    const selected=units.filter((row)=>row.kind===kind),aggregate={kind,label:kind==='product'?'Produtos':'Serviços',grossRevenue:sum(selected,(row)=>row.grossRevenue),deductions:sum(selected,(row)=>row.deductions),netRevenue:sum(selected,(row)=>row.netRevenue),directCosts:sum(selected,(row)=>row.directCosts),operatingExpenses:sum(selected,(row)=>row.operatingExpenses),operatingResult:sum(selected,(row)=>row.operatingResult),thirdPartyParticipation:sum(selected,(row)=>row.thirdPartyParticipation),valtrenResult:sum(selected,(row)=>row.valtrenResult)};
    aggregate.revenueShare=percent(aggregate.grossRevenue,grossTotal);aggregate.valtrenResultShare=null;return aggregate;
  }

  function buildProductsVsServices(units,consolidated){
    const products=groupSummary(units,'product',consolidated.grossRevenue),services=groupSummary(units,'service',consolidated.grossRevenue),knownValtren=roundMoney(products.valtrenResult+services.valtrenResult);
    products.valtrenResultShare=percent(products.valtrenResult,consolidated.valtrenResult);services.valtrenResultShare=percent(services.valtrenResult,consolidated.valtrenResult);
    return {products,services,unattributedRevenue:roundMoney(consolidated.grossRevenue-products.grossRevenue-services.grossRevenue),unattributedValtrenResult:roundMoney(consolidated.valtrenResult-knownValtren)};
  }

  function buildTrend(accountingRows=[],participations=[]){
    const map=new Map();
    const ensure=(month)=>{if(!map.has(month))map.set(month,{month,grossRevenue:0,deductions:0,netRevenue:0,directCosts:0,operatingExpenses:0,operatingResult:0,thirdPartyParticipation:0,valtrenResult:0});return map.get(month);};
    for(const row of accountingRows||[]){const month=monthKey(row?.date);if(!month)continue;const target=ensure(month),section=row?.classification?.section,contribution=num(row?.contribution);if(section==='gross_revenue')target.grossRevenue=roundMoney(target.grossRevenue+Math.max(0,contribution));else if(section==='deductions')target.deductions=roundMoney(target.deductions+Math.abs(contribution));else if(section==='costs')target.directCosts=roundMoney(target.directCosts+Math.abs(contribution));else if(section==='operating_expenses')target.operatingExpenses=roundMoney(target.operatingExpenses+Math.abs(contribution));}
    for(const row of participations||[]){const month=monthKey(row?.periodEnd||row?.approvedAt?.slice?.(0,10));if(!month)continue;const target=ensure(month);target.thirdPartyParticipation=roundMoney(target.thirdPartyParticipation+Math.max(0,num(row.participationAmount??row.amountDue)));}
    const rows=[...map.values()].sort((a,b)=>a.month.localeCompare(b.month));
    for(const row of rows){row.netRevenue=roundMoney(row.grossRevenue-row.deductions);row.operatingResult=roundMoney(row.netRevenue-row.directCosts-row.operatingExpenses);row.valtrenResult=roundMoney(row.operatingResult-row.thirdPartyParticipation);}
    return rows;
  }

  function dueDateForDocument(doc){return safeDate(doc?.dueDate||doc?.paymentDueDate||doc?.metadata?.dueDate||doc?.metadata?.paymentDueDate);}
  function eligibleFiscalDocument(doc){return !!doc&&!doc.isDemo&&!['draft','cancelled','rejected','archived'].includes(doc.status);}
  function buildFiscalSummary(documents=[],settlementProvider=()=>null,today=''){
    const current=safeDate(today)||new Date().toISOString().slice(0,10),outgoing=[],incoming=[];
    for(const doc of documents||[]){if(!eligibleFiscalDocument(doc))continue;const settlement=settlementProvider(doc.id)||{},net=Math.max(0,num(doc.netAmount??doc.totalAmount)),received=Math.max(0,num(settlement.settledAmount)),open=Math.max(0,num(settlement.balance??(net-received))),due=dueDateForDocument(doc),row={id:doc.id,direction:doc.direction,netAmount:roundMoney(net),settledAmount:roundMoney(received),openBalance:roundMoney(open),dueDate:due,overdue:!!due&&due<current&&open>0,status:doc.status,financialStatus:settlement.status||'unlinked'};(doc.direction==='outgoing'?outgoing:incoming).push(row);}
    const billed=sum(outgoing,(row)=>row.netAmount),received=sum(outgoing,(row)=>row.settledAmount),openReceivable=sum(outgoing,(row)=>row.openBalance),overdueReceivable=sum(outgoing.filter((row)=>row.overdue),(row)=>row.openBalance),payable=sum(incoming,(row)=>row.openBalance),overduePayable=sum(incoming.filter((row)=>row.overdue),(row)=>row.openBalance);
    return {billed,received,open:openReceivable,receivedPercent:percent(received,billed),overdue:overdueReceivable,totalReceivable:openReceivable,overdueReceivable,totalPayable:payable,overduePayable,outgoingCount:outgoing.length,incomingCount:incoming.length,hasDueDates:[...outgoing,...incoming].some((row)=>row.dueDate)};
  }

  function buildParticipationSummary(participations=[],payoutObligations=[]){
    const eligible=(participations||[]).filter((row)=>row&&!row.isDemo),totalResult=sum(eligible,(row)=>row.distributableBase??row.calculationBase??0),thirdParty=sum(eligible,(row)=>row.participationAmount??row.amountDue??0),valtren=roundMoney(totalResult-thirdParty);
    const obligations=(payoutObligations||[]).filter((row)=>row&&!row.isDemo),repassed=sum(obligations,(row)=>row.amountPaid),pending=sum(obligations.filter((row)=>!['paid','cancelled','superseded'].includes(row.status)),(row)=>row.openBalance),overdue=sum(obligations.filter((row)=>row.status==='overdue'),(row)=>row.openBalance),scheduled=sum(obligations.filter((row)=>row.status==='open'&&row.dueDate),(row)=>row.openBalance);
    return {totalResult,valtren,thirdParty,repassed,pending,scheduled,overdue,obligations:clone(obligations)};
  }

  function buildParticipationTable(participations=[],payoutObligations=[],catalogInput={}){
    const catalog=normalizeCatalog(catalogInput),obligationByCalculation=new Map();
    for(const obligation of payoutObligations||[]){const key=obligation.participationCalculationId;if(!key)continue;if(!obligationByCalculation.has(key))obligationByCalculation.set(key,[]);obligationByCalculation.get(key).push(obligation);}
    return (participations||[]).filter((row)=>row&&!row.isDemo).map((row)=>{const descriptor=participationDimension(row,catalog),base=Math.max(0,num(row.distributableBase??row.calculationBase)),thirdParty=Math.max(0,num(row.participationAmount??row.amountDue)),valtren=Math.max(0,roundMoney(base-thirdParty)),thirdPartyPercent=percent(thirdParty,base),obligations=obligationByCalculation.get(row.id)||[],repassed=sum(obligations,(item)=>item.amountPaid),pending=sum(obligations.filter((item)=>!['paid','cancelled','superseded'].includes(item.status)),(item)=>item.openBalance);return {calculationId:row.id,descriptor,result:roundMoney(base),valtrenPercent:thirdPartyPercent==null?null:roundMoney(100-thirdPartyPercent),valtrenValue:valtren,thirdPartyPercent,thirdPartyValue:roundMoney(thirdParty),repassed,pending};}).sort((a,b)=>b.thirdPartyValue-a.thirdPartyValue||a.descriptor.name.localeCompare(b.descriptor.name,'pt-BR'));
  }

  function buildDeductionBreakdown(dre={}){
    const rows=Array.isArray(dre?.breakdown?.deductions)?dre.breakdown.deductions:[],gross=num(dre?.summary?.grossRevenue);
    return rows.map((row)=>({id:row.classification?.id||'',name:row.classification?.name||'Dedução',value:Math.max(0,num(row.displayAmount)),shareOfGross:percent(Math.max(0,num(row.displayAmount)),gross),count:num(row.count)})).filter((row)=>row.value>0).sort((a,b)=>b.value-a.value);
  }

  function buildCostStructure(accountingRows=[],catalogInput={}){
    const catalog=normalizeCatalog(catalogInput),attributed={costs:0,operatingExpenses:0,rows:[]},corporate={costs:0,operatingExpenses:0,rows:[]},unassigned={costs:0,operatingExpenses:0,rows:[]};
    for(const row of accountingRows||[]){const section=row?.classification?.section;if(!['costs','operating_expenses'].includes(section))continue;for(const slice of allocationSlices(row,catalog)){const bucket=slice.descriptor.kind==='corporate'?corporate:slice.descriptor.kind==='unassigned'?unassigned:attributed,value=Math.abs(num(slice.contribution));if(section==='costs')bucket.costs=roundMoney(bucket.costs+value);else bucket.operatingExpenses=roundMoney(bucket.operatingExpenses+value);bucket.rows.push({name:row.classification?.name||section,value:roundMoney(value),dimension:slice.descriptor});}}
    const summarize=(bucket)=>({...bucket,total:roundMoney(bucket.costs+bucket.operatingExpenses)});return {attributed:summarize(attributed),corporate:summarize(corporate),unassigned:summarize(unassigned),allocationModes:['not_allocated','equal','revenue_based','manual_percentage','future_rule']};
  }

  function rankingItem(label,row,value,format='money'){return row?{label,unitKey:row.key,unitName:row.name,value,format}:null;}
  function buildRankings(units=[],previousUnits=[]){
    const economic=units.filter((row)=>row.kind!=='unassigned'&&(row.grossRevenue||row.netRevenue||row.directCosts||row.operatingExpenses||row.operatingResult||row.thirdPartyParticipation)),by=(selector,order=-1)=>economic.slice().sort((a,b)=>order*(selector(a)-selector(b)))[0]||null;
    const items=[rankingItem('Maior faturamento',by((x)=>x.grossRevenue),by((x)=>x.grossRevenue)?.grossRevenue),rankingItem('Maior resultado operacional',by((x)=>x.operatingResult),by((x)=>x.operatingResult)?.operatingResult),rankingItem('Maior Resultado Valtren',by((x)=>x.valtrenResult),by((x)=>x.valtrenResult)?.valtrenResult),rankingItem('Maior margem',by((x)=>x.operatingMargin==null?-Infinity:x.operatingMargin),by((x)=>x.operatingMargin==null?-Infinity:x.operatingMargin)?.operatingMargin,'percent'),rankingItem('Maior custo',by((x)=>x.directCosts+x.operatingExpenses),by((x)=>x.directCosts+x.operatingExpenses)?roundMoney(by((x)=>x.directCosts+x.operatingExpenses).directCosts+by((x)=>x.directCosts+x.operatingExpenses).operatingExpenses):null)].filter((item)=>item&&Number.isFinite(item.value));
    const previous=new Map((previousUnits||[]).map((row)=>[row.key,row]));const comparable=economic.map((row)=>{const prev=previous.get(row.key);if(!prev)return null;const growth=percent(row.valtrenResult-prev.valtrenResult,Math.abs(prev.valtrenResult)),marginDelta=row.operatingMargin==null||prev.operatingMargin==null?null:roundMoney(row.operatingMargin-prev.operatingMargin);return {row,growth,marginDelta};}).filter(Boolean);
    if(comparable.some((x)=>x.growth!=null)){const growth=comparable.filter((x)=>x.growth!=null).sort((a,b)=>b.growth-a.growth)[0];items.push(rankingItem('Maior crescimento',growth.row,growth.growth,'percent'));}
    if(comparable.some((x)=>x.marginDelta!=null)){const drop=comparable.filter((x)=>x.marginDelta!=null).sort((a,b)=>a.marginDelta-b.marginDelta)[0];if(drop.marginDelta<0)items.push(rankingItem('Maior redução de margem',drop.row,drop.marginDelta,'percentage_points'));}
    return items;
  }

  function buildDashboard(input={}){
    const dre=input.dre||{summary:{},breakdown:{}},previousDre=input.previousDre||null,catalog=normalizeCatalog(input.catalog||{}),participations=Array.isArray(input.participations)?input.participations:[],previousParticipations=Array.isArray(input.previousParticipations)?input.previousParticipations:[],accountingRows=Array.isArray(input.accountingRows)?input.accountingRows:[],previousAccountingRows=Array.isArray(input.previousAccountingRows)?input.previousAccountingRows:[];
    const unitResult=buildUnitPerformance(accountingRows,participations,catalog),previousUnitResult=buildUnitPerformance(previousAccountingRows,previousParticipations,catalog),consolidated=consolidatedFromDre(dre.summary||{},participations),previous=previousDre?consolidatedFromDre(previousDre.summary||{},previousParticipations):null;
    const snapshot={company:{legalEntity:'Valtren Solutions',dimensionModel:'single_legal_entity_with_internal_business_dimensions'},consolidated,comparison:previous?comparison(consolidated,previous):{},bridge:bridge(consolidated),units:unitResult.rows,unitIssues:unitResult.issues,productsVsServices:buildProductsVsServices(unitResult.rows,consolidated),trend:buildTrend(accountingRows,participations),participations:buildParticipationSummary(participations,input.payoutObligations||[]),participationTable:buildParticipationTable(participations,input.payoutObligations||[],catalog),fiscal:buildFiscalSummary(input.fiscalDocuments||[],input.settlementProvider||(()=>null),input.today),deductions:buildDeductionBreakdown(dre),costStructure:buildCostStructure(accountingRows,catalog),rankings:buildRankings(unitResult.rows,previousUnitResult.rows),warnings:[]};
    if(input.accountingPendingCount)snapshot.warnings.push({code:'accounting_pending',message:`${input.accountingPendingCount} lançamento(s) possuem pendências contábeis e podem não estar refletidos integralmente.`});
    if(unitResult.issues.length)snapshot.warnings.push({code:'dimension_quality',message:'Existem lançamentos com dimensão gerencial incompleta, conflitante ou não resolvida.'});
    if(!snapshot.fiscal.hasDueDates&&(snapshot.fiscal.totalReceivable>0||snapshot.fiscal.totalPayable>0))snapshot.warnings.push({code:'missing_due_dates',message:'Há saldos fiscais em aberto sem datas de vencimento suficientes para consolidar todo o vencido.'});
    snapshot.hasFinancialData=Boolean(dre?.rowCount||participations.length||snapshot.fiscal.outgoingCount||snapshot.fiscal.incomingCount);
    return snapshot;
  }

  return {MONEY_SECTIONS,DIMENSION_KINDS,clone,text,fold,num,roundMoney,sum,percent,safeDate,monthKey,normalizeCatalog,dimensionDescriptor,primaryDimension,allocationSlices,buildUnitPerformance,consolidatedFromDre,comparison,bridge,buildProductsVsServices,buildTrend,buildFiscalSummary,buildParticipationSummary,buildParticipationTable,buildDeductionBreakdown,buildCostStructure,buildRankings,buildDashboard};
});
