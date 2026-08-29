(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenPartyCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const ROLE_ALIASES={
    cliente:'customer',client:'customer',customer:'customer',lead:'lead',prospect:'prospect',
    fornecedor:'supplier',supplier:'supplier',vendor:'supplier',parceiro:'partner',partner:'partner',
    'prestador de servicos':'service_provider','prestador de serviços':'service_provider',service_provider:'service_provider',
    beneficiario:'beneficiary','beneficiário':'beneficiary',beneficiary:'beneficiary',
    'participante economico':'economic_participant','participante econômico':'economic_participant',economic_participant:'economic_participant',
    'parte contratual':'contractual_party',contractual_party:'contractual_party',
    'contato de empresa':'organization_contact',organization_contact:'organization_contact',
    responsavel:'responsible','responsável':'responsible',responsible:'responsible',crm_contact:'crm_contact'
  };

  const clone=(v)=>v==null?v:JSON.parse(JSON.stringify(v));
  const normalizeWhitespace=(v)=>String(v??'').trim().replace(/\s+/g,' ');
  const fold=(v)=>normalizeWhitespace(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const digits=(v)=>String(v??'').replace(/\D/g,'');
  const normalizeEmail=(v)=>normalizeWhitespace(v).toLowerCase();
  const normalizePhone=(v)=>digits(v);
  const normalizeDocument=(v)=>String(v??'').replace(/[^0-9A-Za-z]/g,'').toUpperCase();
  function normalizeDomain(value){
    const raw=normalizeWhitespace(value).toLowerCase(); if(!raw)return '';
    const candidate=raw.includes('@')?raw.split('@').pop():raw;
    try{return new URL(candidate.includes('://')?candidate:`https://${candidate}`).hostname.replace(/^www\./,'');}
    catch{return candidate.replace(/^https?:\/\//,'').split('/')[0].replace(/^www\./,'');}
  }
  const normalizeRole=(v)=>{const key=fold(v);return ROLE_ALIASES[key]||key.replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');};
  const personName=(x)=>normalizeWhitespace(x.fullName||[x.firstName,x.lastName].filter(Boolean).join(' ')||x.name);
  const organizationName=(x)=>normalizeWhitespace(x.legalName||x.tradeName||x.name);

  function validateCPF(value){
    const cpf=digits(value); if(cpf.length!==11||/^(\d)\1{10}$/.test(cpf))return false;
    const calc=(len)=>{let sum=0;for(let i=0;i<len;i++)sum+=Number(cpf[i])*(len+1-i);const mod=(sum*10)%11;return mod===10?0:mod;};
    return calc(9)===Number(cpf[9])&&calc(10)===Number(cpf[10]);
  }
  function validateCNPJ(value){
    const cnpj=digits(value); if(cnpj.length!==14||/^(\d)\1{13}$/.test(cnpj))return false;
    const calc=(weights)=>{let sum=0;for(let i=0;i<weights.length;i++)sum+=Number(cnpj[i])*weights[i];const mod=sum%11;return mod<2?0:11-mod;};
    return calc([5,4,3,2,9,8,7,6,5,4,3,2])===Number(cnpj[12])&&calc([6,5,4,3,2,9,8,7,6,5,4,3,2])===Number(cnpj[13]);
  }
  function validateDocument(type,value){
    const normalized=normalizeDocument(value); if(!normalized)return true;
    const t=fold(type); if(t==='cpf')return validateCPF(normalized); if(t==='cnpj')return validateCNPJ(normalized); return true;
  }

  function createState(){return {schemaVersion:SCHEMA_VERSION,people:[],organizations:[],roles:[],personOrganizationRelationships:[],contactPoints:[],addresses:[],documents:[],userLinks:[],history:[],legacyBindings:[],potentialDuplicates:[],metadata:{}};}
  function ensureState(input){
    const target=input&&typeof input==='object'?input:createState(),template=createState();
    for(const [key,value] of Object.entries(template)){if(Array.isArray(value)&&!Array.isArray(target[key]))target[key]=[];}
    if(!target.metadata||typeof target.metadata!=='object')target.metadata={}; target.schemaVersion=SCHEMA_VERSION; return target;
  }
  function defaultIdFactory(prefix){
    const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
    return `${prefix}_${token}`;
  }

  function createService(store,options={}){
    const data=ensureState(store),idFactory=options.idFactory||defaultIdFactory,now=options.now||(()=>new Date().toISOString()),actor=options.actorProvider||(()=>null);
    const listFor=(type)=>type==='person'?data.people:type==='organization'?data.organizations:null;
    const getEntity=(type,id)=>listFor(type)?.find((x)=>x.id===id)||null;
    const contactsFor=(type,id)=>data.contactPoints.filter((x)=>x.entityType===type&&x.entityId===id);
    const primaryContact=(type,id,kind)=>contactsFor(type,id).find((x)=>x.type===kind&&x.primary)||contactsFor(type,id).find((x)=>x.type===kind)||null;
    const primaryAddress=(type,id)=>data.addresses.find((x)=>x.entityType===type&&x.entityId===id&&x.primary)||data.addresses.find((x)=>x.entityType===type&&x.entityId===id)||null;
    const documentFor=(type,id,kind)=>data.documents.find((x)=>x.entityType===type&&x.entityId===id&&fold(x.type)===fold(kind));
    const audit=(action,type,id,before,after,metadata={})=>data.history.push({id:idFactory('hist'),action,entityType:type,entityId:id,at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)});
    const baseFields=(input,existing)=>({status:normalizeWhitespace(input.status||existing?.status||'active')||'active',tags:Array.from(new Set([...(existing?.tags||[]),...(Array.isArray(input.tags)?input.tags:[])])),metadata:{...(existing?.metadata||{}),...(input.metadata||{})},createdAt:existing?.createdAt||now(),updatedAt:now(),createdBy:existing?.createdBy||actor()||null,updatedBy:actor()||null});

    function detectPotentialDuplicates(type,input,excludeId=''){
      const results=[];
      if(type==='person'){
        const name=fold(personName(input)),cpf=normalizeDocument(input.cpf||input.document),email=normalizeEmail(input.email),phone=normalizePhone(input.phone);
        for(const p of data.people){if(p.id===excludeId)continue;const reasons=[];if(cpf&&documentFor('person',p.id,'cpf')?.normalizedValue===cpf)reasons.push('cpf');if(email&&primaryContact('person',p.id,'email')?.normalizedValue===email)reasons.push('email');if(phone&&primaryContact('person',p.id,'phone')?.normalizedValue===phone)reasons.push('phone');if(name&&fold(p.fullName)===name)reasons.push('exact_name');if(reasons.length)results.push({entityType:type,entityId:p.id,reasons,confidence:reasons.includes('cpf')||((reasons.includes('email')||reasons.includes('phone'))&&reasons.includes('exact_name'))?'strong':'possible'});}
      }else if(type==='organization'){
        const legal=fold(input.legalName||input.name),trade=fold(input.tradeName),cnpj=normalizeDocument(input.cnpj||input.document),domain=normalizeDomain(input.site||input.email);
        for(const o of data.organizations){if(o.id===excludeId)continue;const reasons=[];if(cnpj&&documentFor('organization',o.id,'cnpj')?.normalizedValue===cnpj)reasons.push('cnpj');if(legal&&fold(o.legalName)===legal)reasons.push('exact_legal_name');if(trade&&fold(o.tradeName)===trade)reasons.push('exact_trade_name');if(domain&&primaryContact('organization',o.id,'site')?.normalizedValue===domain)reasons.push('domain');if(reasons.length)results.push({entityType:type,entityId:o.id,reasons,confidence:reasons.includes('cnpj')||(reasons.includes('domain')&&(reasons.includes('exact_legal_name')||reasons.includes('exact_trade_name')))?'strong':'possible'});}
      }
      return results;
    }
    function findStrongMatch(type,input,opts={}){
      const strong=detectPotentialDuplicates(type,input).filter((x)=>x.confidence==='strong'); if(strong.length===1)return getEntity(type,strong[0].entityId);
      if(type==='organization'&&opts.allowExactNameMatch){const name=fold(input.legalName||input.tradeName||input.name);const exact=data.organizations.filter((o)=>name&&(fold(o.legalName)===name||fold(o.tradeName)===name));if(exact.length===1)return exact[0];}
      return null;
    }

    function preflightDocuments(type,entityId,input,opts={}){
      const docs=[];
      if(type==='person'&&(input.cpf||input.document))docs.push({type:'cpf',value:input.cpf||input.document});
      if(type==='organization'&&(input.cnpj||input.document))docs.push({type:'cnpj',value:input.cnpj||input.document});
      if(Array.isArray(input.documents))docs.push(...input.documents);
      for(const doc of docs){if(!doc?.value)continue;const kind=fold(doc.type||'other'),normalized=normalizeDocument(doc.value);if(!normalized)continue;if(!validateDocument(kind,normalized)&&!opts.allowInvalidLegacy){const e=new Error(`Documento ${kind.toUpperCase()} inválido`);e.code='INVALID_DOCUMENT';throw e;}const collision=data.documents.find((d)=>d.type===kind&&d.normalizedValue===normalized&&(d.entityType!==type||d.entityId!==entityId));if(collision){const e=new Error(`Documento ${kind.toUpperCase()} já vinculado a outro cadastro`);e.code='DUPLICATE_DOCUMENT';throw e;}}
    }
    function addDocument(type,id,input,opts={}){
      if(!input?.value)return null; const kind=fold(input.type||'other'),normalized=normalizeDocument(input.value); if(!normalized)return null; preflightDocuments(type,id,{documents:[input]},opts);
      let row=data.documents.find((d)=>d.entityType===type&&d.entityId===id&&d.type===kind);const valid=validateDocument(kind,normalized),payload={type:kind,country:input.country||'BR',value:String(input.value),normalizedValue:normalized,validationStatus:valid?'valid':'legacy-unverified',metadata:{...(row?.metadata||{}),...(input.metadata||{})},updatedAt:now()};
      if(row)Object.assign(row,payload);else{row={id:idFactory('doc'),entityType:type,entityId:id,createdAt:now(),...payload};data.documents.push(row);} return row;
    }
    function addContactPoint(type,id,input){
      if(!input?.value)return null;const kind=fold(input.type),normalize=kind==='email'?normalizeEmail:(kind==='phone'||kind==='whatsapp')?normalizePhone:kind==='site'?normalizeDomain:normalizeWhitespace,normalized=normalize(input.value);if(!normalized)return null;
      let row=data.contactPoints.find((x)=>x.entityType===type&&x.entityId===id&&x.type===kind&&x.normalizedValue===normalized);if(!row){row={id:idFactory('cp'),entityType:type,entityId:id,type:kind,value:String(input.value),normalizedValue:normalized,label:input.label||'',primary:!!input.primary,metadata:clone(input.metadata||{}),createdAt:now(),updatedAt:now()};data.contactPoints.push(row);}else{row.value=String(input.value);row.primary=row.primary||!!input.primary;row.updatedAt=now();}
      if(row.primary)data.contactPoints.forEach((x)=>{if(x!==row&&x.entityType===type&&x.entityId===id&&x.type===kind)x.primary=false;});return row;
    }
    function setPrimaryAddress(type,id,input){
      if(!input)return null;const keys=['line1','number','complement','district','city','region','postalCode','country'];if(!keys.some((k)=>normalizeWhitespace(input[k])))return null;let row=primaryAddress(type,id);const payload={line1:normalizeWhitespace(input.line1),number:normalizeWhitespace(input.number),complement:normalizeWhitespace(input.complement),district:normalizeWhitespace(input.district),city:normalizeWhitespace(input.city),region:normalizeWhitespace(input.region),postalCode:normalizeWhitespace(input.postalCode),country:normalizeWhitespace(input.country||'BR')||'BR',primary:true,metadata:{...(row?.metadata||{}),...(input.metadata||{})},updatedAt:now()};if(row)Object.assign(row,payload);else{row={id:idFactory('addr'),entityType:type,entityId:id,createdAt:now(),...payload};data.addresses.push(row);}return row;
    }
    function syncDetails(type,id,input,opts={}){
      if(input.email)addContactPoint(type,id,{type:'email',value:input.email,primary:true});if(input.phone)addContactPoint(type,id,{type:'phone',value:input.phone,primary:true});if(input.whatsapp)addContactPoint(type,id,{type:'whatsapp',value:input.whatsapp,primary:true});if(input.site)addContactPoint(type,id,{type:'site',value:input.site,primary:true});if(input.address)setPrimaryAddress(type,id,input.address);
      if(type==='person'&&(input.cpf||input.document))addDocument(type,id,{type:'cpf',value:input.cpf||input.document,country:input.documentCountry||'BR'},opts);if(type==='organization'&&(input.cnpj||input.document))addDocument(type,id,{type:'cnpj',value:input.cnpj||input.document,country:input.documentCountry||'BR'},opts);if(Array.isArray(input.documents))input.documents.forEach((d)=>addDocument(type,id,d,opts));
    }

    function createPerson(input={},opts={}){const fullName=personName(input);if(!fullName)throw new Error('Pessoa requer nome');const match=findStrongMatch('person',input,opts);if(match){updatePerson(match.id,input,opts);return match;}preflightDocuments('person','',input,opts);const row={id:input.id||idFactory('per'),firstName:normalizeWhitespace(input.firstName),lastName:normalizeWhitespace(input.lastName),fullName,status:'active',tags:[],metadata:{},...baseFields(input)};data.people.push(row);syncDetails('person',row.id,input,opts);audit('person.created','person',row.id,null,row);const weak=detectPotentialDuplicates('person',input,row.id).filter((x)=>x.confidence==='possible');data.potentialDuplicates.push(...weak.map((x)=>({...x,candidateId:row.id,detectedAt:now()})));return row;}
    function updatePerson(id,input={},opts={}){const row=getEntity('person',id);if(!row)throw new Error('Pessoa não encontrada');preflightDocuments('person',id,input,opts);const before=clone(row),name=personName(input);if(name)row.fullName=name;if('firstName'in input)row.firstName=normalizeWhitespace(input.firstName);if('lastName'in input)row.lastName=normalizeWhitespace(input.lastName);Object.assign(row,baseFields(input,row));syncDetails('person',id,input,opts);audit('person.updated','person',id,before,row);return row;}
    function createOrganization(input={},opts={}){const legalName=organizationName(input);if(!legalName)throw new Error('Organização requer nome');const match=findStrongMatch('organization',input,opts);if(match){updateOrganization(match.id,input,opts);return match;}preflightDocuments('organization','',input,opts);const row={id:input.id||idFactory('org'),legalName,tradeName:normalizeWhitespace(input.tradeName),organizationType:normalizeWhitespace(input.organizationType||input.type),segment:normalizeWhitespace(input.segment),status:'active',tags:[],metadata:{},...baseFields(input)};data.organizations.push(row);syncDetails('organization',row.id,input,opts);audit('organization.created','organization',row.id,null,row);const weak=detectPotentialDuplicates('organization',input,row.id).filter((x)=>x.confidence==='possible');data.potentialDuplicates.push(...weak.map((x)=>({...x,candidateId:row.id,detectedAt:now()})));return row;}
    function updateOrganization(id,input={},opts={}){const row=getEntity('organization',id);if(!row)throw new Error('Organização não encontrada');preflightDocuments('organization',id,input,opts);const before=clone(row),name=normalizeWhitespace(input.legalName||input.name);if(name)row.legalName=name;if('tradeName'in input)row.tradeName=normalizeWhitespace(input.tradeName);if('organizationType'in input||'type'in input)row.organizationType=normalizeWhitespace(input.organizationType||input.type);if('segment'in input)row.segment=normalizeWhitespace(input.segment);Object.assign(row,baseFields(input,row));syncDetails('organization',id,input,opts);audit('organization.updated','organization',id,before,row);return row;}

    function assignRole(type,id,role,metadata={}){if(!getEntity(type,id))throw new Error('Entidade não encontrada');const normalized=normalizeRole(role);if(!normalized)throw new Error('Papel inválido');let row=data.roles.find((x)=>x.entityType===type&&x.entityId===id&&x.role===normalized&&x.status!=='inactive');if(row){row.metadata={...(row.metadata||{}),...metadata};row.updatedAt=now();return row;}row={id:idFactory('role'),entityType:type,entityId:id,role:normalized,status:'active',metadata:clone(metadata),createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null};data.roles.push(row);audit('role.assigned',type,id,null,row,{role:normalized});return row;}
    function removeRole(type,id,role){const normalized=normalizeRole(role),row=data.roles.find((x)=>x.entityType===type&&x.entityId===id&&x.role===normalized&&x.status!=='inactive');if(!row)return false;const before=clone(row);row.status='inactive';row.updatedAt=now();audit('role.removed',type,id,before,row,{role:normalized});return true;}
    const getRoles=(type,id)=>data.roles.filter((x)=>x.entityType===type&&x.entityId===id&&x.status!=='inactive');
    function linkPersonOrganization(personId,organizationId,input={}){if(!getEntity('person',personId)||!getEntity('organization',organizationId))throw new Error('Pessoa ou organização não encontrada');const relationshipType=normalizeRole(input.relationshipType||'organization_contact');let row=data.personOrganizationRelationships.find((x)=>x.personId===personId&&x.organizationId===organizationId&&x.relationshipType===relationshipType&&x.status!=='inactive');const payload={positionTitle:normalizeWhitespace(input.positionTitle),department:normalizeWhitespace(input.department),primary:!!input.primary,financialContact:!!input.financialContact,legalContact:!!input.legalContact,notes:normalizeWhitespace(input.notes),status:normalizeWhitespace(input.status||'active')||'active',metadata:{...(row?.metadata||{}),...(input.metadata||{})},updatedAt:now(),updatedBy:actor()||null};if(row){Object.assign(row,payload);return row;}row={id:idFactory('rel'),personId,organizationId,relationshipType,createdAt:now(),createdBy:actor()||null,...payload};data.personOrganizationRelationships.push(row);audit('relationship.created','person',personId,null,row,{organizationId});return row;}
    const getOrganizationContacts=(organizationId)=>data.personOrganizationRelationships.filter((x)=>x.organizationId===organizationId&&x.status!=='inactive').map((relationship)=>({relationship,person:getEntity('person',relationship.personId)})).filter((x)=>x.person);
    function linkUser(personId,userId,metadata={}){if(!getEntity('person',personId))throw new Error('Pessoa não encontrada');if(!userId)throw new Error('userId obrigatório');let row=data.userLinks.find((x)=>x.personId===personId&&x.userId===userId&&x.status!=='inactive');if(row)return row;row={id:idFactory('usrlnk'),personId,userId,status:'active',metadata:clone(metadata),createdAt:now(),updatedAt:now()};data.userLinks.push(row);audit('user.linked','person',personId,null,row,{userId});return row;}

    return {data,getEntity,createPerson,updatePerson,createOrganization,updateOrganization,assignRole,removeRole,getRoles,linkPersonOrganization,getOrganizationContacts,linkUser,addDocument,addContactPoint,setPrimaryAddress,detectPotentialDuplicates,findStrongMatch,primaryContact,primaryAddress,documentFor,preflightDocuments};
  }

  return {SCHEMA_VERSION,ROLE_ALIASES,createState,ensureState,createService,normalizeWhitespace,fold,digits,normalizeEmail,normalizePhone,normalizeDocument,normalizeDomain,normalizeRole,validateCPF,validateCNPJ,validateDocument};
});
