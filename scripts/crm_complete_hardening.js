// VALTREN CRM COMPLETE HARDENING
function crmFullStatusLabel(value){
  const key=ValtrenCrmCore.fold(value).replace(/[^a-z0-9]+/g,'_');
  return {active:'Ativo',ativo:'Ativo',inactive:'Inativo',inativo:'Inativo',negotiating:'Negociando',negociando:'Negociando',open:'Aberto',aberto:'Aberto',paused:'Pausado',pausado:'Pausado',lost:'Perdido',perdido:'Perdido',converted:'Convertido',convertido:'Convertido',archived:'Arquivado',arquivado:'Arquivado',pending:'Pendente',pendente:'Pendente',completed:'Concluído',concluido:'Concluído',cancelled:'Cancelado',cancelado:'Cancelado'}[key]||value||'-';
}
function crmFullPriorityLabel(value){
  const key=ValtrenCrmCore.fold(value).replace(/[^a-z0-9]+/g,'_');
  return {low:'Baixa',baixa:'Baixa',medium:'Média',media:'Média',high:'Alta',alta:'Alta',strategic:'Estratégica',estrategico:'Estratégica',estrategica:'Estratégica'}[key]||value||'-';
}
function crmFullRoleBadges(roles){
  const visible=(roles||[]).filter((role)=>['customer','prospect','partner','supplier','service_provider','beneficiary','economic_participant','contractual_party'].includes(role));
  if(!visible.length)return '<span class="crm-full-muted">Contato</span>';
  return `<div class="crm-full-badges">${visible.map((role)=>`<span>${esc(crmFullRoleLabel(role))}</span>`).join('')}</div>`;
}
function crmFullSyncLegacyContact(entityType,entityId,legacyId=''){
  const service=crmFullService(),view=crmFullPartyView(entityType,entityId);if(!view)return '';
  const ctx=service.getContext(entityType,entityId,true),id=crmFullLegacyId('c',legacyId||ctx.legacyId),roles=service.roles(entityType,entityId),rel=entityType==='person'?service.party.data.personOrganizationRelationships.find((x)=>x.personId===entityId&&x.status!=='inactive'):null,org=rel?service.party.getEntity('organization',rel.organizationId):null;
  const item={id,tipo_pessoa:entityType==='organization'?'pessoa_juridica':'pessoa_fisica',name:entityType==='organization'?view.entity.legalName:view.entity.fullName,company:entityType==='organization'?(view.entity.tradeName||''):(org?.tradeName||org?.legalName||''),segment:crmFullRoleToLegacy(crmFullPrimaryRole(roles)),profile:'',phone:view.phone,email:view.email,city:[view.address?.city,view.address?.region].filter(Boolean).join(' / '),responsible:crmFullResponsibleName(ctx.responsibleId),status:crmFullStatusLabel(ctx.status||'active'),priority:crmFullPriorityLabel(ctx.priority||'medium'),cpf:entityType==='person'?view.document:'',cnpj:entityType==='organization'?view.document:'',function:rel?.positionTitle||'',address:view.address?.line1||'',notes:ctx.notes||'',interactions:[]};
  const mode=crmCanonicalBinding('crm.contacts',id)?'edit':'create';
  // Compatibility projection: the canonical identity was already resolved above, so exact-name reuse is safe here and prevents a duplicate Organization created only for the legacy view.
  if(!crmCanonicalUpsertLegacyRecord('contacts',item,mode,{legacy:true}))throw new Error('Não foi possível atualizar a projeção de compatibilidade do contato.');
  service.patchContext(entityType,entityId,{legacyId:id});return id;
}
function crmFullSyncLegacyLead(lead){
  const service=crmFullService(),person=lead.personId?crmFullPartyView('person',lead.personId):null,org=lead.organizationId?crmFullPartyView('organization',lead.organizationId):null,id=crmFullLegacyId('l',lead.legacyId),entityType=person?'person':'organization';
  const item={id,tipo_pessoa:entityType==='organization'?'pessoa_juridica':'pessoa_fisica',name:person?.name||org?.legalName||org?.name||'',company:org?.name||'',email:person?.email||org?.email||'',phone:person?.phone||org?.phone||'',source:lead.origin||'',stage:crmFullStageLabel(lead.stage),responsible:crmFullResponsibleName(lead.responsibleId),status:crmFullStatusLabel(lead.status||'open'),priority:crmFullPriorityLabel(lead.priority||'medium'),notes:lead.notes||''};
  const mode=crmCanonicalBinding('crm.leads',id)?'edit':'create';
  if(!crmCanonicalUpsertLegacyRecord('leads',item,mode,{legacy:true}))throw new Error('Não foi possível atualizar a projeção de compatibilidade do lead.');lead.legacyId=id;return id;
}
function crmFullArchive(kind,id){
  const service=crmFullService();
  if(kind==='customer'){
    const [entityType,entityId]=id.split(':');service.party.removeRole(entityType,entityId,'customer');service.history('customer.removed',{entityType,entityId});crmFullPersistAll();return true;
  }
  if(kind==='lead'){
    const lead=service.data.leads.find((x)=>x.id===id);if(!lead)return false;lead.status='archived';lead.updatedAt=new Date().toISOString();service.history('lead.archived',{leadId:id});if(lead.legacyId)crmCanonicalRemoveLegacyRecord('leads',lead.legacyId);crmFullPersistAll();return true;
  }
  if(kind==='interaction'){service.removeInteraction(id);crmFullPersistAll();return true;}
  const entityType=kind==='company'?'organization':'person',ctx=service.getContext(entityType,id,false),legacyId=ctx?.legacyId||'';
  const ok=service.archiveEntityContext(entityType,id);if(legacyId)crmCanonicalRemoveLegacyRecord('contacts',legacyId);crmFullPersistAll();return ok;
}

// Editing a Customer must never silently change the canonical identity type.
const crmFullSerializeFormCanonicalBase=crmFullSerializeForm;
crmFullSerializeForm=function(form){
  const result=crmFullSerializeFormCanonicalBase(form);
  if(form?.dataset?.kind==='customer'&&form?.dataset?.mode==='edit'&&form.dataset.id?.includes(':')){
    const [entityType,entityId]=form.dataset.id.split(':');result.payload.entityType=entityType==='organization'?'organization':'person';result.payload.entityId=entityId||'';
  }
  return result;
};
const crmFullOpenModalCanonicalBase=crmFullOpenModal;
crmFullOpenModal=function(kind,mode='create',id=''){
  crmFullOpenModalCanonicalBase(kind,mode,id);
  if(kind==='customer'&&mode==='edit'){
    const type=document.querySelector('#crm-full-form [name="entityType"]');if(type){type.disabled=true;type.setAttribute('aria-disabled','true');}
    document.querySelectorAll('#crm-full-form [name="existingPersonId"],#crm-full-form [name="existingOrganizationId"]').forEach((el)=>{el.disabled=true;el.setAttribute('aria-disabled','true');});
  }
};
