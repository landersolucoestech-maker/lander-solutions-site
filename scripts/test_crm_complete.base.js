'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const partyCore=require('./crm_canonical_parties_core.js');
const crmCore=require('./crm_complete_domain.js');

let seq=0,clock=0;
const partyState=partyCore.createState();
const party=partyCore.createService(partyState,{idFactory:(p)=>`${p}_${++seq}`,now:()=>`2026-08-25T13:${String(Math.floor(clock/60)).padStart(2,'0')}:${String(clock++%60).padStart(2,'0')}.000Z`});
const crmState=crmCore.createState();
const crm=crmCore.createService(party,crmState,{idFactory:(p)=>`${p}_${++seq}`,now:()=>`2026-08-25T14:${String(Math.floor(clock/60)).padStart(2,'0')}:${String(clock++%60).padStart(2,'0')}.000Z`});
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${name}`);}catch(error){console.error(`FAIL ${name}`);throw error;}}

const p1=crm.saveContact({fullName:'João Silva',cpf:'529.982.247-25',email:'joao@empresa.test',phone:'11999990000',role:'partner',status:'active',priority:'high'});
test('1 Contato cria Person canônica',()=>{assert(party.getEntity('person',p1.person.id));assert(crm.hasRole('person',p1.person.id,'crm_contact'));});
test('2 Contato não cria identidade paralela no CRM',()=>{assert.equal(crmState.contexts.filter((x)=>x.entityId===p1.person.id).length,1);});

const company=crm.saveCompany({legalName:'Empresa ABC Ltda',tradeName:'Empresa ABC',cnpj:'04.252.011/0001-10',email:'contato@abc.test',roles:['customer','supplier'],segment:'Tecnologia'});
test('3 Empresa cria Organization canônica',()=>{assert(party.getEntity('organization',company.organization.id));});
test('4 Empresa pode ser Cliente + Fornecedor',()=>{const roles=crm.roles('organization',company.organization.id);assert(roles.includes('customer'));assert(roles.includes('supplier'));});

test('5 Contato pode ser vinculado à Empresa',()=>{crm.saveContact({personId:p1.person.id,fullName:'João Silva',organizationId:company.organization.id,positionTitle:'Diretor',department:'Comercial'});const links=party.getOrganizationContacts(company.organization.id);assert(links.some((x)=>x.person.id===p1.person.id&&x.relationship.positionTitle==='Diretor'));});
const p2=crm.saveContact({fullName:'Maria Souza',email:'maria@abc.test',organizationId:company.organization.id,department:'Financeiro'});
test('6 Dois contatos pertencem à mesma Empresa sem duplicá-la',()=>{assert.equal(partyState.organizations.filter((x)=>x.id===company.organization.id).length,1);assert(party.getOrganizationContacts(company.organization.id).length>=2);});

test('7 Pessoa pode possuir múltiplos papéis',()=>{party.assignRole('person',p1.person.id,'customer');const roles=crm.roles('person',p1.person.id);assert(roles.includes('crm_contact')&&roles.includes('partner')&&roles.includes('customer'));});
test('8 Novo papel não duplica entidade',()=>{const before=partyState.people.length;party.assignRole('person',p1.person.id,'customer');assert.equal(partyState.people.length,before);});

test('9 Cliente PF utiliza Person existente',()=>{const before=partyState.people.length;const c=crm.saveCustomer({entityType:'person',entityId:p1.person.id,fullName:'João Silva'});assert.equal(c.entity.id,p1.person.id);assert.equal(partyState.people.length,before);assert(crm.hasRole('person',p1.person.id,'customer'));});
test('10 Cliente PJ utiliza Organization existente',()=>{const before=partyState.organizations.length;const c=crm.saveCustomer({entityType:'organization',entityId:company.organization.id,legalName:'Empresa ABC Ltda'});assert.equal(c.entity.id,company.organization.id);assert.equal(partyState.organizations.length,before);});

const lead=crm.saveLead({identityMode:'person_organization',fullName:'Carlos Lima',email:'carlos@prospect.test',organizationName:'Prospect XPTO Ltda',origin:'Indicação',stage:'new',priority:'high'});
test('11 Lead usa identidade canônica',()=>{assert(lead.personId);assert(lead.organizationId);assert(party.getEntity('person',lead.personId));assert(party.getEntity('organization',lead.organizationId));});
test('12 Pipeline possui exatamente cinco etapas',()=>{assert.deepEqual(crmCore.STAGES,['new','contacted','qualified','proposal','converted']);});
const beforeInteractions=crmState.interactions.length;
crm.changeLeadStage(lead.id,'contacted');
test('13 Mudança de etapa gera histórico e interação',()=>{assert.equal(lead.stage,'contacted');assert(crmState.interactions.length>beforeInteractions);assert(crmState.interactions.some((x)=>x.leadId===lead.id&&x.type==='stage_change'));assert(crmState.history.some((x)=>x.action==='lead.stage.changed'&&x.leadId===lead.id));});
crm.changeLeadStage(lead.id,'qualified');crm.changeLeadStage(lead.id,'proposal');
const personCountBeforeConversion=partyState.people.length,orgCountBeforeConversion=partyState.organizations.length,leadCountBeforeConversion=crmState.leads.length;
const conversion=crm.convertLead(lead.id);
test('14 Conversão Lead → Cliente preserva identidade',()=>{assert.equal(conversion.customerEntityId,lead.organizationId);assert(crm.hasRole('organization',lead.organizationId,'customer'));});
test('15 Conversão não cria Pessoa/Organização desnecessária',()=>{assert.equal(partyState.people.length,personCountBeforeConversion);assert.equal(partyState.organizations.length,orgCountBeforeConversion);});
test('16 Conversão não apaga Lead',()=>{assert.equal(crmState.leads.length,leadCountBeforeConversion);assert(crmState.leads.some((x)=>x.id===lead.id));});
test('17 Conversão preserva histórico e origem',()=>{assert.equal(lead.origin,'Indicação');assert(lead.convertedAt);assert(crmState.history.some((x)=>x.action==='lead.converted'&&x.leadId===lead.id));assert(crmState.interactions.some((x)=>x.leadId===lead.id&&x.type==='stage_change'));});
test('18 Conversão mantém papel Lead e adiciona Customer',()=>{assert(crm.hasRole('person',lead.personId,'lead'));assert(crm.hasRole('organization',lead.organizationId,'customer'));});

const i1=crm.createInteraction({type:'whatsapp',title:'Retorno de proposta',description:'Cliente respondeu.',personId:p1.person.id});
test('19 Interação vinculada a Pessoa por ID',()=>{assert.equal(i1.personId,p1.person.id);assert(!i1.organizationId);});
const i2=crm.createInteraction({type:'meeting',title:'Reunião',organizationId:company.organization.id});
test('20 Interação vinculada a Organização por ID',()=>{assert.equal(i2.organizationId,company.organization.id);});
const i3=crm.createInteraction({type:'follow_up',title:'Retomar contato',leadId:lead.id,followUpAt:'2026-08-30T10:00:00.000Z'});
test('21 Interação vinculada a Lead e Follow-up',()=>{assert.equal(i3.leadId,lead.id);assert.equal(i3.status,'pending');assert(i3.followUpAt);});
test('22 Timeline retorna interações reais relacionadas',()=>{assert(crm.interactionsFor({personId:p1.person.id}).some((x)=>x.id===i1.id));assert(crm.interactionsFor({organizationId:company.organization.id}).some((x)=>x.id===i2.id));});

test('23 CPF/CNPJ continuam validados pela camada canônica',()=>{assert.throws(()=>crm.saveContact({fullName:'CPF ruim',cpf:'111.111.111-11'}),(e)=>e.code==='INVALID_DOCUMENT');assert.throws(()=>crm.saveCompany({legalName:'CNPJ ruim',cnpj:'11.111.111/1111-11'}),(e)=>e.code==='INVALID_DOCUMENT');});
test('24 Potencial duplicidade não sofre merge inseguro por nome',()=>{const a=crm.saveContact({fullName:'Ana Pereira',email:'ana1@test.com'}),b=crm.saveContact({fullName:'Ana Pereira',email:'ana2@test.com'});assert.notEqual(a.person.id,b.person.id);assert(partyState.potentialDuplicates.some((x)=>x.candidateId===b.person.id));});
test('25 Matching forte reutiliza Person',()=>{const before=partyState.people.length;const same=crm.saveContact({fullName:'João Silva',cpf:'52998224725',email:'joao@empresa.test'});assert.equal(same.person.id,p1.person.id);assert.equal(partyState.people.length,before);});

test('26 Remover Contato do CRM não destrói Person',()=>{const id=p2.person.id;assert(crm.archiveEntityContext('person',id));assert(party.getEntity('person',id));assert.equal(crm.getContext('person',id).active,false);});
test('27 Prospect é papel, não entidade separada',()=>{assert(crm.hasRole('organization',lead.organizationId,'prospect'));assert(!('prospects' in crmState));});
test('28 Parceiro/Fornecedor/Prestador são papéis',()=>{party.assignRole('organization',company.organization.id,'partner');party.assignRole('organization',company.organization.id,'service_provider');const roles=crm.roles('organization',company.organization.id);assert(roles.includes('partner')&&roles.includes('supplier')&&roles.includes('service_provider'));});
test('29 Pessoa não é Usuário do sistema',()=>{assert.equal(partyState.userLinks.filter((x)=>x.personId===p1.person.id).length,0);});
test('30 Pessoa pode futuramente ser Colaborador via personId',()=>{const employment={personId:p1.person.id};assert.equal(party.getEntity('person',employment.personId).id,p1.person.id);});

test('31 Busca por dados canônicos é possível sem identidade duplicada',()=>{const blob=crmCore.fold([p1.person.fullName,crm.primary('person',p1.person.id,'email'),crm.primary('person',p1.person.id,'phone')].join(' '));assert(blob.includes('joao'));assert(blob.includes('joao@empresa.test'));});
test('32 Filtros usam enums estáveis de estágio',()=>{assert.equal(crmCore.normalizeStage('Em contato'),'contacted');assert.equal(crmCore.normalizeStage('Qualificado'),'qualified');});
test('33 Interações usam tipos centralizados',()=>{assert.deepEqual(crmCore.INTERACTION_TYPES,['call','email','whatsapp','meeting','message','note','stage_change','follow_up','proposal','commercial_activity']);});

test('34 Migração legada preserva IDs/referências canônicas',()=>{const localParty=partyCore.createState(),ps=partyCore.createService(localParty,{idFactory:(p)=>`${p}_${++seq}`}),person=ps.createPerson({fullName:'Legado'}),localCrm=crmCore.createState(),cs=crmCore.createService(ps,localCrm,{idFactory:(p)=>`${p}_${++seq}`});cs.migrateLegacy({contacts:[{id:'c99',canonicalEntityType:'person',canonicalEntityId:person.id,name:'Legado',status:'Ativo'}],leads:[],isDemo:()=>false});const ctx=cs.getContext('person',person.id);assert.equal(ctx.legacyId,'c99');assert.equal(person.id,ctx.entityId);});
test('35 Migração de lead preserva legacyId',()=>{const localParty=partyCore.createState(),ps=partyCore.createService(localParty,{idFactory:(p)=>`${p}_${++seq}`}),person=ps.createPerson({fullName:'Lead Legado'}),localCrm=crmCore.createState(),cs=crmCore.createService(ps,localCrm,{idFactory:(p)=>`${p}_${++seq}`});cs.migrateLegacy({contacts:[],leads:[{id:'l99',canonicalEntityType:'person',canonicalEntityId:person.id,name:'Lead Legado',stage:'Novo'}],isDemo:()=>false});assert.equal(cs.data.leads[0].legacyId,'l99');assert.equal(cs.data.leads[0].personId,person.id);});

const browserSource=fs.readFileSync(path.join(__dirname,'crm_complete_browser.js'),'utf8');
test('36 CRM novo não escreve diretamente em crmRelContacts',()=>{assert(!/state\.crmRelContacts\s*=|state\.crmRelContacts\.(?:push|unshift|splice)/.test(browserSource));});
test('37 CRM novo não escreve diretamente em crmRelLeads',()=>{assert(!/state\.crmRelLeads\s*=|state\.crmRelLeads\.(?:push|unshift|splice)/.test(browserSource));});
test('38 CRM usa adapters canônicos para projeções legadas',()=>{assert(browserSource.includes("crmCanonicalUpsertLegacyRecord('contacts'"));assert(browserSource.includes("crmCanonicalUpsertLegacyRecord('leads'"));assert(browserSource.includes('crmCanonicalSyncLegacyViews()'));});
test('39 CRM possui exatamente cinco áreas internas',()=>{assert.deepEqual(crmCore.TABS,['contacts','companies','customers','leads','interactions']);assert(browserSource.includes("['contacts','Contatos'],['companies','Empresas'],['customers','Clientes'],['leads','Leads'],['interactions','Interações']"));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.resolve(__dirname,'..','app.js'),'utf8');
  test('40 bundle materializado contém CRM completo',()=>{assert(app.includes('VALTREN CRM COMPLETE START'));assert(app.includes('function crmFullCompaniesView()'));assert(app.includes('function crmFullInteractionsView()'));});
  test('41 cinco áreas não viraram itens do sidebar',()=>{const start=app.lastIndexOf('function crmRelSidebar');const end=app.indexOf('function crmReferenceRoute',start);const sidebar=app.slice(start,end);for(const label of ['Contatos','Empresas','Clientes','Leads','Interações'])assert(!sidebar.includes(`>${label}<`));});
  test('42 sidebar oficial continua apontando para um único CRM',()=>{const start=app.lastIndexOf('function crmRelSidebar');const end=app.indexOf('function crmReferenceRoute',start);const sidebar=app.slice(start,end);assert(sidebar.includes("nav('#/crm/relationships','CRM'"));});
  test('43 deep links internos são gerados pelo mecanismo canônico da tab',()=>{assert(app.includes('function crmFullTabHref(tab)'));assert(app.includes('#/crm/relationships?tab=${tab}'));for(const tab of crmCore.TABS)assert(app.includes(`['${tab}'`)||app.includes(`,'${tab}'`));});
  test('44 Agenda mantém compatibilidade com crmRelContacts',()=>{assert(app.includes('state.crmRelContacts'));assert(app.includes('crmCanonicalSyncLegacyViews'));assert(app.includes('canonicalEntityId'));});
  test('45 CRM materializado não introduz write direto novo nas projeções',()=>{const start=app.indexOf('// VALTREN CRM COMPLETE START'),end=app.indexOf('// VALTREN CRM COMPLETE END',start);const block=app.slice(start,end);assert(!/state\.crmRelContacts\s*=|state\.crmRelLeads\s*=/.test(block));});
}

console.log(`CRM complete tests: ${passed} passed`);
