// VALTREN CANONICAL PARTIES BROWSER/LEGACY ADAPTER
function crmCanonicalPartyService(){
  const core=(typeof ValtrenPartyCore!=='undefined'?ValtrenPartyCore:globalThis.ValtrenPartyCore);
  if(!core)throw new Error('ValtrenPartyCore indisponível');
  state.crmCanonicalParties=core.ensureState(state.crmCanonicalParties);
  if(!state.__crmCanonicalPartyService||state.__crmCanonicalPartyService.data!==state.crmCanonicalParties){
    state.__crmCanonicalPartyService=core.createService(state.crmCanonicalParties,{actorProvider:()=>state.crmUserId||state.crmUserName||null});
  }
  return state.__crmCanonicalPartyService;
}

function crmCanonicalRoleFromSegment(value){
  const core=(typeof ValtrenPartyCore!=='undefined'?ValtrenPartyCore:globalThis.ValtrenPartyCore);
  const normalized=core.fold(value);
  const map={cliente:'customer',fornecedor:'supplier',parceiro:'partner','prestador de servicos':'service_provider','prestador de serviços':'service_provider',contratante:'contractual_party',beneficiario:'beneficiary','beneficiário':'beneficiary'};
  return map[normalized]||core.normalizeRole(value||'crm_contact');
}

function crmCanonicalSplitCity(value){
  const parts=String(value||'').split('/').map((x)=>x.trim()).filter(Boolean);
  return {city:parts[0]||'',region:parts[1]||''};
}

function crmCanonicalIdentityInput(item,entityType){
  const city=crmCanonicalSplitCity(item.city);
  const address={line1:item.address||'',number:item.addressNumber||'',complement:item.addressComplement||'',district:item.neighborhood||'',city:city.city,region:city.region,postalCode:item.zipCode||'',country:'BR'};
  if(entityType==='organization')return {legalName:item.name||item.company||'',tradeName:item.company||'',cnpj:item.cnpj||'',email:item.email||'',phone:item.phone||'',site:item.site||'',address,status:item.status||'active',segment:item.segment||'',metadata:{source:'crm_legacy_adapter'}};
  return {fullName:item.name||'',cpf:item.cpf||'',email:item.email||'',phone:item.phone||'',address,status:item.status||'active',metadata:{source:'crm_legacy_adapter'}};
}

function crmCanonicalBinding(source,legacyId){
  const service=crmCanonicalPartyService();
  return service.data.legacyBindings.find((b)=>b.source===source&&String(b.legacyId)===String(legacyId))||null;
}

function crmCanonicalEnsureBinding(source,legacyId,entityType,entityId,organizationId,metadata,prepend=false){
  const service=crmCanonicalPartyService();
  let binding=crmCanonicalBinding(source,legacyId);
  if(!binding){
    binding={id:`bind_${source.replace(/\W+/g,'_')}_${legacyId}`,source,legacyId:String(legacyId),entityType,entityId,organizationId:organizationId||'',metadata:{...metadata},createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()};
    prepend?service.data.legacyBindings.unshift(binding):service.data.legacyBindings.push(binding);
  }else{
    binding.entityType=entityType;binding.entityId=entityId;binding.organizationId=organizationId||binding.organizationId||'';binding.metadata={...(binding.metadata||{}),...metadata};binding.updatedAt=new Date().toISOString();
  }
  return binding;
}

function crmCanonicalLegacyMetadata(item){
  return {
    segment:item.segment||'',profile:item.profile||'',source:item.source||'',stage:item.stage||'',status:item.status||'',priority:item.priority||'',
    responsible:item.responsible||'',responsibleRole:item.responsibleRole||'',responsibleEmail:item.responsibleEmail||'',responsiblePhone:item.responsiblePhone||'',
    instagram:item.instagram||'',function:item.function||'',notes:item.notes||'',interactions:Array.isArray(item.interactions)?item.interactions.map((x)=>({...x})):[],
    legacySnapshot:{...item,interactions:Array.isArray(item.interactions)?item.interactions.map((x)=>({...x})):[]}
  };
}

function crmCanonicalUpsertResponsible(organizationId,item,allowInvalidLegacy=false){
  const name=String(item.responsible||'').trim();
  if(!name||/^equipe valtren$/i.test(name))return null;
  const service=crmCanonicalPartyService();
  const person=service.createPerson({fullName:name,email:item.responsibleEmail||'',phone:item.responsiblePhone||'',metadata:{source:'crm_organization_contact'}},{allowInvalidLegacy});
  service.assignRole('person',person.id,'organization_contact',{source:'crm'});
  return service.linkPersonOrganization(person.id,organizationId,{relationshipType:'organization_contact',positionTitle:item.responsibleRole||'',primary:true,financialContact:/financeir/i.test(item.responsibleRole||''),legalContact:/jurid/i.test(item.responsibleRole||''),metadata:{source:'crm'}});
}

