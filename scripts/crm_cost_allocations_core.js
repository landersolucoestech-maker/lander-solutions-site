(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenCostAllocationCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const METHODS=['percentage','fixed','equal','driver'];
  const STATUSES=['draft','review','approved','posted','reversed'];
  const DESTINATION_TYPES=['corporate','product','service','business_unit'];
  const CONSISTENCY_STATUSES=['consistent','needs_review'];
  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const num=(value)=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0;};
  const toCents=(value)=>Math.round((num(value)+Number.EPSILON)*100);
  const fromCents=(value)=>Math.round(value)/100;
  const moneyEqual=(a,b)=>Math.abs(toCents(a)-toCents(b))<=0;
  const percent=(value)=>Math.round(num(value)*1000000)/1000000;
  const percentEqual=(a,b,tolerance=0.0001)=>Math.abs(num(a)-num(b))<=tolerance;
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}
  function createState(options={}){const now=options.now||(()=>new Date().toISOString());return {schemaVersion:SCHEMA_VERSION,allocations:[],lines:[],criteria:[],approvals:[],history:[],metadata:{createdAt:now(),legacyMigrated:false}};}
  function ensureState(input,options={}){const data=input&&typeof input==='object'?input:createState(options);for(const key of ['allocations','lines','criteria','approvals','history'])if(!Array.isArray(data[key]))data[key]=[];if(!data.metadata||typeof data.metadata!=='object')data.metadata={};data.schemaVersion=SCHEMA_VERSION;return data;}

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const finance=()=>typeof options.financeService==='function'?options.financeService():options.financeService;
    const resolveDestination=options.resolveDestination||(()=>true);
    const data=ensureState(store,{now});
    const financeService=()=>{const service=finance();if(!service||typeof service.getTransaction!=='function')throw new Error('Fonte financeira canônica indisponível');return service;};
    const getTransaction=(id)=>financeService().getTransaction(id);
    const getAllocation=(id)=>data.allocations.find((row)=>row.id===id)||null;
    const getLines=(id)=>data.lines.filter((row)=>row.allocationId===id).sort((a,b)=>a.order-b.order);
    const getCriterion=(id)=>data.criteria.find((row)=>row.id===id)||null;
    const snapshotSource=(tx)=>({amount:tx.amount,status:tx.status,financialNature:tx.financialNature,direction:tx.direction,categoryId:tx.categoryId||'',businessDimension:tx.businessDimension||'',productId:tx.productId||'',transactionDate:tx.transactionDate||''});
    const history=(action,allocationId,before,after,metadata={})=>{const event={id:idFactory('allochist'),action,allocationId:allocationId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(event);return event;};
    const approval=(action,row)=>{const event={id:idFactory('allocapproval'),allocationId:row.id,action,version:row.version,at:now(),actorId:actor()||null};data.approvals.push(event);return event;};
    const touch=(row)=>{row.updatedAt=now();row.updatedBy=actor()||null;return row;};

    function assertEligibleTransaction(id,{forPosting=false}={}){
      const tx=getTransaction(id);if(!tx)throw new Error('Transação de origem não encontrada');
      if(tx.isDemo)throw new Error('Transação demo não é elegível para Rateio real');
      if(tx.status==='excluded')throw new Error('Transação excluída não é elegível para Rateio');
      if(tx.financialNature==='transfer')throw new Error('Transferência não é elegível para Rateio');
      if(tx.financialNature!=='expense'||tx.direction!=='outflow')throw new Error('Rateios aceita somente custos/despesas de saída');
      if(!['pending','posted'].includes(tx.status))throw new Error('Status da transação não é elegível para Rateio');
      if(forPosting&&tx.status!=='posted')throw new Error('Somente transação lançada pode receber Rateio postado');
      return tx;
    }

    function normalizeDestination(input={}){
      let destinationType=text(input.destinationType||input.dimension);
      if(destinationType==='unit')destinationType='business_unit';
      if(!DESTINATION_TYPES.includes(destinationType))throw new Error('Destino de Rateio inválido');
      const destinationId=destinationType==='corporate'?'':text(input.destinationId||input.productId||input.serviceId||input.businessUnitId);
      if(destinationType!=='corporate'&&!destinationId)throw new Error('Destino requer referência estável');
      if(destinationType!=='corporate'&&!resolveDestination(destinationType,destinationId))throw new Error('Destino canônico não encontrado');
      return {destinationType,destinationId};
    }

    function normalizeLineInput(input={},index=0){
      const destination=normalizeDestination(input);
      return {
        id:input.id||idFactory('allocline'),
        destinationType:destination.destinationType,
        destinationId:destination.destinationId,
        percentage:input.percentage==null||input.percentage===''?null:percent(input.percentage),
        amount:input.amount==null||input.amount===''?null:fromCents(toCents(input.amount)),
        driverValue:input.driverValue==null||input.driverValue===''?null:num(input.driverValue),
        note:text(input.note),
        metadata:clone(input.metadata||{}),
        order:index+1
      };
    }

    function assertUniqueDestinations(lines){
      const seen=new Set();
      for(const line of lines){const key=`${line.destinationType}:${line.destinationId}`;if(seen.has(key))throw new Error('Destino duplicado no mesmo Rateio');seen.add(key);}
      return true;
    }

    function distributeCents(totalCents,weights){
      if(!weights.length)return [];
      const sum=weights.reduce((acc,value)=>acc+num(value),0);if(!(sum>0))throw new Error('Direcionadores precisam somar valor maior que zero');
      const raw=weights.map((weight)=>totalCents*num(weight)/sum);
      const cents=raw.map((value)=>Math.floor(value));
      let remainder=totalCents-cents.reduce((a,b)=>a+b,0);
      const order=raw.map((value,index)=>({index,fraction:value-Math.floor(value)})).sort((a,b)=>b.fraction-a.fraction||a.index-b.index);
      for(let i=0;i<remainder;i++)cents[order[i%order.length].index]++;
      return cents;
    }

    function calculate(method,basisAmount,inputLines,allowPartial=false){
      if(!METHODS.includes(method))throw new Error('Método de Rateio inválido');
      const basisCents=toCents(basisAmount);if(!(basisCents>0))throw new Error('Valor-base do Rateio deve ser maior que zero');
      const lines=inputLines.map((line,index)=>normalizeLineInput(line,index));
      if(!lines.length)throw new Error('Adicione pelo menos um destino');
      assertUniqueDestinations(lines);

      let distributedCents=0;
      if(method==='percentage'){
        if(lines.some((line)=>line.percentage==null||line.percentage<0))throw new Error('Percentual inválido');
        const totalPercent=percent(lines.reduce((sum,line)=>sum+line.percentage,0));
        if(allowPartial){if(totalPercent>100.0001)throw new Error('Percentual não pode exceder 100%');}
        else if(!percentEqual(totalPercent,100))throw new Error('Rateio percentual integral deve totalizar 100%');
        const targetCents=Math.round(basisCents*totalPercent/100);
        const shares=lines.map((line)=>line.percentage);
        const cents=targetCents?distributeCents(targetCents,shares):lines.map(()=>0);
        lines.forEach((line,index)=>{line.amount=fromCents(cents[index]);});
        distributedCents=cents.reduce((a,b)=>a+b,0);
      }else if(method==='fixed'){
        if(lines.some((line)=>line.amount==null||line.amount<0))throw new Error('Valor fixo inválido');
        distributedCents=lines.reduce((sum,line)=>sum+toCents(line.amount),0);
        if(allowPartial){if(distributedCents>basisCents)throw new Error('Rateio não pode exceder o valor-base');}
        else if(distributedCents!==basisCents)throw new Error('Rateio por valor integral deve totalizar o valor-base');
        lines.forEach((line)=>{line.percentage=basisCents?percent(toCents(line.amount)*100/basisCents):0;});
      }else if(method==='equal'){
        const cents=distributeCents(basisCents,lines.map(()=>1));
        lines.forEach((line,index)=>{line.amount=fromCents(cents[index]);line.percentage=percent(cents[index]*100/basisCents);});
        distributedCents=basisCents;
      }else if(method==='driver'){
        if(lines.some((line)=>line.driverValue==null||line.driverValue<0))throw new Error('Direcionador inválido');
        const cents=distributeCents(basisCents,lines.map((line)=>line.driverValue));
        lines.forEach((line,index)=>{line.amount=fromCents(cents[index]);line.percentage=percent(cents[index]*100/basisCents);});
        distributedCents=basisCents;
      }
      const distributedAmount=fromCents(distributedCents),unallocatedAmount=fromCents(basisCents-distributedCents);
      const totalPercentage=percent(lines.reduce((sum,line)=>sum+num(line.percentage),0));
      return {lines,distributedAmount,unallocatedAmount,totalPercentage,basisAmount:fromCents(basisCents)};
    }

    function activePostedForTransaction(transactionId,excludeId=''){
      return data.allocations.find((row)=>row.sourceTransactionId===transactionId&&row.id!==excludeId&&row.status==='posted'&&row.consistencyStatus!=='needs_review')||null;
    }

    function createAllocation(input={}){
      const tx=assertEligibleTransaction(input.sourceTransactionId);
      const active=activePostedForTransaction(tx.id);if(active&&!input.replacesAllocationId)throw new Error(`A transação já possui Rateio postado ativo: ${active.id}`);
      const id=input.id||idFactory('calloc');
      if(getAllocation(id))throw new Error('ID de Rateio já existe');
      const method=METHODS.includes(input.method)?input.method:'percentage';
      const version=Math.max(1,Number(input.version||1));
      const row={
        id,
        sourceTransactionId:tx.id,
        name:text(input.name||tx.originalDescription||'Rateio'),
        description:text(input.description),
        method,
        criterionId:text(input.criterionId),
        basisAmount:fromCents(toCents(tx.amount)),
        distributedAmount:0,
        unallocatedAmount:fromCents(toCents(tx.amount)),
        totalPercentage:0,
        allowPartial:!!input.allowPartial,
        status:'draft',
        effectiveDate:text(input.effectiveDate||tx.transactionDate),
        accountingPeriod:text(input.accountingPeriod),
        submittedAt:null,submittedBy:null,
        reviewedAt:null,reviewedBy:null,
        approvedAt:null,approvedBy:null,
        postedAt:null,postedBy:null,
        reversedAt:null,reversedBy:null,reversalReason:'',
        notes:text(input.notes),
        version,
        parentAllocationId:text(input.parentAllocationId),
        replacesAllocationId:text(input.replacesAllocationId),
        sourceSnapshot:snapshotSource(tx),
        consistencyStatus:'consistent',
        consistencyIssues:[],
        isDemo:!!input.isDemo,
        metadata:clone(input.metadata||{}),
        createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null
      };
      data.allocations.push(row);
      history('allocation.created',id,null,row,{sourceTransactionId:tx.id});
      if(Array.isArray(input.lines)&&input.lines.length)replaceLines(id,input.lines);
      return row;
    }

    function assertDraft(id){const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');if(row.status!=='draft')throw new Error('Somente Rascunho pode ser alterado');return row;}
    function replaceLines(id,inputLines=[]){
      const row=assertDraft(id),before={allocation:clone(row),lines:clone(getLines(id))};
      const result=calculate(row.method,row.basisAmount,inputLines,row.allowPartial);
      data.lines=data.lines.filter((line)=>line.allocationId!==id);
      for(const line of result.lines)data.lines.push({...line,allocationId:id});
      row.distributedAmount=result.distributedAmount;row.unallocatedAmount=result.unallocatedAmount;row.totalPercentage=result.totalPercentage;touch(row);
      history('allocation.lines.changed',id,before,{allocation:clone(row),lines:clone(getLines(id))});
      return getLines(id);
    }

    function updateDraft(id,input={}){
      const row=assertDraft(id),before=clone(row);
      if('sourceTransactionId'in input&&input.sourceTransactionId!==row.sourceTransactionId){const tx=assertEligibleTransaction(input.sourceTransactionId),active=activePostedForTransaction(tx.id,row.id);if(active)throw new Error(`A transação já possui Rateio postado ativo: ${active.id}`);row.sourceTransactionId=tx.id;row.basisAmount=fromCents(toCents(tx.amount));row.sourceSnapshot=snapshotSource(tx);row.consistencyStatus='consistent';row.consistencyIssues=[];}
      if('name'in input)row.name=text(input.name);
      if('description'in input)row.description=text(input.description);
      if('method'in input){if(!METHODS.includes(input.method))throw new Error('Método de Rateio inválido');row.method=input.method;}
      if('allowPartial'in input)row.allowPartial=!!input.allowPartial;
      if('criterionId'in input){if(input.criterionId&&!getCriterion(input.criterionId))throw new Error('Critério não encontrado');row.criterionId=text(input.criterionId);}
      if('effectiveDate'in input)row.effectiveDate=text(input.effectiveDate);
      if('accountingPeriod'in input)row.accountingPeriod=text(input.accountingPeriod);
      if('notes'in input)row.notes=text(input.notes);
      touch(row);
      history('allocation.draft.changed',id,before,row);
      if(Array.isArray(input.lines))replaceLines(id,input.lines);
      return row;
    }

    function preview(id){const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');const tx=getTransaction(row.sourceTransactionId),result=calculate(row.method,row.basisAmount,getLines(id),row.allowPartial);return {allocation:row,transaction:tx,...result};}
    function validateForWorkflow(id){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');
      assertEligibleTransaction(row.sourceTransactionId);
      const result=calculate(row.method,row.basisAmount,getLines(id),row.allowPartial);
      if(!row.allowPartial&&(result.unallocatedAmount!==0||!percentEqual(result.totalPercentage,100)))throw new Error('Rateio integral precisa fechar 100% e o valor-base');
      if(row.allowPartial&&result.unallocatedAmount<0)throw new Error('Saldo não distribuído inválido');
      return result;
    }

    function sendToReview(id){
      const row=assertDraft(id),before=clone(row);validateForWorkflow(id);
      row.status='review';row.submittedAt=now();row.submittedBy=actor()||null;touch(row);
      history('allocation.sent_to_review',id,before,row);approval('submitted',row);return row;
    }
    function returnToDraft(id,reason=''){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');if(row.status!=='review')throw new Error('Somente Rateio em revisão pode voltar para Rascunho');
      const before=clone(row);row.status='draft';row.metadata={...(row.metadata||{}),lastReturnReason:text(reason)};touch(row);history('allocation.returned_to_draft',id,before,row,{reason:text(reason)});return row;
    }
    function approve(id){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');if(row.status!=='review')throw new Error('Somente Rateio em revisão pode ser aprovado');
      validateForWorkflow(id);const before=clone(row);row.status='approved';row.reviewedAt=now();row.reviewedBy=actor()||null;row.approvedAt=now();row.approvedBy=actor()||null;touch(row);
      history('allocation.approved',id,before,row);approval('approved',row);return row;
    }

    function projectionLines(row){
      return getLines(row.id).map((line)=>({
        allocationId:row.id,allocationVersion:row.version,dimension:line.destinationType,
        destinationType:line.destinationType,destinationId:line.destinationId,
        productId:line.destinationType==='product'?line.destinationId:'',
        serviceId:line.destinationType==='service'?line.destinationId:'',
        businessUnitId:line.destinationType==='business_unit'?line.destinationId:'',
        percentage:line.percentage,amount:line.amount,driverValue:line.driverValue,
        source:'cost_allocation',status:'posted'
      }));
    }

    function writeProjection(row){
      const service=financeService(),tx=getTransaction(row.sourceTransactionId);if(!tx)throw new Error('Transação de origem não encontrada');
      service.updateTransaction(tx.id,{allocations:projectionLines(row),metadata:{costAllocationProjection:{allocationId:row.id,version:row.version,status:'posted',basisAmount:row.basisAmount,postedAt:row.postedAt}}});
      return tx.allocations;
    }

    function post(id){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');
      if(row.status==='posted'){refreshConsistency(id);return row;}
      if(row.status!=='approved')throw new Error('Somente Rateio aprovado pode ser postado');
      const tx=assertEligibleTransaction(row.sourceTransactionId,{forPosting:true});
      validateForWorkflow(id);refreshConsistency(id);
      if(row.consistencyStatus==='needs_review')throw new Error('Rateio inconsistente precisa de nova revisão');
      const existing=activePostedForTransaction(tx.id,row.id);if(existing)throw new Error(`A transação já possui Rateio postado ativo: ${existing.id}`);
      const before=clone(row);row.status='posted';row.postedAt=now();row.postedBy=actor()||null;row.sourceSnapshot=snapshotSource(tx);row.consistencyStatus='consistent';row.consistencyIssues=[];touch(row);
      writeProjection(row);history('allocation.posted',id,before,row);approval('posted',row);return row;
    }

    function clearProjection(row,reason=''){
      const service=financeService(),tx=getTransaction(row.sourceTransactionId);if(!tx)return;
      const current=Array.isArray(tx.allocations)?tx.allocations:[];
      const filtered=current.filter((item)=>item.allocationId!==row.id);
      if(filtered.length!==current.length||tx.metadata?.costAllocationProjection?.allocationId===row.id){
        service.updateTransaction(tx.id,{allocations:filtered,metadata:{costAllocationProjection:{allocationId:row.id,version:row.version,status:reason||'inactive',basisAmount:row.basisAmount}}});
      }
    }

    function reverse(id,reason=''){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');if(row.status!=='posted')throw new Error('Somente Rateio postado pode ser estornado');
      const before=clone(row);clearProjection(row,'reversed');row.status='reversed';row.reversedAt=now();row.reversedBy=actor()||null;row.reversalReason=text(reason);touch(row);
      history('allocation.reversed',id,before,row,{reason:row.reversalReason});approval('reversed',row);return row;
    }

    function removeDraft(id){
      const row=getAllocation(id);if(!row)return false;if(row.status!=='draft')throw new Error('Somente Rascunho sem efeito pode ser excluído');
      const before={allocation:clone(row),lines:clone(getLines(id))};data.lines=data.lines.filter((line)=>line.allocationId!==id);data.allocations=data.allocations.filter((item)=>item.id!==id);history('allocation.draft.deleted',id,before,null);return true;
    }

    function createNewVersion(id){
      const source=getAllocation(id);if(!source)throw new Error('Rateio não encontrado');if(!['posted','reversed'].includes(source.status))throw new Error('Nova versão exige Rateio postado ou estornado');
      const siblings=data.allocations.filter((row)=>(row.metadata?.versionGroupId||row.id)===(source.metadata?.versionGroupId||source.id));
      const version=Math.max(source.version,...siblings.map((row)=>row.version||1))+1;
      const created=createAllocation({sourceTransactionId:source.sourceTransactionId,name:source.name,description:source.description,method:source.method,criterionId:source.criterionId,allowPartial:source.allowPartial,effectiveDate:source.effectiveDate,accountingPeriod:source.accountingPeriod,notes:source.notes,version,parentAllocationId:source.id,replacesAllocationId:source.id,metadata:{...(source.metadata||{}),versionGroupId:source.metadata?.versionGroupId||source.id}});
      replaceLines(created.id,getLines(source.id).map((line)=>({...line,id:undefined})));
      history('allocation.new_version_created',created.id,null,created,{previousAllocationId:source.id,previousVersion:source.version});
      return created;
    }

    function refreshConsistency(id){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');const tx=getTransaction(row.sourceTransactionId),issues=[];
      if(!tx)issues.push('source_missing');
      else{
        if(tx.status==='excluded')issues.push('source_excluded');
        if(row.status==='posted'&&tx.status!=='posted')issues.push('source_not_posted');
        if(!moneyEqual(tx.amount,row.sourceSnapshot?.amount??row.basisAmount))issues.push('source_amount_changed');
        if((tx.categoryId||'')!==(row.sourceSnapshot?.categoryId||''))issues.push('source_classification_changed');
        if((tx.businessDimension||'')!==(row.sourceSnapshot?.businessDimension||'')||(tx.productId||'')!==(row.sourceSnapshot?.productId||''))issues.push('source_dimension_changed');
        if(tx.financialNature!=='expense'||tx.direction!=='outflow')issues.push('source_no_longer_expense');
      }
      const beforeStatus=row.consistencyStatus;
      row.consistencyStatus=issues.length?'needs_review':'consistent';row.consistencyIssues=issues;
      if(issues.length&&row.status==='posted')clearProjection(row,'needs_review');
      if(beforeStatus!==row.consistencyStatus)history('allocation.consistency.changed',row.id,{consistencyStatus:beforeStatus},{consistencyStatus:row.consistencyStatus,issues:clone(issues)});
      return row;
    }

    function refreshAllConsistency(){for(const row of data.allocations)if(['approved','posted'].includes(row.status))refreshConsistency(row.id);return data.allocations;}

    function createCriterion(input={}){
      const method=METHODS.includes(input.method)?input.method:'percentage',name=text(input.name);if(!name)throw new Error('Critério requer nome');
      const templateLines=(input.lines||[]).map((line,index)=>normalizeLineInput(line,index));if(templateLines.length)assertUniqueDestinations(templateLines);
      const row={id:input.id||idFactory('alloccriterion'),name,type:text(input.type||method),method,description:text(input.description),unit:text(input.unit),status:text(input.status||'active')||'active',lines:clone(templateLines),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};
      data.criteria.push(row);history('criterion.created','',null,row,{criterionId:row.id});return row;
    }
    function applyCriterion(allocationId,criterionId){
      const row=assertDraft(allocationId),criterion=getCriterion(criterionId);if(!criterion||criterion.status==='inactive')throw new Error('Critério não encontrado');
      const before=clone(row);row.method=criterion.method;row.criterionId=criterion.id;touch(row);replaceLines(row.id,criterion.lines.map((line)=>({...line,id:undefined})));history('criterion.applied',row.id,before,row,{criterionId});return row;
    }

    function memory(id){
      const row=getAllocation(id);if(!row)throw new Error('Rateio não encontrado');const tx=getTransaction(row.sourceTransactionId),lines=getLines(id);
      return {allocationId:row.id,version:row.version,sourceTransactionId:row.sourceTransactionId,sourceDescription:tx?.originalDescription||'',basisAmount:row.basisAmount,method:row.method,criterionId:row.criterionId,lines:clone(lines),distributedAmount:row.distributedAmount,unallocatedAmount:row.unallocatedAmount,totalPercentage:row.totalPercentage,consistent:row.consistencyStatus==='consistent'};
    }

    function accountingProjection(transactionId){
      const rows=data.allocations.filter((row)=>row.sourceTransactionId===transactionId);
      if(!rows.length)return {handled:false,allocation:null,lines:[]};
      const active=rows.find((row)=>row.status==='posted')||null;
      if(!active)return {handled:true,allocation:null,lines:[]};
      refreshConsistency(active.id);
      if(active.consistencyStatus!=='consistent')return {handled:true,allocation:active,lines:[]};
      return {handled:true,allocation:active,lines:projectionLines(active)};
    }

    function query(filters={}){
      refreshAllConsistency();
      let rows=data.allocations.filter((row)=>filters.includeDemo?true:!row.isDemo);
      if(filters.status&&filters.status!=='all')rows=rows.filter((row)=>row.status===filters.status);
      if(filters.method)rows=rows.filter((row)=>row.method===filters.method);
      if(filters.from)rows=rows.filter((row)=>(row.effectiveDate||'')>=filters.from);
      if(filters.to)rows=rows.filter((row)=>(row.effectiveDate||'')<=filters.to);
      if(filters.responsible)rows=rows.filter((row)=>[row.createdBy,row.reviewedBy,row.approvedBy,row.postedBy].includes(filters.responsible));
      if(filters.accountId||filters.categoryId){
        rows=rows.filter((row)=>{const tx=getTransaction(row.sourceTransactionId);if(!tx)return false;if(filters.accountId&&tx.financialAccountId!==filters.accountId)return false;if(filters.categoryId&&tx.categoryId!==filters.categoryId)return false;return true;});
      }
      if(filters.destinationType||filters.destinationId)rows=rows.filter((row)=>getLines(row.id).some((line)=>(!filters.destinationType||line.destinationType===filters.destinationType)&&(!filters.destinationId||line.destinationId===filters.destinationId)));
      if(filters.search){const needle=text(filters.search).toLowerCase();rows=rows.filter((row)=>{const tx=getTransaction(row.sourceTransactionId),blob=[row.id,row.name,row.description,row.accountingPeriod,row.createdBy,tx?.id,tx?.originalDescription,tx?.financialAccountId,tx?.categoryId,...getLines(row.id).flatMap((line)=>[line.destinationType,line.destinationId])].join(' ').toLowerCase();return blob.includes(needle);});}
      rows.sort((a,b)=>String(b.effectiveDate||b.createdAt).localeCompare(String(a.effectiveDate||a.createdAt)));
      const total=rows.length,limit=Math.max(1,Math.min(50,Number(filters.limit||50))),page=Math.max(1,Number(filters.page||1)),offset=(page-1)*limit;
      return {rows:rows.slice(offset,offset+limit),total,page,limit};
    }

    function migrateLegacyTransactionAllocations(){
      if(data.metadata.legacyMigrated)return {created:0,skipped:0};
      const service=financeService();let created=0,skipped=0;
      for(const tx of service.data.transactions||[]){
        if(!Array.isArray(tx.allocations)||!tx.allocations.length)continue;
        if(data.allocations.some((row)=>row.sourceTransactionId===tx.id)){skipped++;continue;}
        if(tx.financialNature!=='expense'||tx.direction!=='outflow'||tx.isDemo||tx.status==='excluded'){skipped++;continue;}
        const method=tx.allocations.every((line)=>line.amount!=null)?'fixed':'percentage';
        const legacyLines=[];
        for(const item of tx.allocations){
          const destinationType=item.dimension==='corporate'?'corporate':item.dimension==='service'?'service':item.dimension==='business_unit'?'business_unit':'product';
          const destinationId=destinationType==='corporate'?'':text(item.destinationId||item.productId||item.serviceId||item.businessUnitId);
          if(destinationType!=='corporate'&&!destinationId)continue;
          legacyLines.push({destinationType,destinationId,percentage:item.percentage,amount:item.amount,driverValue:item.driverValue,note:'Compatibilidade de allocation legado'});
        }
        if(!legacyLines.length){skipped++;continue;}
        const row=createAllocation({sourceTransactionId:tx.id,name:`Rateio legado · ${tx.originalDescription||tx.id}`,method,lines:legacyLines,isDemo:false,metadata:{legacyTransactionAllocation:true,versionGroupId:`legacy:${tx.id}`}});
        if(tx.status==='posted'){
          row.status='approved';row.reviewedAt=now();row.reviewedBy='legacy';row.approvedAt=now();row.approvedBy='legacy';post(row.id);
        }else{
          service.updateTransaction(tx.id,{allocations:[],metadata:{costAllocationProjection:{allocationId:row.id,version:row.version,status:'draft',basisAmount:row.basisAmount}}});
        }
        created++;
      }
      data.metadata.legacyMigrated=true;data.metadata.legacyMigratedAt=now();return {created,skipped};
    }

    return {data,getAllocation,getLines,getCriterion,createAllocation,replaceLines,updateDraft,preview,validateForWorkflow,sendToReview,returnToDraft,approve,post,reverse,removeDraft,createNewVersion,refreshConsistency,refreshAllConsistency,createCriterion,applyCriterion,memory,accountingProjection,query,migrateLegacyTransactionAllocations,assertEligibleTransaction,calculate,projectionLines,activePostedForTransaction};
  }

  return {SCHEMA_VERSION,METHODS,STATUSES,DESTINATION_TYPES,CONSISTENCY_STATUSES,createState,ensureState,createService,toCents,fromCents,moneyEqual,percent,percentEqual};
});
