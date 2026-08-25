(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenPartyCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const ROLE_ALIASES={
    cliente:'customer',client:'customer',customer:'customer',
    lead:'lead',prospect:'prospect',
    fornecedor:'supplier',supplier:'supplier',vendor:'supplier',
    parceiro:'partner',partner:'partner',
    'prestador de servicos':'service_provider','prestador de serviços':'service_provider',service_provider:'service_provider',
    beneficiario:'beneficiary','beneficiário':'beneficiary',beneficiary:'beneficiary',
    'participante economico':'economic_participant','participante econômico':'economic_participant',economic_participant:'economic_participant',
    'parte contratual':'contractual_party',contractual_party:'contractual_party',
    'contato de empresa':'organization_contact',organization_contact:'organization_contact',
    responsavel:'responsible','responsável':'responsible',responsible:'responsible',
    crm_contact:'crm_contact'
  };

  function nowIso(){return new Date().toISOString();}
  function clone(value){return value==null?value:JSON.parse(JSON.stringify(value));}
  function normalizeWhitespace(value){return String(value??'').trim().replace(/\s+/g,' ');}
  function fold(value){return normalizeWhitespace(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
  function digits(value){return String(value??'').replace(/\D/g,'');}
  function normalizeEmail(value){return normalizeWhitespace(value).toLowerCase();}
  function normalizePhone(value){return digits(value);}
  function normalizeDocument(value){return String(value??'').replace(/[^0-9A-Za-z]/g,'').toUpperCase();}
  function normalizeDomain(value){
    const raw=normalizeWhitespace(value).toLowerCase();
    if(!raw)return '';
    const candidate=raw.includes('@')?raw.split('@').pop():raw;
    try{return new URL(candidate.includes('://')?candidate:`https://${candidate}`).hostname.replace(/^www\./,'');}
    catch{return candidate.replace(/^https?:\/\//,'').split('/')[0].replace(/^www\./,'');}
  }
  function normalizeRole(value){const key=fold(value).replace(/\s+/g,' ');return ROLE_ALIASES[key]||key.replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');}
  function personDisplayName(input){return normalizeWhitespace(input.fullName||[input.firstName,input.lastName].filter(Boolean).join(' ')||input.name);}
  function organizationDisplayName(input){return normalizeWhitespace(input.legalName||input.tradeName||input.name);}

  function validateCPF(value){
    const cpf=digits(value);
    if(cpf.length!==11||/^(\d)\1{10}$/.test(cpf))return false;
    const calc=(len)=>{let sum=0;for(let i=0;i<len;i++)sum+=Number(cpf[i])*(len+1-i);const mod=(sum*10)%11;return mod===10?0:mod;};
    return calc(9)===Number(cpf[9])&&calc(10)===Number(cpf[10]);
  }
  function validateCNPJ(value){
    const cnpj=digits(value);
    if(cnpj.length!==14||/^(\d)\1{13}$/.test(cnpj))return false;
    const calc=(base,weights)=>{let sum=0;for(let i=0;i<weights.length;i++)sum+=Number(base[i])*weights[i];const mod=sum%11;return mod<2?0:11-mod;};
    const d1=calc(cnpj,[5,4,3,2,9,8,7,6,5,4,3,2]);
    const d2=calc(cnpj,[6,5,4,3,2,9,8,7,6,5,4,3,2]);
    return d1===Number(cnpj[12])&&d2===Number(cnpj[13]);
  }
  function validateDocument(type,value){
    const t=fold(type);
    if(!normalizeDocument(value))return true;
    if(t==='cpf')return validateCPF(value);
    if(t==='cnpj')return validateCNPJ(value);
    return true;
  }

  function createState(){return {schemaVersion:SCHEMA_VERSION,people:[],organizations:[],roles:[],personOrganizationRelationships:[],contactPoints:[],addresses:[],documents:[],userLinks:[],history:[],legacyBindings:[],potentialDuplicates:[],metadata:{}};}
  function ensureState(store){
    const target=store&&typeof store==='object'?store:createState();
    const template=createState();
    for(const [key,value] of Object.entries(template)){
      if(Array.isArray(value)&&!Array.isArray(target[key]))target[key]=[];
      if(key==='metadata'&&(!target.metadata||typeof target.metadata!=='object'))target.metadata={};
    }
    target.schemaVersion=SCHEMA_VERSION;
    return target;
  }

  function defaultIdFactory(prefix){
    const uuid=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
    return `${prefix}_${uuid}`;
  }

  function createService(store,options={}){
    const data=ensureState(store);
    const idFactory=options.idFactory||defaultIdFactory;
    const actorProvider=options.actorProvider||(()=>null);
    const timestamp=options.now||nowIso;

    const entityList=(entityType)=>entityType==='person'?data.people:entityType==='organization'?data.organizations:null;
    const getEntity=(entityType,id)=>entityList(entityType)?.find((row)=>row.id===id)||null;
    const audit=(action,entityType,entityId,before,after,metadata={})=>{
      data.history.push({id:idFactory('hist'),action,entityType,entityId,at:timestamp(),actorId:actorProvider()||null,before:clone(before),after:clone(after),metadata:clone(metadata)});
    };
    const baseFields=(input,existing)=>({
      status:normalizeWhitespace(input.status||existing?.status||'active')||'active',
      tags:Array.from(new Set([...(existing?.tags||[]),...(Array.isArray(input.tags)?input.tags:[])])),
      metadata:{...(existing?.metadata||{}),...(input.metadata||{})},
      createdAt:existing?.createdAt||timestamp(),updatedAt:timestamp(),createdBy:existing?.createdBy||actorProvider()||null,updatedBy:actorProvider()||null
    });
    const documentFor=(entityType,entityId,type)=>data.documents.find((d)=>d.entityType===entityType&&d.entityId===entityId&&fold(d.type)===fold(type));
    const contactsFor=(entityType,entityId)=>data.contactPoints.filter((c)=>c.entityType===entityType&&c.entityId===entityId);
    const primaryContact=(entityType,entityId,type)=>contactsFor(entityType,entityId).find((c)=>c.type===type&&c.primary)||contactsFor(entityType,entityId).find((c)=>c.type===type)||null;
    const primaryAddress=(entityType,entityId)=>data.addresses.find((a)=>a.entityType===entityType&&a.entityId===entityId&&a.primary)||data.addresses.find((a)=>a.entityType===entityType&&a.entityId===entityId)||null;

    function detectPotentialDuplicates(entityType,input,excludeId=''){
      const results=[];
      if(entityType==='person'){
        const name=fold(personDisplayName(input)),email=normalizeEmail(input.email),phone=normalizePhone(input.phone),cpf=normalizeDocument(input.cpf||input.document);
        for(const person of data.people){
          if(person.id===excludeId)continue;
          const reasons=[];
          const doc=documentFor('person',person.id,'cpf');
          const mail=primaryContact('person',person.id,'email');
          const tel=primaryContact('person',person.id,'phone');
          if(cpf&&doc?.normalizedValue===cpf)reasons.push('cpf');
          if(email&&mail?.normalizedValue===email)reasons.push('email');
          if(phone&&tel?.normalizedValue===phone)reasons.push('phone');
          if(name&&fold(person.fullName)===name)reasons.push('exact_name');
          if(reasons.length)results.push({entityType:'person',entityId:person.id,reasons,confidence:reasons.includes('cpf')?'strong':(reasons.includes('email')||reasons.includes('phone'))&&reasons.includes('exact_name')?'strong':'possible'});
        }
      }else if(entityType==='organization'){
        const legal=fold(input.legalName||input.name),trade=fold(input.tradeName),cnpj=normalizeDocument(input.cnpj||input.document),domain=normalizeDomain(input.site||input.email);
        for(const org of data.organizations){
          if(org.id===excludeId)continue;
          const reasons=[];
          const doc=documentFor('organization',org.id,'cnpj');
          const site=primaryContact('organization',org.id,'site');
          if(cnpj&&doc?.normalizedValue===cnpj)reasons.push('cnpj');
          if(legal&&fold(org.legalName)===legal)reasons.push('exact_legal_name');
          if(trade&&fold(org.tradeName)===trade)reasons.push('exact_trade_name');
          if(domain&&site?.normalizedValue===domain)reasons.push('domain');
          if(reasons.length)results.push({entityType:'organization',entityId:org.id,reasons,confidence:reasons.includes('cnpj')?'strong':reasons.includes('domain')&&(reasons.includes('exact_legal_name')||reasons.includes('exact_trade_name'))?'strong':'possible'});
        }
      }
      return results;
    }

    function findStrongMatch(entityType,input,options={}){
      const candidates=detectPotentialDuplicates(entityType,input);
      const strong=candidates.filter((c)=>c.confidence==='strong');
      if(strong.length===1)return getEntity(entityType,strong[0].entityId);
      if(entityType==='organization'&&options.allowExactNameMatch){
        const name=fold(input.legalName||input.tradeName||input.name);
        if(name){const exact=data.organizations.filter((o)=>fold(o.legalName)===name||fold(o.tradeName)===name);if(exact.length===1)return exact[0];}
      }
      return null;
    }

    function addDocument(entityType,entityId,input,opts={}){
      if(!input||!input.value)return null;
      const type=fold(input.type||'other');
      const normalizedValue=normalizeDocument(input.value);
      if(!normalizedValue)return null;
      const valid=validateDocument(type,normalizedValue);
      if(!valid&&!opts.allowInvalidLegacy){const error=new Error(`Documento ${type.toUpperCase()} inválido`);error.code='INVALID_DOCUMENT';throw error;}
      const collision=data.documents.find((d)=>d.type===type&&d.normalizedValue===normalizedValue&&(d.entityType!==entityType||d.entityId!==entityId));
      if(collision){const error=new Error(`Documento ${type.toUpperCase()} já vinculado a outro cadastro`);error.code='DUPLICATE_DOCUMENT';throw error;}
      let doc=data.documents.find((d)=>d.entityType===entityType&&d.entityId===entityId&&d.type===type);
      const payload={type,country:input.country||'BR',value:String(input.value),normalizedValue,validationStatus:valid?'valid':opts.allowInvalidLegacy?'legacy-unverified':'invalid',metadata:{...(doc?.metadata||{}),...(input.metadata||{})},updatedAt:timestamp()};
      if(doc){Object.assign(doc,payload);}else{doc={id:idFactory('doc'),entityType,entityId,createdAt:timestamp(),...payload};data.documents.push(doc);}
      return doc;
    }

    function addContactPoint(entityType,entityId,input){
      if(!input||!input.value)return null;
      const type=fold(input.type);
      const normalizer=type==='email'?normalizeEmail:(type==='phone'||type==='whatsapp')?normalizePhone:type==='site'?normalizeDomain:normalizeWhitespace;
      const normalizedValue=normalizer(input.value);
      if(!normalizedValue)return null;
      let item=data.contactPoints.find((c)=>c.entityType===entityType&&c.entityId===entityId&&c.type===type&&c.normalizedValue===normalizedValue);
      if(!item){item={id:idFactory('cp'),entityType,entityId,type,value:String(input.value),normalizedValue,label:input.label||'',primary:!!input.primary,metadata:clone(input.metadata||{}),createdAt:timestamp(),updatedAt:timestamp()};data.contactPoints.push(item);}else{item.value=String(input.value);item.primary=item.primary||!!input.primary;item.updatedAt=timestamp();}
      if(item.primary)data.contactPoints.forEach((c)=>{if(c!==item&&c.entityType===entityType&&c.entityId===entityId&&c.type===type)c.primary=false;});
      return item;
    }

    function setPrimaryAddress(entityType,entityId,input){
      if(!input)return null;
      const hasValue=['line1','number','complement','district','city','region','postalCode','country'].some((key)=>normalizeWhitespace(input[key]));
      if(!hasValue)return null;
      let item=primaryAddress(entityType,entityId);
      const payload={line1:normalizeWhitespace(input.line1),number:normalizeWhitespace(input.number),complement:normalizeWhitespace(input.complement),district:normalizeWhitespace(input.district),city:normalizeWhitespace(input.city),region:normalizeWhitespace(input.region),postalCode:normalizeWhitespace(input.postalCode),country:normalizeWhitespace(input.country||'BR')||'BR',primary:true,metadata:{...(item?.metadata||{}),...(input.metadata||{})},updatedAt:timestamp()};
      if(item){Object.assign(item,payload);}else{item={id:idFactory('addr'),entityType,entityId,createdAt:timestamp(),...payload};data.addresses.push(item);}
      return item;
    }

    function syncIdentityDetails(entityType,entityId,input,opts={}){
      if(input.email)addContactPoint(entityType,entityId,{type:'email',value:input.email,primary:true});
      if(input.phone)addContactPoint(entityType,entityId,{type:'phone',value:input.phone,primary:true});
      if(input.whatsapp)addContactPoint(entityType,entityId,{type:'whatsapp',value:input.whatsapp,primary:true});
      if(input.site)addContactPoint(entityType,entityId,{type:'site',value:input.site,primary:true});
      if(input.address)setPrimaryAddress(entityType,entityId,input.address);
      if(entityType==='person'&&(input.cpf||input.document))addDocument('person',entityId,{type:'cpf',value:input.cpf||input.document,country:input.documentCountry||'BR'},{allowInvalidLegacy:!!opts.allowInvalidLegacy});
      if(entityType==='organization'&&(input.cnpj||input.document))addDocument('organization',entityId,{type:'cnpj',value:input.cnpj||input.document,country:input.documentCountry||'BR'},{allowInvalidLegacy:!!opts.allowInvalidLegacy});
      if(Array.isArray(input.documents))input.documents.forEach((doc)=>addDocument(entityType,entityId,doc,{allowInvalidLegacy:!!opts.allowInvalidLegacy}));
    }

    function createPerson(input={},opts={}){
      const fullName=personDisplayName(input);
      if(!fullName)throw new Error('Pessoa requer nome');
      const existing=findStrongMatch('person',input,opts);
      if(existing){updatePerson(existing.id,input,opts);return existing;}
      const record={id:input.id||idFactory('per'),firstName:normalizeWhitespace(input.firstName),lastName:normalizeWhitespace(input.lastName),fullName,status:'active',tags:[],metadata:{},...baseFields(input)};
      data.people.push(record);syncIdentityDetails('person',record.id,input,opts);audit('person.created','person',record.id,null,record);record.updatedAt=timestamp();
      const possible=detectPotentialDuplicates('person',input,record.id).filter((x)=>x.confidence==='possible');if(possible.length)data.potentialDuplicates.push(...possible.map((x)=>({...x,candidateId:record.id,detectedAt:timestamp()})));
      return record;
    }
    function updatePerson(id,input={},opts={}){
      const record=getEntity('person',id);if(!record)throw new Error('Pessoa não encontrada');const before=clone(record);const name=personDisplayName(input);if(name)record.fullName=name;if('firstName'in input)record.firstName=normalizeWhitespace(input.firstName);if('lastName'in input)record.lastName=normalizeWhitespace(input.lastName);Object.assign(record,baseFields(input,record));syncIdentityDetails('person',id,input,opts);audit('person.updated','person',id,before,record);return record;
    }
    function createOrganization(input={},opts={}){
      const legalName=organizationDisplayName(input);if(!legalName)throw new Error('Organização requer nome');
      const existing=findStrongMatch('organization',input,opts);if(existing){updateOrganization(existing.id,input,opts);return existing;}
      const record={id:input.id||idFactory('org'),legalName,tradeName:normalizeWhitespace(input.tradeName),organizationType:normalizeWhitespace(input.organizationType||input.type),segment:normalizeWhitespace(input.segment),status:'active',tags:[],metadata:{},...baseFields(input)};
      data.organizations.push(record);syncIdentityDetails('organization',record.id,input,opts);audit('organization.created','organization',record.id,null,record);
      const possible=detectPotentialDuplicates('organization',input,record.id).filter((x)=>x.confidence==='possible');if(possible.length)data.potentialDuplicates.push(...possible.map((x)=>({...x,candidateId:record.id,detectedAt:timestamp()})));
      return record;
    }
    function updateOrganization(id,input={},opts={}){
      const record=getEntity('organization',id);if(!record)throw new Error('Organização não encontrada');const before=clone(record);const legal=normalizeWhitespace(input.legalName||input.name);if(legal)record.legalName=legal;if('tradeName'in input)record.tradeName=normalizeWhitespace(input.tradeName);if('organizationType'in input||'type'in input)record.organizationType=normalizeWhitespace(input.organizationType||input.type);if('segment'in input)record.segment=normalizeWhitespace(input.segment);Object.assign(record,baseFields(input,record));syncIdentityDetails('organization',id,input,opts);audit('organization.updated','organization',id,before,record);return record;
    }

    function assignRole(entityType,entityId,role,metadata={}){
      if(!getEntity(entityType,entityId))throw new Error('Entidade não encontrada');const normalizedRole=normalizeRole(role);if(!normalizedRole)throw new Error('Papel inválido');
      let item=data.roles.find((r)=>r.entityType===entityType&&r.entityId===entityId&&r.role===normalizedRole&&r.status!=='inactive');
      if(item){item.metadata={...(item.metadata||{}),...metadata};item.updatedAt=timestamp();return item;}
      item={id:idFactory('role'),entityType,entityId,role:normalizedRole,status:'active',metadata:clone(metadata),createdAt:timestamp(),updatedAt:timestamp(),createdBy:actorProvider()||null,updatedBy:actorProvider()||null};data.roles.push(item);audit('role.assigned',entityType,entityId,null,item,{role:normalizedRole});return item;
    }
    function removeRole(entityType,entityId,role){const normalizedRole=normalizeRole(role);const item=data.roles.find((r)=>r.entityType===entityType&&r.entityId===entityId&&r.role===normalizedRole&&r.status!=='inactive');if(!item)return false;item.status='inactive';item.updatedAt=timestamp();audit('role.removed',entityType,entityId,item,null,{role:normalizedRole});return true;}
    function getRoles(entityType,entityId){return data.roles.filter((r)=>r.entityType===entityType&&r.entityId===entityId&&r.status!=='inactive');}

    function linkPersonOrganization(personId,organizationId,input={}){
      if(!getEntity('person',personId)||!getEntity('organization',organizationId))throw new Error('Pessoa ou organização não encontrada');
      const relationshipType=normalizeRole(input.relationshipType||'organization_contact');
      let item=data.personOrganizationRelationships.find((r)=>r.personId===personId&&r.organizationId===organizationId&&r.relationshipType===relationshipType&&r.status!=='inactive');
      const payload={positionTitle:normalizeWhitespace(input.positionTitle),department:normalizeWhitespace(input.department),primary:!!input.primary,financialContact:!!input.financialContact,legalContact:!!input.legalContact,notes:normalizeWhitespace(input.notes),status:normalizeWhitespace(input.status||'active')||'active',metadata:{...(item?.metadata||{}),...(input.metadata||{})},updatedAt:timestamp(),updatedBy:actorProvider()||null};
      if(item){Object.assign(item,payload);return item;}
      item={id:idFactory('rel'),personId,organizationId,relationshipType,createdAt:timestamp(),createdBy:actorProvider()||null,...payload};data.personOrganizationRelationships.push(item);audit('relationship.created','person',personId,null,item,{organizationId});return item;
    }
    function getOrganizationContacts(organizationId){return data.personOrganizationRelationships.filter((r)=>r.organizationId===organizationId&&r.status!=='inactive').map((r)=>({relationship:r,person:getEntity('person',r.personId)})).filter((x)=>x.person);}
    function linkUser(personId,userId,metadata={}){if(!getEntity('person',personId))throw new Error('Pessoa não encontrada');if(!userId)throw new Error('userId obrigatório');let item=data.userLinks.find((x)=>x.personId===personId&&x.userId===userId&&x.status!=='inactive');if(item)return item;item={id:idFactory('usrlnk'),personId,userId,status:'active',metadata:clone(metadata),createdAt:timestamp(),updatedAt:timestamp()};data.userLinks.push(item);audit('user.linked','person',personId,null,item,{userId});return item;}

    return {data,getEntity,createPerson,updatePerson,createOrganization,updateOrganization,assignRole,removeRole,getRoles,linkPersonOrganization,getOrganizationContacts,linkUser,addDocument,addContactPoint,setPrimaryAddress,detectPotentialDuplicates,findStrongMatch,primaryContact,primaryAddress,documentFor};
  }

  return {SCHEMA_VERSION,ROLE_ALIASES,createState,ensureState,createService,normalizeWhitespace,fold,digits,normalizeEmail,normalizePhone,normalizeDocument,normalizeDomain,normalizeRole,validateCPF,validateCNPJ,validateDocument};
});