function crmCanonicalUpsertLegacyRecord(kind,item,mode='create',options={}){
  try{
    const service=crmCanonicalPartyService();
    const source=kind==='contacts'?'crm.contacts':'crm.leads';
    const existingBinding=crmCanonicalBinding(source,item.id);
    const entityType=item.tipo_pessoa==='pessoa_juridica'?'organization':'person';
    const identity=crmCanonicalIdentityInput(item,entityType);
    const legacy=!!options.legacy;
    let entity;
    if(existingBinding&&existingBinding.entityType===entityType&&service.getEntity(entityType,existingBinding.entityId)){
      entity=entityType==='organization'?service.updateOrganization(existingBinding.entityId,identity,{allowInvalidLegacy:legacy}):service.updatePerson(existingBinding.entityId,identity,{allowInvalidLegacy:legacy});
    }else{
      entity=entityType==='organization'?service.createOrganization(identity,{allowInvalidLegacy:legacy,allowExactNameMatch:legacy}):service.createPerson(identity,{allowInvalidLegacy:legacy});
    }
    if(kind==='contacts'){
      service.assignRole(entityType,entity.id,'crm_contact',{source:'crm'});
      if(item.segment)service.assignRole(entityType,entity.id,crmCanonicalRoleFromSegment(item.segment),{source:'crm',displayLabel:item.segment});
    }else{
      service.assignRole(entityType,entity.id,'lead',{source:'crm',stage:item.stage||'Novo'});
    }

    let organizationId='';
    if(entityType==='organization'){
      organizationId=entity.id;
      crmCanonicalUpsertResponsible(entity.id,item,legacy);
    }else if(item.company){
      const organization=service.createOrganization({legalName:item.company,tradeName:item.company,status:'active',metadata:{source:'crm_company_reference'}},{allowExactNameMatch:true,allowInvalidLegacy:legacy});
      organizationId=organization.id;
      service.assignRole('organization',organization.id,kind==='leads'?'prospect':'crm_contact',{source:'crm'});
      service.linkPersonOrganization(entity.id,organization.id,{relationshipType:'organization_contact',positionTitle:item.function||'',primary:true,metadata:{source:'crm'}});
    }

    const metadata=crmCanonicalLegacyMetadata(item);
    let binding=existingBinding;
    if(!binding&&mode==='create'){
      binding=service.data.legacyBindings.find((b)=>b.source===source&&b.entityType===entityType&&b.entityId===entity.id)||null;
    }
    if(binding){
      binding.entityType=entityType;binding.entityId=entity.id;binding.organizationId=organizationId||binding.organizationId||'';binding.metadata={...(binding.metadata||{}),...metadata};binding.updatedAt=new Date().toISOString();
    }else{
      crmCanonicalEnsureBinding(source,item.id,entityType,entity.id,organizationId,metadata,!legacy);
    }
    crmCanonicalSyncLegacyViews();
    return true;
  }catch(error){
    console.error('Falha na infraestrutura canônica de Pessoas e Organizações:',error);
    if(!options.silent&&typeof alert==='function')alert(error?.message||'Não foi possível salvar o cadastro.');
    return false;
  }
}

