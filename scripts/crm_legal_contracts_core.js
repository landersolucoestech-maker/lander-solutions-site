(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenContractCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const CONTRACT_STATUSES=['draft','negotiation','active','suspended','expired','terminated','archived'];
  const VERSION_STATUSES=['draft','review','approved','rejected','signed','superseded'];
  const TEMPLATE_STATUSES=['draft','active','archived'];
  const TEMPLATE_VERSION_STATUSES=['draft','active','superseded'];
  const PARTY_TYPES=['person','organization'];
  const ECONOMIC_RULE_TYPES=['percentage','fixed','tiered','custom'];
  const BASIS_TYPES=['gross_revenue','net_revenue','distributable_base','product_result','service_result','custom_reference'];
  const SIGNATURE_STATUSES=['pending','manual_recorded','signed'];
  const VARIABLE_STATUSES=['active','inactive'];
  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const num=(value)=>{const n=Number(value);return Number.isFinite(n)?n:null;};
  const isoDate=(value)=>/^\d{4}-\d{2}-\d{2}$/.test(text(value))?text(value):'';
  const dateBefore=(a,b)=>!!a&&!!b&&a<b;
  const overlaps=(aFrom,aUntil,bFrom,bUntil)=>{const af=aFrom||'0000-01-01',au=aUntil||'9999-12-31',bf=bFrom||'0000-01-01',bu=bUntil||'9999-12-31';return af<=bu&&bf<=au;};
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}

  const BUILTIN_VARIABLES=[
    ['EMPRESA.RAZAO_SOCIAL','Razão social da empresa','Empresa','text','company.legalName',true,'Configurações / Empresa'],
    ['EMPRESA.CNPJ','CNPJ da empresa','Empresa','text','company.cnpj',true,'Configurações / Empresa'],
    ['EMPRESA.ENDERECO','Endereço institucional da empresa','Empresa','text','company.address',false,'Configurações / Empresa'],
    ['CLIENTE.NOME','Nome ou razão social do cliente','Cliente','text','customer.name',true,'CRM'],
    ['CLIENTE.DOCUMENTO','CPF ou CNPJ do cliente','Cliente','text','customer.document',true,'CRM'],
    ['CONTRATO.NUMERO','Número interno ou informado do contrato','Contrato','text','contract.number',true,'Jurídico / Contratos'],
    ['CONTRATO.VALOR','Valor de referência do contrato','Contrato','currency','contract.referenceValue',false,'Jurídico / Contratos'],
    ['CONTRATO.INICIO','Data inicial do contrato','Contrato','date','contract.startDate',false,'Jurídico / Contratos'],
    ['CONTRATO.FIM','Data final do contrato','Contrato','date','contract.endDate',false,'Jurídico / Contratos'],
    ['PRODUTO.NOME','Nome do Produto relacionado','Produto','text','reference.product',false,'Negócios / Produtos'],
    ['SERVICO.NOME','Nome do Serviço relacionado','Serviço','text','reference.service',false,'Negócios / Serviços'],
    ['UNIDADE.NOME','Nome da Unidade de Negócio relacionada','Unidade','text','reference.business_unit',false,'Negócios / Unidades de Negócio']
  ];

  function createState(options={}){
    const now=options.now||(()=>new Date().toISOString());
    return {schemaVersion:SCHEMA_VERSION,contracts:[],versions:[],parties:[],clauses:[],economicRules:[],approvals:[],signatures:[],attachments:[],history:[],templates:[],templateVersions:[],variables:[],legacyBindings:[],metadata:{createdAt:now(),internalNumberSequence:{},legacyMigrated:false,legacySkipped:[]}};
  }
  function ensureState(input,options={}){
    const data=input&&typeof input==='object'?input:createState(options),template=createState(options);
    for(const [key,value] of Object.entries(template))if(Array.isArray(value)&&!Array.isArray(data[key]))data[key]=[];
    if(!data.metadata||typeof data.metadata!=='object')data.metadata={};
    if(!data.metadata.internalNumberSequence||typeof data.metadata.internalNumberSequence!=='object')data.metadata.internalNumberSequence={};
    if(!Array.isArray(data.metadata.legacySkipped))data.metadata.legacySkipped=[];
    data.schemaVersion=SCHEMA_VERSION;
    return data;
  }

  function createService(store,options={}){
    const now=options.now||(()=>new Date().toISOString());
    const today=options.today||(()=>now().slice(0,10));
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const partyOption=options.partyService;
    const companyProvider=options.companyProvider||(()=>({}));
    const resolveReference=options.resolveReference||(()=>null);
    const data=ensureState(store,{now});
    const partyService=()=>{const service=typeof partyOption==='function'?partyOption():partyOption;if(!service||typeof service.getEntity!=='function')throw new Error('Infraestrutura canônica de Pessoas e Organizações indisponível');return service;};
    const history=(action,entityType,entityId,before,after,metadata={})=>{const row={id:idFactory('legalhist'),action,entityType,entityId,at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};data.history.push(row);return row;};
    const getContract=(id)=>data.contracts.find((x)=>x.id===id)||null;
    const getVersion=(id)=>data.versions.find((x)=>x.id===id)||null;
    const getTemplate=(id)=>data.templates.find((x)=>x.id===id)||null;
    const getTemplateVersion=(id)=>data.templateVersions.find((x)=>x.id===id)||null;
    const getVariable=(keyOrId)=>data.variables.find((x)=>x.id===keyOrId||x.key===keyOrId)||null;
    const versionsFor=(contractId)=>data.versions.filter((x)=>x.contractId===contractId).sort((a,b)=>a.versionNumber-b.versionNumber);
    const partiesFor=(versionId)=>data.parties.filter((x)=>x.contractVersionId===versionId).sort((a,b)=>a.order-b.order);
    const clausesFor=(versionId)=>data.clauses.filter((x)=>x.versionId===versionId).sort((a,b)=>a.order-b.order);
    const rulesFor=(versionId)=>data.economicRules.filter((x)=>x.contractVersionId===versionId);
    const signaturesFor=(versionId)=>data.signatures.filter((x)=>x.contractVersionId===versionId);
    const approvalsFor=(versionId)=>data.approvals.filter((x)=>x.contractVersionId===versionId);
    const templateVersionsFor=(templateId)=>data.templateVersions.filter((x)=>x.templateId===templateId).sort((a,b)=>a.versionNumber-b.versionNumber);

    function seedVariables(){
      for(const [key,label,scope,valueType,resolver,required,origin] of BUILTIN_VARIABLES){
        if(data.variables.some((x)=>x.key===key))continue;
        data.variables.push({id:idFactory('var'),key,label,description:label,scope,valueType,resolver,required,status:'active',fallbackPolicy:'block_if_required',origin,system:true,metadata:{builtin:true},createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null});
      }
      return data.variables;
    }
    seedVariables();

    function nextInternalNumber(){
      const year=String(today().slice(0,4)||new Date().getFullYear()),next=(Number(data.metadata.internalNumberSequence[year])||0)+1;
      data.metadata.internalNumberSequence[year]=next;
      return `CTR-${year}-${String(next).padStart(4,'0')}`;
    }
    function assertUniqueNumber(number,excludeId=''){
      const normalized=fold(number);if(!normalized)throw new Error('Número do contrato é obrigatório');
      if(data.contracts.some((x)=>x.id!==excludeId&&fold(x.number)===normalized))throw new Error('Número de contrato já existe');
      return true;
    }
    function validateReference(type,id){
      const ref=text(id);if(!ref)return null;
      const resolved=resolveReference(type,ref);if(!resolved)throw new Error(`${type==='product'?'Produto':type==='service'?'Serviço':'Unidade de Negócio'} referenciado não encontrado`);
      return resolved;
    }
    function normalizeParty(type,id){
      const partyType=PARTY_TYPES.includes(type)?type:'';if(!partyType)throw new Error('Tipo de parte inválido');
      const partyId=text(id);const entity=partyService().getEntity(partyType,partyId);if(!entity)throw new Error('Parte canônica não encontrada');
      return {partyType,partyId,entity};
    }
    function assertSignatory(partyType,partyId,signatoryPersonId){
      if(!signatoryPersonId)return null;
      const person=partyService().getEntity('person',signatoryPersonId);if(!person)throw new Error('Signatário canônico não encontrado');
      if(partyType==='organization'){
        const linked=partyService().getOrganizationContacts(partyId).some((x)=>x.person&&x.person.id===signatoryPersonId);
        if(!linked)throw new Error('Signatário deve estar vinculado à Organização contratual');
      }else if(signatoryPersonId!==partyId)throw new Error('Signatário de uma parte Pessoa deve ser a própria Pessoa');
      return person;
    }
    function partySnapshot(type,id){
      const service=partyService(),entity=service.getEntity(type,id);if(!entity)return null;
      const document=type==='person'?service.documentFor('person',id,'cpf'):service.documentFor('organization',id,'cnpj');
      const address=service.primaryAddress(type,id),email=service.primaryContact(type,id,'email'),phone=service.primaryContact(type,id,'phone');
      return {partyType:type,partyId:id,name:type==='person'?entity.fullName:(entity.legalName||entity.tradeName),document:document?.value||'',address:address?clone(address):null,email:email?.value||'',phone:phone?.value||''};
    }

    function createContract(input={}){
      const supplied=text(input.number),number=supplied||nextInternalNumber();assertUniqueNumber(number);
      const productId=text(input.productId),serviceId=text(input.serviceId),businessUnitId=text(input.businessUnitId);
      if(productId)validateReference('product',productId);if(serviceId)validateReference('service',serviceId);if(businessUnitId)validateReference('business_unit',businessUnitId);
      let customerPartyType=text(input.customerPartyType),customerPartyId=text(input.customerPartyId);
      if(customerPartyId){const normalized=normalizeParty(customerPartyType,customerPartyId);customerPartyType=normalized.partyType;customerPartyId=normalized.partyId;}
      const contract={id:input.id||idFactory('ctr'),number,numberSource:supplied?'manual':'internal',name:text(input.name)||number,type:text(input.type),category:text(input.category),status:'draft',ownerUserId:text(input.ownerUserId),responsibleUserIds:Array.isArray(input.responsibleUserIds)?[...new Set(input.responsibleUserIds.map(text).filter(Boolean))]:[],startDate:isoDate(input.startDate),endDate:isoDate(input.endDate),renewalDate:isoDate(input.renewalDate),terminationDate:'',terminationReason:'',currency:text(input.currency||'BRL')||'BRL',referenceValue:num(input.referenceValue),customerPartyType,customerPartyId,productId,serviceId,businessUnitId,templateId:'',activeVersionId:'',latestVersionId:'',createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null,metadata:clone(input.metadata||{}),isDemo:!!input.isDemo};
      if(contract.startDate&&contract.endDate&&dateBefore(contract.endDate,contract.startDate))throw new Error('Fim da vigência não pode ser anterior ao início');
      data.contracts.push(contract);history('contract.created','contract',contract.id,null,contract,{numberSource:contract.numberSource});
      let templateVersion=null;
      if(input.templateId){const template=getTemplate(input.templateId);if(!template)throw new Error('Template não encontrado');templateVersion=input.templateVersionId?getTemplateVersion(input.templateVersionId):getTemplateVersion(template.activeVersionId);if(!templateVersion||templateVersion.templateId!==template.id||templateVersion.status!=='active')throw new Error('Versão ativa do Template não encontrada');contract.templateId=template.id;}
      const version=createVersion(contract.id,{title:text(input.title||contract.name),content:templateVersion?templateVersion.content:text(input.content),effectiveFrom:isoDate(input.effectiveFrom||contract.startDate),effectiveUntil:isoDate(input.effectiveUntil||contract.endDate),currency:contract.currency,referenceValue:contract.referenceValue,templateId:templateVersion?.templateId||'',templateVersionId:templateVersion?.id||'',metadata:{source:templateVersion?'template':'manual'}});
      if(templateVersion){
        for(const definition of templateVersion.partyDefinitions||[]){if(definition.partyType&&definition.partyId)addParty(version.id,definition);}
        history('template.used','contract',contract.id,null,{templateId:templateVersion.templateId,templateVersionId:templateVersion.id});
      }
      contract.latestVersionId=version.id;return contract;
    }
    function updateContract(id,input={}){
      const row=getContract(id);if(!row)throw new Error('Contrato não encontrado');if(['terminated','archived'].includes(row.status))throw new Error('Contrato encerrado/arquivado não pode ser alterado diretamente');
      const before=clone(row);
      if('number'in input){const number=text(input.number);assertUniqueNumber(number,id);row.number=number;row.numberSource='manual';}
      for(const key of ['name','type','category','ownerUserId'])if(key in input)row[key]=text(input[key]);
      if('responsibleUserIds'in input)row.responsibleUserIds=[...new Set((input.responsibleUserIds||[]).map(text).filter(Boolean))];
      for(const key of ['startDate','endDate','renewalDate'])if(key in input)row[key]=isoDate(input[key]);
      if(row.startDate&&row.endDate&&dateBefore(row.endDate,row.startDate))throw new Error('Fim da vigência não pode ser anterior ao início');
      if('currency'in input)row.currency=text(input.currency||'BRL')||'BRL';if('referenceValue'in input)row.referenceValue=num(input.referenceValue);
      for(const [field,type] of [['productId','product'],['serviceId','service'],['businessUnitId','business_unit']])if(field in input){const value=text(input[field]);if(value)validateReference(type,value);row[field]=value;}
      if('customerPartyId'in input||'customerPartyType'in input){const type=text(input.customerPartyType||row.customerPartyType),partyId=text(input.customerPartyId||row.customerPartyId);if(partyId){const normalized=normalizeParty(type,partyId);row.customerPartyType=normalized.partyType;row.customerPartyId=normalized.partyId;}else{row.customerPartyType='';row.customerPartyId='';}}
      row.metadata={...(row.metadata||{}),...(input.metadata||{})};row.updatedAt=now();row.updatedBy=actor()||null;history('contract.updated','contract',id,before,row);return row;
    }

    function createVersion(contractId,input={}){
      const contract=getContract(contractId);if(!contract)throw new Error('Contrato não encontrado');
      const current=versionsFor(contractId),versionNumber=current.length?Math.max(...current.map((x)=>x.versionNumber))+1:1;
      const effectiveFrom=isoDate(input.effectiveFrom||contract.startDate),effectiveUntil=isoDate(input.effectiveUntil||contract.endDate);if(effectiveFrom&&effectiveUntil&&dateBefore(effectiveUntil,effectiveFrom))throw new Error('Vigência da versão inválida');
      const row={id:input.id||idFactory('ctrv'),contractId,versionNumber,status:'draft',title:text(input.title||contract.name),content:String(input.content??''),effectiveFrom,effectiveUntil,currency:text(input.currency||contract.currency||'BRL')||'BRL',referenceValue:num(input.referenceValue??contract.referenceValue),templateId:text(input.templateId),templateVersionId:text(input.templateVersionId),parentVersionId:text(input.parentVersionId),supersedesVersionId:text(input.supersedesVersionId),snapshot:null,createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null,submittedAt:null,submittedBy:null,approvedAt:null,approvedBy:null,rejectedAt:null,rejectedBy:null,rejectionReason:'',signedAt:null,supersededAt:null,supersededByVersionId:'',metadata:clone(input.metadata||{})};
      data.versions.push(row);contract.latestVersionId=row.id;contract.updatedAt=now();contract.updatedBy=actor()||null;history('version.created','version',row.id,null,row,{contractId});return row;
    }
    function createNewVersion(contractId,sourceVersionId=''){
      const contract=getContract(contractId);if(!contract)throw new Error('Contrato não encontrado');const source=getVersion(sourceVersionId||contract.latestVersionId);if(!source||source.contractId!==contractId)throw new Error('Versão de origem não encontrada');
      const row=createVersion(contractId,{title:source.title,content:source.content,effectiveFrom:source.effectiveFrom,effectiveUntil:source.effectiveUntil,currency:source.currency,referenceValue:source.referenceValue,templateId:source.templateId,templateVersionId:source.templateVersionId,parentVersionId:source.id,supersedesVersionId:['approved','signed'].includes(source.status)?source.id:'',metadata:{clonedFromVersionId:source.id}});
      for(const p of partiesFor(source.id))addParty(row.id,{partyType:p.partyType,partyId:p.partyId,role:p.role,signatory:p.signatory,signatoryPersonId:p.signatoryPersonId,order:p.order,notes:p.notes,metadata:clone(p.metadata)});
      for(const c of clausesFor(source.id))addClause(row.id,{title:c.title,content:c.content,order:c.order,category:c.category,metadata:clone(c.metadata)});
      for(const r of rulesFor(source.id))addEconomicRule(row.id,{name:r.name,type:r.type,participantPartyType:r.participantPartyType,participantPartyId:r.participantPartyId,percentage:r.percentage,fixedValue:r.fixedValue,basisType:r.basisType,deductions:clone(r.deductions),effectiveFrom:r.effectiveFrom,effectiveUntil:r.effectiveUntil,status:r.status,productId:r.productId,serviceId:r.serviceId,businessUnitId:r.businessUnitId,currency:r.currency,metadata:clone(r.metadata)});
      history('version.cloned','version',row.id,null,row,{sourceVersionId:source.id});return row;
    }
    function assertVersionDraft(versionId){const row=getVersion(versionId);if(!row)throw new Error('Versão não encontrada');if(row.status!=='draft')throw new Error('Somente versão em Rascunho pode ser alterada');return row;}
    function updateVersion(versionId,input={}){
      const row=assertVersionDraft(versionId),before=clone(row);
      if('title'in input)row.title=text(input.title);if('content'in input)row.content=String(input.content??'');
      if('effectiveFrom'in input)row.effectiveFrom=isoDate(input.effectiveFrom);if('effectiveUntil'in input)row.effectiveUntil=isoDate(input.effectiveUntil);if(row.effectiveFrom&&row.effectiveUntil&&dateBefore(row.effectiveUntil,row.effectiveFrom))throw new Error('Vigência da versão inválida');
      if('currency'in input)row.currency=text(input.currency||'BRL')||'BRL';if('referenceValue'in input)row.referenceValue=num(input.referenceValue);
      row.metadata={...(row.metadata||{}),...(input.metadata||{})};row.updatedAt=now();row.updatedBy=actor()||null;history('version.updated','version',versionId,before,row);return row;
    }

    function addParty(versionId,input={}){
      const version=assertVersionDraft(versionId),normalized=normalizeParty(input.partyType,input.partyId),signatoryPersonId=text(input.signatoryPersonId);if(signatoryPersonId)assertSignatory(normalized.partyType,normalized.partyId,signatoryPersonId);
      const duplicate=data.parties.find((x)=>x.contractVersionId===versionId&&x.partyType===normalized.partyType&&x.partyId===normalized.partyId&&text(x.role)===text(input.role));if(duplicate)throw new Error('Parte com o mesmo papel já existe nesta versão');
      const row={id:input.id||idFactory('ctrparty'),contractVersionId:versionId,partyType:normalized.partyType,partyId:normalized.partyId,role:text(input.role||'Outro')||'Outro',signatory:!!input.signatory,signatoryPersonId,order:Number(input.order)||partiesFor(versionId).length+1,notes:text(input.notes),metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null};data.parties.push(row);history('party.added','version',versionId,null,row);return row;
    }
    function removeParty(versionId,partyRowId){assertVersionDraft(versionId);const index=data.parties.findIndex((x)=>x.id===partyRowId&&x.contractVersionId===versionId);if(index<0)throw new Error('Parte não encontrada');const [row]=data.parties.splice(index,1);history('party.removed','version',versionId,row,null);return true;}
    function addClause(versionId,input={}){assertVersionDraft(versionId);const row={id:input.id||idFactory('clause'),versionId,title:text(input.title),content:String(input.content??''),order:Number(input.order)||clausesFor(versionId).length+1,category:text(input.category),metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null};data.clauses.push(row);history('clause.added','version',versionId,null,row);return row;}

    function addEconomicRule(versionId,input={}){
      assertVersionDraft(versionId);const type=ECONOMIC_RULE_TYPES.includes(input.type)?input.type:'percentage',participant=normalizeParty(input.participantPartyType,input.participantPartyId),basisType=text(input.basisType);
      if(!BASIS_TYPES.includes(basisType))throw new Error('Base econômica inválida ou ausente');
      let percentage=null,fixedValue=null;if(type==='percentage'){percentage=num(input.percentage);if(percentage==null||percentage<=0||percentage>100)throw new Error('Percentual econômico deve ser maior que 0% e no máximo 100%');}else if(type==='fixed'){fixedValue=num(input.fixedValue);if(fixedValue==null||fixedValue<0)throw new Error('Valor fixo econômico inválido');}
      const effectiveFrom=isoDate(input.effectiveFrom),effectiveUntil=isoDate(input.effectiveUntil);if(effectiveFrom&&effectiveUntil&&dateBefore(effectiveUntil,effectiveFrom))throw new Error('Vigência da regra econômica inválida');
      const productId=text(input.productId),serviceId=text(input.serviceId),businessUnitId=text(input.businessUnitId);if(productId)validateReference('product',productId);if(serviceId)validateReference('service',serviceId);if(businessUnitId)validateReference('business_unit',businessUnitId);
      const row={id:input.id||idFactory('econ'),contractVersionId:versionId,name:text(input.name)||'Regra econômica',type,participantPartyType:participant.partyType,participantPartyId:participant.partyId,percentage,fixedValue,basisType,deductions:Array.isArray(input.deductions)?[...new Set(input.deductions.map(text).filter(Boolean))]:[],effectiveFrom,effectiveUntil,status:text(input.status||'active')||'active',productId,serviceId,businessUnitId,currency:text(input.currency||getVersion(versionId)?.currency||'BRL')||'BRL',metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.economicRules.push(row);history('economic_rule.created','version',versionId,null,row);return row;
    }
    function updateEconomicRule(ruleId,input={}){
      const row=data.economicRules.find((x)=>x.id===ruleId);if(!row)throw new Error('Regra econômica não encontrada');assertVersionDraft(row.contractVersionId);const before=clone(row),merged={...row,...input};
      const participant=normalizeParty(merged.participantPartyType,merged.participantPartyId),type=ECONOMIC_RULE_TYPES.includes(merged.type)?merged.type:'';if(!type)throw new Error('Tipo de regra econômica inválido');const basisType=text(merged.basisType);if(!BASIS_TYPES.includes(basisType))throw new Error('Base econômica inválida ou ausente');
      if(type==='percentage'){const p=num(merged.percentage);if(p==null||p<=0||p>100)throw new Error('Percentual econômico deve ser maior que 0% e no máximo 100%');row.percentage=p;row.fixedValue=null;}
      row.name=text(merged.name);row.type=type;row.participantPartyType=participant.partyType;row.participantPartyId=participant.partyId;row.basisType=basisType;row.deductions=[...new Set((merged.deductions||[]).map(text).filter(Boolean))];row.effectiveFrom=isoDate(merged.effectiveFrom);row.effectiveUntil=isoDate(merged.effectiveUntil);if(row.effectiveFrom&&row.effectiveUntil&&dateBefore(row.effectiveUntil,row.effectiveFrom))throw new Error('Vigência da regra econômica inválida');row.status=text(merged.status||'active')||'active';row.metadata={...(row.metadata||{}),...(input.metadata||{})};row.updatedAt=now();row.updatedBy=actor()||null;history('economic_rule.updated','version',row.contractVersionId,before,row);return row;
    }

    function companyValue(field){const company=companyProvider()||{};return text(company[field]);}
    function partyDisplay(type,id){const entity=partyService().getEntity(type,id);return entity?(type==='person'?entity.fullName:(entity.legalName||entity.tradeName||'')):'';}
    function partyDocument(type,id){const doc=type==='person'?partyService().documentFor('person',id,'cpf'):partyService().documentFor('organization',id,'cnpj');return text(doc?.value);}
    function referenceName(type,id){if(!id)return '';const ref=resolveReference(type,id);return text(ref?.name||ref?.title||ref?.legalName||ref?.tradeName);}
    function resolveVariableValue(variable,contract,version){
      switch(variable.resolver){
        case 'company.legalName':return companyValue('legalName');
        case 'company.cnpj':return companyValue('cnpj');
        case 'company.address':return companyValue('address');
        case 'customer.name':return contract.customerPartyId?partyDisplay(contract.customerPartyType,contract.customerPartyId):'';
        case 'customer.document':return contract.customerPartyId?partyDocument(contract.customerPartyType,contract.customerPartyId):'';
        case 'contract.number':return contract.number;
        case 'contract.referenceValue':return version.referenceValue==null?'':String(version.referenceValue);
        case 'contract.startDate':return contract.startDate||version.effectiveFrom||'';
        case 'contract.endDate':return contract.endDate||version.effectiveUntil||'';
        case 'reference.product':return referenceName('product',contract.productId);
        case 'reference.service':return referenceName('service',contract.serviceId);
        case 'reference.business_unit':return referenceName('business_unit',contract.businessUnitId);
        default:return '';
      }
    }
    function resolveVariables(versionId){
      const version=getVersion(versionId);if(!version)throw new Error('Versão não encontrada');const contract=getContract(version.contractId);if(!contract)throw new Error('Contrato não encontrado');const values={},unresolved=[];
      for(const variable of data.variables.filter((x)=>x.status==='active')){const value=resolveVariableValue(variable,contract,version);values[variable.key]=value;if(variable.required&&!text(value))unresolved.push(variable.key);}
      history('variables.resolved','version',versionId,null,{keys:Object.keys(values),unresolved});return {values,unresolved};
    }
    function renderVariables(content,values){return String(content??'').replace(/\{\{\s*([A-Z0-9_.]+)\s*\}\}/g,(match,key)=>{if(text(values[key]))return String(values[key]);return `Variável pendente: {{${key}}}`;});}

    function validationIssues(versionId,{forApproval=false}={}){
      const version=getVersion(versionId);if(!version)return ['version_not_found'];const contract=getContract(version.contractId);if(!contract)return ['contract_not_found'];const issues=[];
      if(!partiesFor(versionId).length)issues.push('missing_parties');
      for(const p of partiesFor(versionId)){if(!partyService().getEntity(p.partyType,p.partyId))issues.push(`invalid_party:${p.id}`);if(p.signatory&&p.signatoryPersonId){try{assertSignatory(p.partyType,p.partyId,p.signatoryPersonId);}catch(_){issues.push(`invalid_signatory:${p.id}`);}}}
      for(const r of rulesFor(versionId)){if(!partyService().getEntity(r.participantPartyType,r.participantPartyId))issues.push(`invalid_economic_participant:${r.id}`);if(!BASIS_TYPES.includes(r.basisType))issues.push(`invalid_basis:${r.id}`);if(r.type==='percentage'&&(!(Number.isFinite(r.percentage))||r.percentage<=0||r.percentage>100))issues.push(`invalid_percentage:${r.id}`);}
      if(forApproval){const resolved=resolveVariables(versionId);for(const key of resolved.unresolved)issues.push(`unresolved_variable:${key}`);if(contract.productId&&!resolveReference('product',contract.productId))issues.push('invalid_product_reference');if(contract.serviceId&&!resolveReference('service',contract.serviceId))issues.push('invalid_service_reference');if(contract.businessUnitId&&!resolveReference('business_unit',contract.businessUnitId))issues.push('invalid_business_unit_reference');}
      return [...new Set(issues)];
    }
    function buildSnapshot(versionId){
      const version=getVersion(versionId),contract=version&&getContract(version.contractId);if(!version||!contract)throw new Error('Contrato/versão não encontrados');const resolved=resolveVariables(versionId),company=clone(companyProvider()||{});
      return {capturedAt:now(),contract:{id:contract.id,number:contract.number,name:contract.name,type:contract.type,category:contract.category,startDate:contract.startDate,endDate:contract.endDate,currency:version.currency,referenceValue:version.referenceValue,productId:contract.productId,serviceId:contract.serviceId,businessUnitId:contract.businessUnitId},version:{id:version.id,versionNumber:version.versionNumber,title:version.title,effectiveFrom:version.effectiveFrom,effectiveUntil:version.effectiveUntil,content:version.content},company,parties:partiesFor(versionId).map((p)=>({...clone(p),identity:partySnapshot(p.partyType,p.partyId),signatoryIdentity:p.signatoryPersonId?partySnapshot('person',p.signatoryPersonId):null})),clauses:clone(clausesFor(versionId)),economicRules:clone(rulesFor(versionId)),variables:clone(resolved.values),unresolvedVariables:clone(resolved.unresolved),renderedContent:renderVariables(version.content,resolved.values)};
    }
    function detectVersionConflicts(versionId){
      const version=getVersion(versionId);if(!version)return [];const conflicts=[];
      for(const other of versionsFor(version.contractId)){
        if(other.id===version.id||!['approved','signed'].includes(other.status))continue;
        const explicit=version.supersedesVersionId===other.id||other.supersedesVersionId===version.id;if(explicit)continue;
        if(overlaps(version.effectiveFrom,version.effectiveUntil,other.effectiveFrom,other.effectiveUntil))conflicts.push({type:'version_overlap',versionId:version.id,otherVersionId:other.id});
      }
      return conflicts;
    }
    function sendVersionToReview(versionId){const row=assertVersionDraft(versionId),issues=validationIssues(versionId);if(issues.some((x)=>x==='missing_parties'||x.startsWith('invalid_')))throw new Error(`Versão possui inconsistências: ${issues.join(', ')}`);const before=clone(row);row.status='review';row.submittedAt=now();row.submittedBy=actor()||null;row.updatedAt=now();row.updatedBy=actor()||null;history('version.sent_to_review','version',versionId,before,row);return row;}
    function rejectVersion(versionId,reason=''){const row=getVersion(versionId);if(!row||row.status!=='review')throw new Error('Somente versão em Revisão pode ser rejeitada');const before=clone(row);row.status='rejected';row.rejectedAt=now();row.rejectedBy=actor()||null;row.rejectionReason=text(reason)||'Sem motivo informado';data.approvals.push({id:idFactory('approval'),contractVersionId:row.id,action:'rejected',at:now(),actorId:actor()||null,reason:row.rejectionReason,versionNumber:row.versionNumber});history('version.rejected','version',versionId,before,row,{reason:row.rejectionReason});return row;}
    function approveVersion(versionId){
      const row=getVersion(versionId);if(!row||row.status!=='review')throw new Error('Somente versão em Revisão pode ser aprovada');const issues=validationIssues(versionId,{forApproval:true}),conflicts=detectVersionConflicts(versionId);if(issues.length)throw new Error(`Aprovação bloqueada: ${issues.join(', ')}`);if(conflicts.length)throw new Error('Aprovação bloqueada por conflito de vigência entre versões');const before=clone(row);row.snapshot=buildSnapshot(versionId);row.status='approved';row.approvedAt=now();row.approvedBy=actor()||null;row.updatedAt=now();row.updatedBy=actor()||null;data.approvals.push({id:idFactory('approval'),contractVersionId:row.id,action:'approved',at:row.approvedAt,actorId:row.approvedBy,versionNumber:row.versionNumber});const contract=getContract(row.contractId);if(contract.status==='draft')contract.status='negotiation';contract.updatedAt=now();contract.updatedBy=actor()||null;
      if(row.supersedesVersionId){const previous=getVersion(row.supersedesVersionId);if(previous&&['approved','signed'].includes(previous.status)){previous.status='superseded';previous.supersededAt=now();previous.supersededByVersionId=row.id;}}
      history('version.approved','version',versionId,before,row);return row;
    }
    function returnVersionToDraft(versionId,reason=''){const row=getVersion(versionId);if(!row||row.status!=='review')throw new Error('Somente versão em Revisão pode voltar a Rascunho');const before=clone(row);row.status='draft';row.submittedAt=null;row.submittedBy=null;row.updatedAt=now();row.updatedBy=actor()||null;history('version.returned_to_draft','version',versionId,before,row,{reason:text(reason)});return row;}
    function addSignature(versionId,input={}){
      const version=getVersion(versionId);if(!version||!['approved','signed'].includes(version.status))throw new Error('Assinatura somente pode ser registrada em versão aprovada');const personId=text(input.signatoryPersonId);if(!partyService().getEntity('person',personId))throw new Error('Signatário canônico não encontrado');const contractual=partiesFor(versionId).some((p)=>p.signatoryPersonId===personId||p.partyType==='person'&&p.partyId===personId&&p.signatory);if(!contractual)throw new Error('Signatário não está definido nesta versão');const status=SIGNATURE_STATUSES.includes(input.status)?input.status:'manual_recorded';const row={id:input.id||idFactory('signature'),contractVersionId:versionId,signatoryPersonId:personId,status,provider:text(input.provider||'manual')||'manual',externalReference:text(input.externalReference),signedAt:status==='signed'||status==='manual_recorded'?(input.signedAt||now()):null,metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null};data.signatures.push(row);history('signature.recorded','version',versionId,null,row);return row;
    }
    function markVersionSigned(versionId){
      const row=getVersion(versionId);if(!row||row.status!=='approved')throw new Error('Somente versão aprovada pode ser marcada como assinada');const required=[...new Set(partiesFor(versionId).filter((p)=>p.signatory).map((p)=>p.signatoryPersonId||p.partyId).filter(Boolean))];const recorded=signaturesFor(versionId).filter((s)=>['manual_recorded','signed'].includes(s.status)).map((s)=>s.signatoryPersonId);const missing=required.filter((id)=>!recorded.includes(id));if(missing.length)throw new Error('Existem assinaturas pendentes');const before=clone(row);row.status='signed';row.signedAt=now();row.snapshot=buildSnapshot(versionId);const contract=getContract(row.contractId);contract.status='active';contract.activeVersionId=row.id;contract.updatedAt=now();contract.updatedBy=actor()||null;history('version.signed','version',versionId,before,row,{manualRegistry:true});return row;
    }

    function createTemplate(input={}){
      const row={id:input.id||idFactory('tpl'),name:text(input.name),category:text(input.category),type:text(input.type),status:'draft',activeVersionId:'',latestVersionId:'',createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null,metadata:clone(input.metadata||{})};if(!row.name)throw new Error('Template requer nome');data.templates.push(row);const version=createTemplateVersion(row.id,{content:input.content||'',header:input.header||'',footer:input.footer||'',variableKeys:input.variableKeys||[],partyDefinitions:input.partyDefinitions||[],signatoryDefinitions:input.signatoryDefinitions||[]});row.latestVersionId=version.id;history('template.created','template',row.id,null,row);return row;
    }
    function createTemplateVersion(templateId,input={}){const template=getTemplate(templateId);if(!template)throw new Error('Template não encontrado');const list=templateVersionsFor(templateId),row={id:input.id||idFactory('tplv'),templateId,versionNumber:list.length?Math.max(...list.map((x)=>x.versionNumber))+1:1,status:'draft',content:String(input.content??''),header:String(input.header??''),footer:String(input.footer??''),variableKeys:[...new Set((input.variableKeys||[]).map(text).filter(Boolean))],partyDefinitions:clone(input.partyDefinitions||[]),signatoryDefinitions:clone(input.signatoryDefinitions||[]),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null,activatedAt:null,activatedBy:null,supersededAt:null,metadata:clone(input.metadata||{})};for(const key of row.variableKeys)if(!getVariable(key))throw new Error(`Variável de Template não registrada: ${key}`);data.templateVersions.push(row);template.latestVersionId=row.id;template.updatedAt=now();template.updatedBy=actor()||null;history('template_version.created','template_version',row.id,null,row,{templateId});return row;}
    function updateTemplateVersion(versionId,input={}){const row=getTemplateVersion(versionId);if(!row)throw new Error('Versão de Template não encontrada');if(row.status!=='draft')throw new Error('Somente versão rascunho de Template pode ser editada');const before=clone(row);if('content'in input)row.content=String(input.content??'');if('header'in input)row.header=String(input.header??'');if('footer'in input)row.footer=String(input.footer??'');if('variableKeys'in input){const keys=[...new Set((input.variableKeys||[]).map(text).filter(Boolean))];for(const key of keys)if(!getVariable(key))throw new Error(`Variável de Template não registrada: ${key}`);row.variableKeys=keys;}if('partyDefinitions'in input)row.partyDefinitions=clone(input.partyDefinitions||[]);if('signatoryDefinitions'in input)row.signatoryDefinitions=clone(input.signatoryDefinitions||[]);row.updatedAt=now();row.updatedBy=actor()||null;history('template_version.updated','template_version',row.id,before,row);return row;}
    function activateTemplateVersion(versionId){const row=getTemplateVersion(versionId);if(!row||row.status!=='draft')throw new Error('Somente versão rascunho pode ser ativada');const template=getTemplate(row.templateId),previous=getTemplateVersion(template.activeVersionId);if(previous&&previous.status==='active'){previous.status='superseded';previous.supersededAt=now();}row.status='active';row.activatedAt=now();row.activatedBy=actor()||null;template.activeVersionId=row.id;template.status='active';template.updatedAt=now();template.updatedBy=actor()||null;history('template_version.activated','template_version',row.id,null,row);return row;}
    function duplicateTemplate(templateId){const source=getTemplate(templateId);if(!source)throw new Error('Template não encontrado');const version=getTemplateVersion(source.activeVersionId||source.latestVersionId);return createTemplate({name:`${source.name} (cópia)`,category:source.category,type:source.type,content:version?.content||'',header:version?.header||'',footer:version?.footer||'',variableKeys:version?.variableKeys||[],partyDefinitions:version?.partyDefinitions||[],signatoryDefinitions:version?.signatoryDefinitions||[],metadata:{duplicatedFrom:source.id}});}
    function archiveTemplate(templateId){const row=getTemplate(templateId);if(!row)throw new Error('Template não encontrado');const before=clone(row);row.status='archived';row.updatedAt=now();row.updatedBy=actor()||null;history('template.archived','template',row.id,before,row);return row;}

    function registerVariable(input={}){const key=text(input.key).replace(/^\{\{|\}\}$/g,'');if(!/^[A-Z0-9_]+(?:\.[A-Z0-9_]+)+$/.test(key))throw new Error('Chave de variável inválida');if(data.variables.some((x)=>x.key===key))throw new Error('Chave de variável já registrada');const row={id:input.id||idFactory('var'),key,label:text(input.label||key),description:text(input.description),scope:text(input.scope),valueType:text(input.valueType||'text')||'text',resolver:text(input.resolver),required:!!input.required,status:VARIABLE_STATUSES.includes(input.status)?input.status:'active',fallbackPolicy:text(input.fallbackPolicy||'block_if_required'),origin:text(input.origin||'Personalizada'),system:false,metadata:clone(input.metadata||{}),createdAt:now(),createdBy:actor()||null,updatedAt:now(),updatedBy:actor()||null};data.variables.push(row);history('variable.registered','variable',row.id,null,row);return row;}
    function buildPreview(versionId){const version=getVersion(versionId);if(!version)throw new Error('Versão não encontrada');const contract=getContract(version.contractId),resolved=resolveVariables(versionId),templateVersion=version.templateVersionId?getTemplateVersion(version.templateVersionId):null;return {contract:clone(contract),version:clone(version),header:templateVersion?.header||'',footer:templateVersion?.footer||'',content:renderVariables(version.content,resolved.values),clauses:clausesFor(versionId).map((c)=>({...clone(c),content:renderVariables(c.content,resolved.values)})),values:resolved.values,unresolved:resolved.unresolved,page:{size:'A4',widthMm:210,heightMm:297,marginMm:20},legalStatus:'internal_preview'};}

    function terminateContract(contractId,reason,date=''){const row=getContract(contractId);if(!row)throw new Error('Contrato não encontrado');if(['terminated','archived'].includes(row.status))throw new Error('Contrato já encerrado/arquivado');const before=clone(row);row.status='terminated';row.terminationDate=isoDate(date)||today();row.terminationReason=text(reason)||'Sem motivo informado';row.updatedAt=now();row.updatedBy=actor()||null;history('contract.terminated','contract',contractId,before,row,{reason:row.terminationReason});return row;}
    function suspendContract(contractId,reason=''){const row=getContract(contractId);if(!row||row.status!=='active')throw new Error('Somente contrato ativo pode ser suspenso');const before=clone(row);row.status='suspended';row.updatedAt=now();row.updatedBy=actor()||null;history('contract.suspended','contract',contractId,before,row,{reason:text(reason)});return row;}
    function refreshLifecycle(asOf=today()){
      for(const contract of data.contracts){if(contract.isDemo||!['active','suspended'].includes(contract.status))continue;if(contract.endDate&&contract.endDate<asOf&&(!contract.renewalDate||contract.renewalDate<asOf)){const before=clone(contract);contract.status='expired';contract.updatedAt=now();contract.updatedBy=actor()||null;history('contract.expired','contract',contract.id,before,contract,{asOf});}}
      return data.contracts;
    }

    function effectiveWindow(version){
      let from=version.effectiveFrom||'',until=version.effectiveUntil||'';
      if(version.status==='superseded'&&version.supersededByVersionId){const next=getVersion(version.supersededByVersionId);if(next?.effectiveFrom&&(!until||next.effectiveFrom<=until)){const d=new Date(`${next.effectiveFrom}T00:00:00Z`);d.setUTCDate(d.getUTCDate()-1);until=d.toISOString().slice(0,10);}}
      return {from,until};
    }
    function ruleApplies(rule,version,from,to){const vw=effectiveWindow(version),rf=rule.effectiveFrom||vw.from||'',ru=rule.effectiveUntil||vw.until||'';return overlaps(rf,ru,from,to);}
    function economicRulesFeed(filters={}){
      const from=isoDate(filters.from||filters.date),to=isoDate(filters.to||filters.date)||from,rows=[];
      for(const rule of data.economicRules){const version=getVersion(rule.contractVersionId),contract=version&&getContract(version.contractId);if(!version||!contract||contract.isDemo||rule.status==='inactive')continue;const legallyVisible=['approved','signed','superseded'].includes(version.status);if(!legallyVisible)continue;if(version.status==='superseded'&&!from&&!to&&!filters.includeHistorical)continue;if(from&&to&&!ruleApplies(rule,version,from,to))continue;if(filters.contractId&&contract.id!==filters.contractId)continue;if(filters.participantPartyType&&rule.participantPartyType!==filters.participantPartyType)continue;if(filters.participantPartyId&&rule.participantPartyId!==filters.participantPartyId)continue;
        rows.push({contractId:contract.id,contractNumber:contract.number,versionId:version.id,versionNumber:version.versionNumber,ruleId:rule.id,participantPartyType:rule.participantPartyType,participantPartyId:rule.participantPartyId,basisType:rule.basisType,type:rule.type,percentage:rule.percentage,fixedValue:rule.fixedValue,deductions:clone(rule.deductions),effectiveFrom:rule.effectiveFrom||version.effectiveFrom||'',effectiveUntil:rule.effectiveUntil||effectiveWindow(version).until||'',productId:rule.productId||contract.productId||'',serviceId:rule.serviceId||contract.serviceId||'',businessUnitId:rule.businessUnitId||contract.businessUnitId||'',currency:rule.currency||version.currency||contract.currency||'BRL'});
      }
      return clone(rows);
    }
    function resolveEconomicRuleForPeriod(input={}){
      const from=isoDate(input.from||input.date),to=isoDate(input.to||input.date)||from;if(!from)throw new Error('Período é obrigatório para resolver regra econômica');
      const matches=economicRulesFeed({from,to,includeHistorical:true,contractId:input.contractId||'',participantPartyType:input.participantPartyType||'',participantPartyId:input.participantPartyId||''}).filter((x)=>!input.basisType||x.basisType===input.basisType);
      if(!matches.length)return {status:'none',rules:[]};if(matches.length===1)return {status:'resolved',rule:matches[0],rules:matches};return {status:'conflict',rules:matches};
    }

    function queryContracts(filters={}){
      refreshLifecycle(filters.asOf||today());let rows=data.contracts.filter((x)=>filters.includeDemo||!x.isDemo);
      if(filters.status)rows=rows.filter((x)=>x.status===filters.status);if(filters.type)rows=rows.filter((x)=>x.type===filters.type);if(filters.category)rows=rows.filter((x)=>x.category===filters.category);if(filters.customerPartyId)rows=rows.filter((x)=>x.customerPartyId===filters.customerPartyId);if(filters.productId)rows=rows.filter((x)=>x.productId===filters.productId);if(filters.serviceId)rows=rows.filter((x)=>x.serviceId===filters.serviceId);if(filters.businessUnitId)rows=rows.filter((x)=>x.businessUnitId===filters.businessUnitId);if(filters.responsibleUserId)rows=rows.filter((x)=>x.ownerUserId===filters.responsibleUserId||x.responsibleUserIds.includes(filters.responsibleUserId));if(filters.from||filters.to)rows=rows.filter((x)=>overlaps(x.startDate,x.endDate,filters.from||'',filters.to||''));
      if(filters.partyId){const ids=new Set(data.parties.filter((p)=>p.partyId===filters.partyId).map((p)=>getVersion(p.contractVersionId)?.contractId).filter(Boolean));rows=rows.filter((x)=>ids.has(x.id));}
      if(filters.search){const q=fold(filters.search);rows=rows.filter((contract)=>{const latest=getVersion(contract.latestVersionId),partyNames=latest?partiesFor(latest.id).map((p)=>partyDisplay(p.partyType,p.partyId)).join(' '):'';return fold([contract.number,contract.name,contract.type,contract.category,partyNames,contract.productId,contract.serviceId,contract.ownerUserId].join(' ')).includes(q);});}
      rows.sort((a,b)=>String(b.updatedAt).localeCompare(String(a.updatedAt)));const limit=Math.min(50,Math.max(1,Number(filters.limit)||50)),page=Math.max(1,Number(filters.page)||1),total=rows.length;return {rows:clone(rows.slice((page-1)*limit,page*limit)),total,page,limit,pages:Math.max(1,Math.ceil(total/limit))};
    }

    function migrateLegacy(records=[]){
      if(data.metadata.legacyMigrated)return {migrated:0,skipped:data.metadata.legacySkipped.length};let migrated=0;
      for(const item of records||[]){if(!item||typeof item!=='object')continue;const explicit=item.entityType==='contract'||item.kind==='contract'||item.recordType==='contract'||item.isContract===true;if(!explicit){data.metadata.legacySkipped.push({sourceId:text(item.id),reason:'semantic_ambiguity'});continue;}if(item.isDemo!==true&&!(item.number&&item.name)){data.metadata.legacySkipped.push({sourceId:text(item.id),reason:'insufficient_contract_evidence'});continue;}try{const contract=createContract({number:item.number||'',name:item.name||item.title||'',type:item.type||'',category:item.category||'',startDate:item.startDate||'',endDate:item.endDate||'',currency:item.currency||'BRL',referenceValue:item.referenceValue,isDemo:!!item.isDemo,content:item.content||'',metadata:{legacySource:true,legacyId:text(item.id)}});data.legacyBindings.push({id:idFactory('legacybind'),source:'legacy.contract',legacyId:text(item.id),contractId:contract.id,createdAt:now()});migrated++;}catch(error){data.metadata.legacySkipped.push({sourceId:text(item.id),reason:text(error.message)});}}
      data.metadata.legacyMigrated=true;data.metadata.legacyMigratedAt=now();return {migrated,skipped:data.metadata.legacySkipped.length};
    }

    return {data,seedVariables,getContract,getVersion,getTemplate,getTemplateVersion,getVariable,versionsFor,partiesFor,clausesFor,rulesFor,signaturesFor,approvalsFor,templateVersionsFor,createContract,updateContract,createVersion,createNewVersion,updateVersion,addParty,removeParty,addClause,addEconomicRule,updateEconomicRule,resolveVariables,renderVariables,validationIssues,buildSnapshot,detectVersionConflicts,sendVersionToReview,returnVersionToDraft,rejectVersion,approveVersion,addSignature,markVersionSigned,createTemplate,createTemplateVersion,updateTemplateVersion,activateTemplateVersion,duplicateTemplate,archiveTemplate,registerVariable,buildPreview,terminateContract,suspendContract,refreshLifecycle,economicRulesFeed,resolveEconomicRuleForPeriod,queryContracts,migrateLegacy,assertUniqueNumber,nextInternalNumber,effectiveWindow};
  }

  return {SCHEMA_VERSION,CONTRACT_STATUSES,VERSION_STATUSES,TEMPLATE_STATUSES,TEMPLATE_VERSION_STATUSES,PARTY_TYPES,ECONOMIC_RULE_TYPES,BASIS_TYPES,SIGNATURE_STATUSES,VARIABLE_STATUSES,BUILTIN_VARIABLES,createState,ensureState,createService,clone,text,fold,num,isoDate,overlaps};
});
