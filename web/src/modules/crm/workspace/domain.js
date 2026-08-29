(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenCrmCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const TABS=['contacts','companies','customers','leads','interactions'];
  const STAGES=['new','contacted','qualified','proposal','converted'];
  const STAGE_LABELS={new:'Novo',contacted:'Em contato',qualified:'Qualificado',proposal:'Proposta',converted:'Convertido'};
  const INTERACTION_TYPES=['call','email','whatsapp','meeting','message','note','stage_change','follow_up','proposal','commercial_activity'];
  const INTERACTION_LABELS={call:'Ligação',email:'E-mail',whatsapp:'WhatsApp',meeting:'Reunião',message:'Mensagem',note:'Anotação',stage_change:'Mudança de etapa',follow_up:'Follow-up',proposal:'Proposta',commercial_activity:'Atividade comercial'};
  const ROLE_LABELS={customer:'Cliente',lead:'Lead',prospect:'Prospect',supplier:'Fornecedor',partner:'Parceiro',service_provider:'Prestador',beneficiary:'Beneficiário',economic_participant:'Participante econômico',contractual_party:'Parte contratual',organization_contact:'Contato de empresa',responsible:'Responsável',crm_contact:'Contato CRM'};
  const CRM_ROLE_SET=new Set(['customer','lead','prospect','supplier','partner','service_provider','beneficiary','economic_participant','contractual_party','organization_contact','responsible','crm_contact']);

  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const asArray=(value)=>Array.isArray(value)?value:[];
  const unique=(items)=>Array.from(new Set(asArray(items).map(text).filter(Boolean)));
  const normalizeStage=(value)=>{
    const key=fold(value).replace(/[^a-z0-9]+/g,'_');
    const map={novo:'new',new:'new','em_contato':'contacted',contacted:'contacted',qualificado:'qualified',qualified:'qualified',proposta:'proposal',proposal:'proposal',convertido:'converted',converted:'converted'};
    return STAGES.includes(map[key]||key)?(map[key]||key):'new';
  };
  const normalizeInteractionType=(value)=>{
    const key=fold(value).replace(/[^a-z0-9]+/g,'_');
    const map={'ligacao':'call',call:'call','e_mail':'email',email:'email',whatsapp:'whatsapp','reuniao':'meeting',meeting:'meeting',mensagem:'message',message:'message','anotacao':'note',note:'note','mudanca_de_etapa':'stage_change',stage_change:'stage_change','follow_up':'follow_up',follow_up:'follow_up',proposta:'proposal',proposal:'proposal','atividade_comercial':'commercial_activity',commercial_activity:'commercial_activity'};
    return INTERACTION_TYPES.includes(map[key]||key)?(map[key]||key):'note';
  };

  function createState(){
    return {schemaVersion:SCHEMA_VERSION,contexts:[],leads:[],interactions:[],history:[],metadata:{}};
  }
  function ensureState(input){
    const state=input&&typeof input==='object'?input:createState();
    for(const key of ['contexts','leads','interactions','history'])if(!Array.isArray(state[key]))state[key]=[];
    if(!state.metadata||typeof state.metadata!=='object')state.metadata={};
    state.schemaVersion=SCHEMA_VERSION;
    return state;
  }

  function createService(partyService,crmState,options={}){
    if(!partyService||typeof partyService.createPerson!=='function')throw new Error('Party service canônico obrigatório');
    const data=ensureState(crmState), now=options.now||(()=>new Date().toISOString()), idFactory=options.idFactory||((prefix)=>`${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,10)}`), actor=options.actorProvider||(()=>null);
    const party=partyService;

    const history=(action,payload={})=>{const row={id:idFactory('crmhist'),action,at:now(),actorId:actor()||null,...clone(payload)};data.history.push(row);return row;};
    const getContext=(entityType,entityId,create=false)=>{
      let row=data.contexts.find((x)=>x.entityType===entityType&&x.entityId===entityId);
      if(!row&&create){row={id:idFactory('crmctx'),entityType,entityId,active:true,status:'active',priority:'medium',source:'',responsibleId:'',tags:[],notes:'',legacyId:'',createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null,metadata:{}};data.contexts.push(row);}
      return row||null;
    };
    const patchContext=(entityType,entityId,input={})=>{
      const row=getContext(entityType,entityId,true),before=clone(row);
      if('active'in input)row.active=!!input.active;
      if('status'in input)row.status=text(input.status)||row.status;
      if('priority'in input)row.priority=text(input.priority)||row.priority;
      if('source'in input)row.source=text(input.source);
      if('responsibleId'in input)row.responsibleId=text(input.responsibleId);
      if('notes'in input)row.notes=text(input.notes);
      if('legacyId'in input)row.legacyId=text(input.legacyId);
      if('tags'in input)row.tags=unique(input.tags);
      row.metadata={...(row.metadata||{}),...(input.metadata||{})};row.updatedAt=now();row.updatedBy=actor()||null;
      if(JSON.stringify(before)!==JSON.stringify(row))history('context.updated',{entityType,entityId,before,after:row});
      return row;
    };
    const roles=(entityType,entityId)=>party.getRoles(entityType,entityId).map((x)=>x.role);
    const hasRole=(entityType,entityId,role)=>roles(entityType,entityId).includes(role);
    const assignRoles=(entityType,entityId,items,metadata={})=>unique(items).forEach((role)=>party.assignRole(entityType,entityId,role,metadata));
    const removeRole=(entityType,entityId,role)=>party.removeRole(entityType,entityId,role);
    const primary=(entityType,entityId,kind)=>party.primaryContact(entityType,entityId,kind)?.value||'';
    const document=(entityType,entityId,kind)=>party.documentFor(entityType,entityId,kind)?.value||'';
    const address=(entityType,entityId)=>party.primaryAddress(entityType,entityId)||null;

    function resolveOrganization(input={}){
      if(input.organizationId){const existing=party.getEntity('organization',input.organizationId);if(!existing)throw new Error('Empresa não encontrada');return existing;}
      if(!text(input.organizationName||input.company))return null;
      return party.createOrganization({legalName:text(input.organizationName||input.company),tradeName:text(input.organizationTradeName||input.organizationName||input.company),cnpj:input.organizationCnpj||'',email:input.organizationEmail||'',phone:input.organizationPhone||'',status:'active',metadata:{source:'crm'}},{});
    }

    function saveContact(input={},opts={}){
      const personInput={fullName:text(input.fullName||input.name),firstName:text(input.firstName),lastName:text(input.lastName),cpf:input.cpf||'',email:input.email||'',phone:input.phone||'',whatsapp:input.whatsapp||'',address:input.address||null,status:input.identityStatus||'active',tags:unique(input.tags),metadata:{source:'crm',...(input.identityMetadata||{})}};
      if(!personInput.fullName)throw new Error('Nome do contato é obrigatório');
      let person;
      if(input.personId)person=party.updatePerson(input.personId,personInput);else person=party.createPerson(personInput);
      party.assignRole('person',person.id,'crm_contact',{source:'crm'});
      if(input.role)party.assignRole('person',person.id,input.role,{source:'crm'});
      const ctx=patchContext('person',person.id,{active:true,status:input.status||'active',priority:input.priority||'medium',source:input.source||'',responsibleId:input.responsibleId||'',notes:input.notes||'',tags:input.tags||[],legacyId:input.legacyId||'',metadata:{relationshipLabel:input.relationshipLabel||'',origin:input.source||''}});
      let organization=null,relationship=null;
      if(input.organizationId||input.organizationName||input.company){organization=resolveOrganization(input);if(organization){relationship=party.linkPersonOrganization(person.id,organization.id,{relationshipType:'organization_contact',positionTitle:input.positionTitle||'',department:input.department||'',primary:!!input.primaryContact,financialContact:!!input.financialContact,legalContact:!!input.legalContact,notes:input.relationshipNotes||'',status:'active',metadata:{source:'crm'}});party.assignRole('person',person.id,'organization_contact',{source:'crm'});}}
      history(input.personId?'contact.updated':'contact.created',{entityType:'person',entityId:person.id,organizationId:organization?.id||'',contextId:ctx.id});
      return {person,context:ctx,organization,relationship};
    }

    function saveCompany(input={}){
      const orgInput={legalName:text(input.legalName||input.name),tradeName:text(input.tradeName),cnpj:input.cnpj||'',organizationType:text(input.organizationType),segment:text(input.segment),email:input.email||'',phone:input.phone||'',site:input.site||'',address:input.address||null,status:input.identityStatus||'active',tags:unique(input.tags),metadata:{source:'crm',...(input.identityMetadata||{})}};
      if(!orgInput.legalName)throw new Error('Razão social ou nome da empresa é obrigatório');
      let organization;
      if(input.organizationId)organization=party.updateOrganization(input.organizationId,orgInput);else organization=party.createOrganization(orgInput);
      party.assignRole('organization',organization.id,'crm_contact',{source:'crm'});
      assignRoles('organization',organization.id,input.roles||[],{source:'crm'});
      const ctx=patchContext('organization',organization.id,{active:true,status:input.status||'active',priority:input.priority||'medium',source:input.source||'',responsibleId:input.responsibleId||'',notes:input.notes||'',tags:input.tags||[],legacyId:input.legacyId||'',metadata:{segment:input.segment||''}});
      history(input.organizationId?'company.updated':'company.created',{entityType:'organization',entityId:organization.id,contextId:ctx.id});
      return {organization,context:ctx};
    }

    function saveCustomer(input={}){
      const entityType=input.entityType==='organization'?'organization':'person';
      let entity;
      if(entityType==='person'){
        if(input.entityId)entity=party.updatePerson(input.entityId,{fullName:text(input.fullName||input.name),cpf:input.cpf||'',email:input.email||'',phone:input.phone||'',whatsapp:input.whatsapp||'',address:input.address||null,tags:unique(input.tags),metadata:{source:'crm_customer'}});
        else entity=party.createPerson({fullName:text(input.fullName||input.name),cpf:input.cpf||'',email:input.email||'',phone:input.phone||'',whatsapp:input.whatsapp||'',address:input.address||null,tags:unique(input.tags),metadata:{source:'crm_customer'}});
      }else{
        if(input.entityId)entity=party.updateOrganization(input.entityId,{legalName:text(input.legalName||input.name),tradeName:text(input.tradeName),cnpj:input.cnpj||'',email:input.email||'',phone:input.phone||'',site:input.site||'',segment:input.segment||'',address:input.address||null,tags:unique(input.tags),metadata:{source:'crm_customer'}});
        else entity=party.createOrganization({legalName:text(input.legalName||input.name),tradeName:text(input.tradeName),cnpj:input.cnpj||'',email:input.email||'',phone:input.phone||'',site:input.site||'',segment:input.segment||'',address:input.address||null,tags:unique(input.tags),metadata:{source:'crm_customer'}});
      }
      party.assignRole(entityType,entity.id,'customer',{source:'crm'});
      const ctx=patchContext(entityType,entity.id,{active:true,status:input.status||'active',priority:input.priority||'medium',source:input.source||'',responsibleId:input.responsibleId||'',notes:input.notes||'',tags:input.tags||[],legacyId:input.legacyId||'',metadata:{customerSince:input.customerSince||now()}});
      history('customer.assigned',{entityType,entityId:entity.id,contextId:ctx.id});
      return {entityType,entity,context:ctx};
    }

    function saveLead(input={}){
      const existing=input.leadId?data.leads.find((x)=>x.id===input.leadId):null;
      const identityMode=['person','organization','person_organization'].includes(input.identityMode)?input.identityMode:(existing?.identityMode||'person');
      let person=null,organization=null;
      if(identityMode==='person'||identityMode==='person_organization'){
        if(input.personId||existing?.personId)person=party.updatePerson(input.personId||existing.personId,{fullName:text(input.fullName||input.name),email:input.email||'',phone:input.phone||'',cpf:input.cpf||'',metadata:{source:'crm_lead'}});
        else person=party.createPerson({fullName:text(input.fullName||input.name),email:input.email||'',phone:input.phone||'',cpf:input.cpf||'',metadata:{source:'crm_lead'}});
        party.assignRole('person',person.id,'lead',{source:'crm'});
      }
      if(identityMode==='organization'||identityMode==='person_organization'){
        if(input.organizationId||existing?.organizationId)organization=party.updateOrganization(input.organizationId||existing.organizationId,{legalName:text(input.legalName||input.organizationName||input.company),tradeName:text(input.tradeName||input.organizationName||input.company),cnpj:input.cnpj||'',email:input.organizationEmail||'',phone:input.organizationPhone||'',metadata:{source:'crm_lead'}});
        else organization=party.createOrganization({legalName:text(input.legalName||input.organizationName||input.company),tradeName:text(input.tradeName||input.organizationName||input.company),cnpj:input.cnpj||'',email:input.organizationEmail||'',phone:input.organizationPhone||'',metadata:{source:'crm_lead'}});
        party.assignRole('organization',organization.id,'prospect',{source:'crm'});
      }else if(person&&(input.organizationId||input.organizationName||input.company)){
        organization=resolveOrganization(input);if(organization)party.assignRole('organization',organization.id,'prospect',{source:'crm'});
      }
      if(person&&organization)party.linkPersonOrganization(person.id,organization.id,{relationshipType:'organization_contact',positionTitle:input.positionTitle||'',department:input.department||'',primary:true,metadata:{source:'crm_lead'}});
      const stage=normalizeStage(input.stage||existing?.stage||'new'), previousStage=existing?.stage||'';
      const payload={identityMode,personId:person?.id||existing?.personId||'',organizationId:organization?.id||existing?.organizationId||'',origin:text(input.origin||existing?.origin),productInterestRef:text(input.productInterestRef||existing?.productInterestRef),serviceInterestRef:text(input.serviceInterestRef||existing?.serviceInterestRef),responsibleId:text(input.responsibleId||existing?.responsibleId),stage,priority:text(input.priority||existing?.priority||'medium')||'medium',status:text(input.status||existing?.status||'open')||'open',notes:text(input.notes??existing?.notes),tags:unique(input.tags??existing?.tags),legacyId:text(input.legacyId||existing?.legacyId),updatedAt:now(),updatedBy:actor()||null,metadata:{...(existing?.metadata||{}),...(input.metadata||{})}};
      let lead;
      if(existing){const before=clone(existing);Object.assign(existing,payload);lead=existing;history('lead.updated',{leadId:lead.id,before,after:lead});}
      else{lead={id:input.id||idFactory('lead'),createdAt:now(),createdBy:actor()||null,convertedAt:null,customerEntityType:'',customerEntityId:'',...payload};data.leads.push(lead);history('lead.created',{leadId:lead.id,after:lead});}
      if(previousStage&&previousStage!==stage)recordStageChange(lead,previousStage,stage,input.stageChangeNote||'');
      if(stage==='converted'&&previousStage!=='converted')convertLead(lead.id,{note:input.stageChangeNote||''});
      return lead;
    }

    function recordStageChange(lead,from,to,note=''){
      history('lead.stage.changed',{leadId:lead.id,before:{stage:from},after:{stage:to}});
      return createInteraction({type:'stage_change',title:'Mudança de etapa',description:`${STAGE_LABELS[from]||from} → ${STAGE_LABELS[to]||to}${note?` — ${text(note)}`:''}`,occurredAt:now(),responsibleId:lead.responsibleId,personId:lead.personId,organizationId:lead.organizationId,leadId:lead.id,metadata:{fromStage:from,toStage:to}});
    }

    function changeLeadStage(leadId,nextStage,note=''){
      const lead=data.leads.find((x)=>x.id===leadId);if(!lead)throw new Error('Lead não encontrado');const next=normalizeStage(nextStage),previous=lead.stage;if(next===previous)return lead;lead.stage=next;lead.updatedAt=now();lead.updatedBy=actor()||null;recordStageChange(lead,previous,next,note);if(next==='converted')convertLead(lead.id,{note});return lead;
    }

    function convertLead(leadId,opts={}){
      const lead=data.leads.find((x)=>x.id===leadId);if(!lead)throw new Error('Lead não encontrado');
      const targetType=lead.organizationId?'organization':'person',targetId=lead.organizationId||lead.personId;if(!targetId)throw new Error('Lead sem identidade canônica para conversão');
      const already=lead.convertedAt&&lead.customerEntityId===targetId;
      party.assignRole(targetType,targetId,'customer',{source:'crm',leadId:lead.id});
      patchContext(targetType,targetId,{active:true,status:'active',responsibleId:lead.responsibleId,priority:lead.priority,source:lead.origin,metadata:{convertedFromLeadId:lead.id}});
      if(lead.stage!=='converted'){const previous=lead.stage;lead.stage='converted';recordStageChange(lead,previous,'converted',opts.note||'');}
      lead.status='converted';lead.convertedAt=lead.convertedAt||now();lead.customerEntityType=targetType;lead.customerEntityId=targetId;lead.updatedAt=now();lead.updatedBy=actor()||null;
      if(!already)history('lead.converted',{leadId:lead.id,entityType:targetType,entityId:targetId,after:lead});
      return {lead,customerEntityType:targetType,customerEntityId:targetId};
    }

    function createInteraction(input={}){
      const type=normalizeInteractionType(input.type),occurredAt=input.occurredAt||now();
      if(input.personId&&!party.getEntity('person',input.personId))throw new Error('Pessoa da interação não encontrada');
      if(input.organizationId&&!party.getEntity('organization',input.organizationId))throw new Error('Empresa da interação não encontrada');
      if(input.leadId&&!data.leads.find((x)=>x.id===input.leadId))throw new Error('Lead da interação não encontrado');
      const row={id:input.id||idFactory('int'),type,title:text(input.title||INTERACTION_LABELS[type]||'Interação'),description:text(input.description),occurredAt,responsibleId:text(input.responsibleId),personId:text(input.personId),organizationId:text(input.organizationId),leadId:text(input.leadId),customerEntityType:input.customerEntityType==='organization'?'organization':input.customerEntityType==='person'?'person':'',customerEntityId:text(input.customerEntityId),status:text(input.status||((type==='follow_up')?'pending':'completed'))||'completed',followUpAt:input.followUpAt||'',metadata:clone(input.metadata||{}),createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null};
      data.interactions.push(row);history('interaction.created',{interactionId:row.id,leadId:row.leadId,entityType:row.personId?'person':row.organizationId?'organization':'',entityId:row.personId||row.organizationId||'',after:row});return row;
    }
    function updateInteraction(id,input={}){const row=data.interactions.find((x)=>x.id===id);if(!row)throw new Error('Interação não encontrada');const before=clone(row);if('type'in input)row.type=normalizeInteractionType(input.type);for(const key of ['title','description','occurredAt','responsibleId','personId','organizationId','leadId','customerEntityType','customerEntityId','status','followUpAt'])if(key in input)row[key]=key==='title'||key==='description'||key==='responsibleId'||key==='status'?text(input[key]):input[key]||'';row.metadata={...(row.metadata||{}),...(input.metadata||{})};row.updatedAt=now();row.updatedBy=actor()||null;history('interaction.updated',{interactionId:id,before,after:row});return row;}
    function removeInteraction(id){const row=data.interactions.find((x)=>x.id===id);if(!row)return false;const before=clone(row);row.status='archived';row.updatedAt=now();history('interaction.archived',{interactionId:id,before,after:row});return true;}

    function archiveEntityContext(entityType,entityId){const ctx=getContext(entityType,entityId,false);if(!ctx)return false;const before=clone(ctx);ctx.active=false;ctx.status='archived';ctx.updatedAt=now();ctx.updatedBy=actor()||null;party.removeRole(entityType,entityId,'crm_contact');history('context.archived',{entityType,entityId,before,after:ctx});return true;}

    const isDemoContext=(entityType,entityId)=>!!getContext(entityType,entityId,false)?.metadata?.demo;
    const isDemoLead=(lead)=>!!lead?.metadata?.demo;
    const activeContexts=()=>data.contexts.filter((x)=>x.active!==false&&x.status!=='archived');
    const getContacts=({includeDemo=false}={})=>activeContexts().filter((x)=>x.entityType==='person'&&(hasRole('person',x.entityId,'crm_contact')||hasRole('person',x.entityId,'customer')||hasRole('person',x.entityId,'partner')||hasRole('person',x.entityId,'supplier')||hasRole('person',x.entityId,'service_provider'))&&(!isDemoContext('person',x.entityId)||includeDemo)).map((context)=>({context,person:party.getEntity('person',context.entityId)})).filter((x)=>x.person);
    const getCompanies=({includeDemo=false}={})=>activeContexts().filter((x)=>x.entityType==='organization'&&(!isDemoContext('organization',x.entityId)||includeDemo)).map((context)=>({context,organization:party.getEntity('organization',context.entityId)})).filter((x)=>x.organization);
    const getCustomers=({includeDemo=false}={})=>['person','organization'].flatMap((entityType)=>{const list=entityType==='person'?party.data.people:party.data.organizations;return list.filter((entity)=>hasRole(entityType,entity.id,'customer')).map((entity)=>({entityType,entity,context:getContext(entityType,entity.id,true)})).filter((x)=>includeDemo||!isDemoContext(entityType,x.entity.id));});
    const getLeads=({includeDemo=false}={})=>data.leads.filter((x)=>x.status!=='archived'&&(includeDemo||!isDemoLead(x)));
    const getInteractions=({includeDemo=false}={})=>data.interactions.filter((x)=>x.status!=='archived'&&(includeDemo||!x.metadata?.demo));

    function interactionsFor({personId='',organizationId='',leadId='',customerEntityType='',customerEntityId='',includeDemo=false}={}){
      return getInteractions({includeDemo}).filter((x)=>(personId&&x.personId===personId)||(organizationId&&x.organizationId===organizationId)||(leadId&&x.leadId===leadId)||(customerEntityId&&x.customerEntityType===customerEntityType&&x.customerEntityId===customerEntityId)).sort((a,b)=>String(b.occurredAt).localeCompare(String(a.occurredAt)));
    }

    function migrateLegacy(payload={}){
      if(data.metadata.legacyMigrated)return {contacts:0,companies:0,leads:0,interactions:0};
      let counts={contacts:0,companies:0,leads:0,interactions:0};
      for(const item of asArray(payload.contacts)){
        if(!item?.canonicalEntityId)continue;const demo=!!payload.isDemo?.(item);const entityType=item.canonicalEntityType==='organization'?'organization':'person';
        patchContext(entityType,item.canonicalEntityId,{active:true,status:item.status||'active',priority:item.priority||'medium',responsibleId:item.responsible||'',notes:item.notes||'',legacyId:item.id||'',tags:[],metadata:{demo,legacySource:'crm.contacts'}});
        if(entityType==='person')counts.contacts++;else counts.companies++;
        if(!demo)for(const legacyInteraction of asArray(item.interactions)){if(!text(legacyInteraction.text))continue;createInteraction({type:legacyInteraction.type||'note',title:legacyInteraction.type||'Interação',description:legacyInteraction.text,occurredAt:legacyInteraction.date||now(),personId:entityType==='person'?item.canonicalEntityId:'',organizationId:entityType==='organization'?item.canonicalEntityId:item.canonicalOrganizationId||'',metadata:{legacy:true}});counts.interactions++;}
      }
      for(const item of asArray(payload.leads)){
        if(!item?.canonicalEntityId)continue;const demo=!!payload.isDemo?.(item),lead={id:String(item.id||idFactory('lead')),identityMode:item.canonicalOrganizationId?'person_organization':item.canonicalEntityType==='organization'?'organization':'person',personId:item.canonicalEntityType==='person'?item.canonicalEntityId:'',organizationId:item.canonicalEntityType==='organization'?item.canonicalEntityId:(item.canonicalOrganizationId||''),origin:text(item.source),productInterestRef:'',serviceInterestRef:'',responsibleId:text(item.responsible),stage:normalizeStage(item.stage),priority:text(item.priority||'medium'),status:normalizeStage(item.stage)==='converted'?'converted':'open',notes:text(item.notes),tags:[],legacyId:String(item.id||''),createdAt:item.createdAt||now(),updatedAt:now(),createdBy:null,updatedBy:null,convertedAt:null,customerEntityType:'',customerEntityId:'',metadata:{demo,legacySource:'crm.leads'}};if(!data.leads.some((x)=>x.id===lead.id))data.leads.push(lead);counts.leads++;}
      data.metadata.legacyMigrated=true;data.metadata.legacyMigratedAt=now();history('legacy.migrated',{after:counts});return counts;
    }

    return {data,party,history,getContext,patchContext,roles,hasRole,assignRoles,removeRole,primary,document,address,saveContact,saveCompany,saveCustomer,saveLead,changeLeadStage,convertLead,createInteraction,updateInteraction,removeInteraction,archiveEntityContext,getContacts,getCompanies,getCustomers,getLeads,getInteractions,interactionsFor,migrateLegacy,isDemoContext,isDemoLead};
  }

  return {SCHEMA_VERSION,TABS,STAGES,STAGE_LABELS,INTERACTION_TYPES,INTERACTION_LABELS,ROLE_LABELS,CRM_ROLE_SET,createState,ensureState,createService,normalizeStage,normalizeInteractionType,fold,text};
});