function crmCanonicalProjectBinding(binding){
  const service=crmCanonicalPartyService();
  const entity=service.getEntity(binding.entityType,binding.entityId);if(!entity)return null;
  const meta=binding.metadata||{},snapshot=meta.legacySnapshot||{};
  const email=service.primaryContact(binding.entityType,binding.entityId,'email')?.value||snapshot.email||'';
  const phone=service.primaryContact(binding.entityType,binding.entityId,'phone')?.value||snapshot.phone||'';
  const address=service.primaryAddress(binding.entityType,binding.entityId);
  const cpf=binding.entityType==='person'?service.documentFor('person',binding.entityId,'cpf')?.value||snapshot.cpf||'':'';
  const cnpj=binding.entityType==='organization'?service.documentFor('organization',binding.entityId,'cnpj')?.value||snapshot.cnpj||'':'';
  const org=binding.organizationId?service.getEntity('organization',binding.organizationId):null;
  const city=address?[address.city,address.region].filter(Boolean).join(' / '):(snapshot.city||'');
  return {
    id:String(binding.legacyId),tipo_pessoa:binding.entityType==='organization'?'pessoa_juridica':'pessoa_fisica',
    name:binding.entityType==='organization'?entity.legalName:entity.fullName,
    company:binding.entityType==='organization'?(entity.tradeName||''):(org?.tradeName||org?.legalName||snapshot.company||''),
    segment:meta.segment||snapshot.segment||'',profile:meta.profile||snapshot.profile||'',source:meta.source||snapshot.source||'',stage:meta.stage||snapshot.stage||'',
    phone,email,city,responsible:meta.responsible||snapshot.responsible||'',responsibleRole:meta.responsibleRole||snapshot.responsibleRole||'',responsibleEmail:meta.responsibleEmail||snapshot.responsibleEmail||'',responsiblePhone:meta.responsiblePhone||snapshot.responsiblePhone||'',
    status:meta.status||entity.status||snapshot.status||'',priority:meta.priority||snapshot.priority||'',cpf,cnpj,instagram:meta.instagram||snapshot.instagram||'',function:meta.function||snapshot.function||'',
    address:address?.line1||snapshot.address||'',addressNumber:address?.number||snapshot.addressNumber||'',addressComplement:address?.complement||snapshot.addressComplement||'',neighborhood:address?.district||snapshot.neighborhood||'',zipCode:address?.postalCode||snapshot.zipCode||'',
    notes:meta.notes||snapshot.notes||'',interactions:Array.isArray(meta.interactions)?meta.interactions.map((x)=>({...x})):[],canonicalEntityType:binding.entityType,canonicalEntityId:binding.entityId,canonicalOrganizationId:binding.organizationId||'',canonicalRoles:service.getRoles(binding.entityType,binding.entityId).map((r)=>r.role)
  };
}

function crmCanonicalSyncLegacyViews(){
  const service=crmCanonicalPartyService();
  const contacts=service.data.legacyBindings.filter((b)=>b.source==='crm.contacts').map(crmCanonicalProjectBinding).filter(Boolean);
  const leads=service.data.legacyBindings.filter((b)=>b.source==='crm.leads').map(crmCanonicalProjectBinding).filter(Boolean);
  state.crmRelContacts=contacts;state.crmRelLeads=leads;
  return {contacts,leads};
}

function crmCanonicalEnsureFromLegacy(){
  const service=crmCanonicalPartyService();
  if(!service.data.metadata.crmLegacyMigrated){
    const contacts=Array.isArray(state.crmRelContacts)?state.crmRelContacts.map((x)=>({...x,interactions:Array.isArray(x.interactions)?x.interactions.map((i)=>({...i})):[]})):[];
    const leads=Array.isArray(state.crmRelLeads)?state.crmRelLeads.map((x)=>({...x,interactions:Array.isArray(x.interactions)?x.interactions.map((i)=>({...i})):[]})):[];
    contacts.forEach((item)=>crmCanonicalUpsertLegacyRecord('contacts',item,'migrate',{legacy:true,silent:true}));
    leads.forEach((item)=>crmCanonicalUpsertLegacyRecord('leads',item,'migrate',{legacy:true,silent:true}));
    service.data.metadata.crmLegacyMigrated=true;service.data.metadata.migratedAt=new Date().toISOString();service.data.metadata.source='crmRelContacts/crmRelLeads';
  }
  return crmCanonicalSyncLegacyViews();
}

function crmCanonicalRemoveLegacyRecord(kind,id){
  const service=crmCanonicalPartyService();
  const source=kind==='contacts'?'crm.contacts':'crm.leads';
  const index=service.data.legacyBindings.findIndex((b)=>b.source===source&&String(b.legacyId)===String(id));
  if(index<0)return false;
  const [binding]=service.data.legacyBindings.splice(index,1);
  const stillUsed=service.data.legacyBindings.some((b)=>b.source===source&&b.entityType===binding.entityType&&b.entityId===binding.entityId);
  if(!stillUsed)service.removeRole(binding.entityType,binding.entityId,kind==='contacts'?'crm_contact':'lead');
  service.data.history.push({id:`hist_legacy_${Date.now()}_${Math.random().toString(36).slice(2)}`,action:'legacy.binding.removed',entityType:binding.entityType,entityId:binding.entityId,at:new Date().toISOString(),actorId:state.crmUserId||state.crmUserName||null,before:binding,after:null,metadata:{source}});
  crmCanonicalSyncLegacyViews();return true;
}

function crmCanonicalRemoveLegacyRecords(kind,ids){const set=new Set((ids||[]).map(String));let changed=false;for(const id of [...set])changed=crmCanonicalRemoveLegacyRecord(kind,id)||changed;return changed;}

if(typeof module==='object'&&module.exports){module.exports.legacyAdapter={crmCanonicalRoleFromSegment,crmCanonicalSplitCity,crmCanonicalIdentityInput,crmCanonicalLegacyMetadata};}
