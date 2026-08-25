// VALTREN FISCAL DOCUMENTS BROWSER
function crmFiscalCompanySettings(){
  const candidates=[state.crmCompanySettings,state.companySettings,state.crmSettings?.company,state.company].filter((x)=>x&&typeof x==='object');
  const source=candidates[0]||{};
  return {
    partyType:source.partyType||source.entityType||'organization',
    partyId:source.partyId||source.organizationId||'',
    legalName:source.legalName||source.razaoSocial||'',
    document:source.cnpj||source.document||'',
    address:source.address||source.endereco||'',
    currency:source.currency||state.crmSettings?.currency||'BRL'
  };
}
function crmFiscalService(){
  if(typeof ValtrenFiscalCore==='undefined')throw new Error('ValtrenFiscalCore indisponível');
  if(typeof crmCanonicalPartyService!=='function')throw new Error('Infraestrutura canônica de Pessoas/Organizações indisponível');
  if(typeof crmFinanceService!=='function')throw new Error('Financeiro → Transações indisponível');
  state.crmFiscalDocuments=ValtrenFiscalCore.ensureState(state.crmFiscalDocuments);
  if(!state.__crmFiscalService||state.__crmFiscalService.data!==state.crmFiscalDocuments){
    state.__crmFiscalService=ValtrenFiscalCore.createService(state.crmFiscalDocuments,{
      partyService:crmCanonicalPartyService(),
      financeService:crmFinanceService(),
      companyProvider:()=>crmFiscalCompanySettings(),
      defaultCurrencyProvider:()=>crmFiscalCompanySettings().currency||'BRL',
      actorProvider:()=>state.crmUserId||state.crmUserName||null,
      integrationValidator:()=>false
    });
  }
  const service=state.__crmFiscalService;
  if(!service.data.metadata.legacyReviewed)service.migrateLegacy(Array.isArray(state.crmRefInvoices)?state.crmRefInvoices:[]);
  return service;
}
function crmFiscalUi(){if(!state.crmFiscalUi)state.crmFiscalUi={pageSize:50};return state.crmFiscalUi;}
function crmFiscalMoney(value,currency='BRL'){return Number(value||0).toLocaleString('pt-BR',{style:'currency',currency:currency||'BRL'});}
function crmFiscalDirectionLabel(value){return value==='incoming'?'Entrada':value==='outgoing'?'Saída':'—';}
function crmFiscalStatusLabel(value){return {draft:'Rascunho',pending:'Pendente',issued:'Emitida · registro interno',received:'Recebida',cancelled:'Cancelada · registro',rejected:'Rejeitada',archived:'Arquivada'}[value]||value||'—';}
function crmFiscalFinancialStatusLabel(value){return {unlinked:'Sem movimentação',pending:'Pendente',partial:'Parcial',settled:'Liquidada'}[value]||value||'—';}
function crmFiscalDocumentTypeLabel(value){return {service:'Nota Fiscal de Serviço',product:'Nota Fiscal de Produto',other:'Outro Documento Fiscal'}[value]||value||'Outro Documento Fiscal';}
function crmFiscalSourceLabel(value,validated=false){if(value==='integration')return validated?'Integração validada':'Integração não validada';return value==='import'?'Importada':'Manual';}
function crmFiscalPartyLabel(type,id){if(!id)return 'Não informado';const party=crmCanonicalPartyService().getEntity(type,id);return party?(type==='person'?party.fullName:(party.tradeName||party.legalName||party.name)):id;}
function crmFiscalPartyDocument(type,id){if(!id)return '';const party=crmCanonicalPartyService();const kind=type==='person'?'cpf':'cnpj';return party.data.documents.find((x)=>x.entityType===type&&x.entityId===id&&x.type===kind)?.value||'';}
function crmFiscalPartyOptions(selectedType='',selectedId=''){
  const service=crmCanonicalPartyService(),opt=(type,id,label)=>`<option value="${esc(`${type}:${id}`)}" ${type===selectedType&&id===selectedId?'selected':''}>${esc(label)}</option>`;
  return `<option value="">Selecionar Pessoa/Organização</option><optgroup label="Pessoas">${service.data.people.filter((x)=>x.status!=='inactive').map((x)=>opt('person',x.id,x.fullName)).join('')}</optgroup><optgroup label="Organizações">${service.data.organizations.filter((x)=>x.status!=='inactive').map((x)=>opt('organization',x.id,x.tradeName||x.legalName)).join('')}</optgroup>`;
}
function crmFiscalProducts(){const rows=[state.businessProducts,state.crmBusinessProducts,state.negociosProducts].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&x.name&&x.status!=='inactive').map((x)=>({id:String(x.id),name:String(x.name)}));}
function crmFiscalServices(){const rows=[state.businessServices,state.crmBusinessServices,state.negociosServices].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&x.name&&x.status!=='inactive').map((x)=>({id:String(x.id),name:String(x.name)}));}
function crmFiscalUnits(){const rows=[state.businessUnits,state.crmBusinessUnits,state.negociosUnits].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&x.name&&x.status!=='inactive').map((x)=>({id:String(x.id),name:String(x.name)}));}
function crmFiscalContracts(){const rows=[state.legalContracts,state.crmLegalContracts,state.contracts].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&(x.name||x.title||x.number)&&x.status!=='inactive').map((x)=>({id:String(x.id),name:String(x.name||x.title||x.number)}));}
function crmFiscalSelectOptions(rows,selected='',empty='Nenhum registro disponível'){return `<option value="">${rows.length?'Não informado':empty}</option>${rows.map((x)=>`<option value="${esc(x.id)}" ${x.id===selected?'selected':''}>${esc(x.name)}</option>`).join('')}`;}
function crmFiscalParseParty(value){const [type,...rest]=String(value||'').split(':');return {type:['person','organization'].includes(type)?type:'',id:rest.join(':')};}
function crmFiscalSetQuery(changes){
  const info=routeInfo(),query=new URLSearchParams(info.query||new URLSearchParams());
  Object.entries(changes).forEach(([key,value])=>{if(value==null||value===''||value==='all')query.delete(key);else query.set(key,String(value));});
  location.hash=`#/crm/financeiro/notas-fiscais${query.toString()?`?${query.toString()}`:''}`;
}
function crmFiscalCurrentFilters(){
  const query=routeInfo().query,direction=['incoming','outgoing'].includes(query.get('direction'))?query.get('direction'):'outgoing';
  return {
    direction,search:query.get('q')||'',status:query.get('status')||'',financialStatus:query.get('financial')||'',
    partyId:query.get('party')||'',productId:query.get('product')||'',serviceId:query.get('service')||'',
    businessUnitId:query.get('unit')||'',linked:query.get('linked')||'',from:query.get('from')||'',to:query.get('to')||'',
    page:Math.max(1,Number(query.get('page')||1)),limit:50
  };
}
function crmFiscalQuery(){
  const service=crmFiscalService(),filters=crmFiscalCurrentFilters(),result=service.list({...filters,offset:0,limit:0}),offset=(filters.page-1)*filters.limit;
  return {filters,total:result.total,rows:result.rows.slice(offset,offset+filters.limit)};
}
function crmFiscalBreadcrumb(){return `<nav class="crm-architecture-breadcrumb" aria-label="Breadcrumb"><a href="#/crm/financeiro">Financeiro</a><span>/</span><strong>Notas Fiscais</strong></nav>`;}
function crmFiscalTabs(){
  const service=crmFiscalService(),filters=crmFiscalCurrentFilters(),count=(direction)=>service.list({direction,limit:0}).total;
  return `<nav class="crm-fiscal-tabs" aria-label="Direção fiscal">${[['incoming','Entrada'],['outgoing','Saída']].map(([id,label])=>`<button type="button" class="${filters.direction===id?'active':''}" data-action="crm-fiscal-direction" data-direction="${id}">${label}<span>${count(id)}</span></button>`).join('')}</nav>`;
}
function crmFiscalToolbar(){
  const filters=crmFiscalCurrentFilters(),parties=crmCanonicalPartyService(),products=crmFiscalProducts(),services=crmFiscalServices(),units=crmFiscalUnits();
  const partyRows=[...parties.data.organizations.map((x)=>({id:x.id,name:x.tradeName||x.legalName})),...parties.data.people.map((x)=>({id:x.id,name:x.fullName}))].filter((x)=>x.id&&x.name);
  return `<div class="crm-fiscal-toolbar">
    <label class="crm-fiscal-search">${icon('search',15)}<input id="crm-fiscal-search" type="search" value="${esc(filters.search)}" placeholder="Buscar número, série, chave, parte, descrição, valor ou documento"></label>
    <input id="crm-fiscal-from" type="date" value="${esc(filters.from)}" aria-label="Data inicial">
    <input id="crm-fiscal-to" type="date" value="${esc(filters.to)}" aria-label="Data final">
    <select id="crm-fiscal-status"><option value="">Todo status fiscal</option>${[['draft','Rascunho'],['pending','Pendente'],['issued','Emitida · registro interno'],['received','Recebida'],['cancelled','Cancelada · registro'],['rejected','Rejeitada']].map(([id,label])=>`<option value="${id}" ${filters.status===id?'selected':''}>${label}</option>`).join('')}</select>
    <select id="crm-fiscal-financial"><option value="">Todo status financeiro</option>${[['unlinked','Sem movimentação'],['pending','Pendente'],['partial','Parcial'],['settled','Liquidada']].map(([id,label])=>`<option value="${id}" ${filters.financialStatus===id?'selected':''}>${label}</option>`).join('')}</select>
    <details class="crm-fiscal-more"><summary>Mais filtros</summary><div>
      <select id="crm-fiscal-party"><option value="">Todo cliente/fornecedor</option>${partyRows.map((x)=>`<option value="${esc(x.id)}" ${filters.partyId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select>
      <select id="crm-fiscal-product">${crmFiscalSelectOptions(products,filters.productId,'Sem produtos cadastrados')}</select>
      <select id="crm-fiscal-service">${crmFiscalSelectOptions(services,filters.serviceId,'Sem serviços cadastrados')}</select>
      <select id="crm-fiscal-unit">${crmFiscalSelectOptions(units,filters.businessUnitId,'Sem unidades cadastradas')}</select>
      <select id="crm-fiscal-linked"><option value="">Com ou sem transação</option><option value="yes" ${filters.linked==='yes'?'selected':''}>Com transação vinculada</option><option value="no" ${filters.linked==='no'?'selected':''}>Sem transação vinculada</option></select>
    </div></details>
  </div>`;
}
function crmFiscalRow(doc){
  const service=crmFiscalService(),settlement=service.settlement(doc.id),taxes=service.documentTaxes(doc.id),retentions=service.documentRetentions(doc.id),links=service.documentLinks(doc.id);
  const party=crmFiscalPartyLabel(doc.counterpartyType,doc.counterpartyId),description=doc.description||service.documentItems(doc.id)[0]?.description||'Sem descrição';
  return `<tr data-fiscal-document="${esc(doc.id)}">
    <td><strong>${esc(doc.issueDate||'—')}</strong><small>${esc(doc.competenceDate?`Competência ${doc.competenceDate}`:'Sem competência')}</small></td>
    <td><strong>${esc(doc.number||'Sem número')}</strong><small>${doc.series?`Série ${esc(doc.series)}`:''}</small></td>
    <td><span class="crm-fiscal-badge">${esc(crmFiscalDocumentTypeLabel(doc.documentType))}</span><small>${esc(crmFiscalSourceLabel(doc.source,doc.integrationValidated))}</small></td>
    <td><strong>${esc(party)}</strong><small>${esc(crmFiscalPartyDocument(doc.counterpartyType,doc.counterpartyId)||'')}</small></td>
    <td class="crm-fiscal-description">${esc(description)}</td>
    <td class="money"><strong>${crmFiscalMoney(doc.netAmount,doc.currency)}</strong><small>Bruto ${crmFiscalMoney(doc.totalAmount,doc.currency)}</small></td>
    <td><span>${taxes.length?`${taxes.length} tributo${taxes.length===1?'':'s'}`:'Sem tributos'}</span><small>${retentions.length?`${retentions.length} retenção${retentions.length===1?'':'ões'}`:'Sem retenções'}</small></td>
    <td><span class="crm-fiscal-status ${esc(doc.status)}">${esc(crmFiscalStatusLabel(doc.status))}</span>${doc.reconciliationStatus==='inconsistent'?'<small class="warning">Totais divergentes</small>':''}</td>
    <td><span class="crm-fiscal-financial ${esc(settlement.status)}">${esc(crmFiscalFinancialStatusLabel(settlement.status))}</span><small>${settlement.status==='partial'?`${crmFiscalMoney(settlement.settledAmount,doc.currency)} / ${crmFiscalMoney(doc.netAmount,doc.currency)}`:settlement.status==='settled'?crmFiscalMoney(settlement.settledAmount,doc.currency):''}</small></td>
    <td>${links.length?`${links.length} transação${links.length===1?'':'ões'}`:'Sem vínculo'}</td>
    <td class="right"><button type="button" data-action="crm-fiscal-detail" data-id="${esc(doc.id)}">Detalhes</button></td>
  </tr>`;
}
function crmFiscalTable(){
  const {filters,total,rows}=crmFiscalQuery(),directionLabel=filters.direction==='incoming'?'entrada':'saída',empty=filters.direction==='incoming'?'Nenhuma nota fiscal de entrada encontrada.':'Nenhuma nota fiscal de saída encontrada.';
  const helper=filters.direction==='incoming'?'As notas recebidas ou importadas aparecerão aqui.':'As notas emitidas ou cadastradas aparecerão aqui.';
  const pages=Math.max(1,Math.ceil(total/filters.limit));
  return `<section class="crm-fiscal-table-card"><header><div><h3>Notas Fiscais de ${crmFiscalDirectionLabel(filters.direction)}</h3><p>Documentos fiscais canônicos relacionados às operações da Valtren.</p></div><span>${total}</span></header>${rows.length?`<div class="crm-fiscal-table-wrap"><table><thead><tr><th>Data</th><th>Número</th><th>Tipo</th><th>${filters.direction==='incoming'?'Fornecedor / Emitente':'Cliente / Tomador'}</th><th>Descrição</th><th>Valor</th><th>Tributos / Retenções</th><th>Status Fiscal</th><th>Status Financeiro</th><th>Vínculo</th><th class="right">Ação</th></tr></thead><tbody>${rows.map(crmFiscalRow).join('')}</tbody></table></div>`:`<div class="crm-fiscal-empty">${icon('file',30)}<strong>${empty}</strong><span>${helper}</span></div>`}<footer class="crm-fiscal-pagination"><span>Página ${filters.page} de ${pages}</span><div><button type="button" data-action="crm-fiscal-page" data-page="${Math.max(1,filters.page-1)}" ${filters.page<=1?'disabled':''}>Anterior</button><button type="button" data-action="crm-fiscal-page" data-page="${Math.min(pages,filters.page+1)}" ${filters.page>=pages?'disabled':''}>Próxima</button></div></footer></section>`;
}
function crmFiscalDocumentsPage(){
  crmFiscalService();
  const actions=`<button type="button" class="primary" data-action="crm-fiscal-create">${crmRefIcon('plus')} Criar Nota</button>`;
  const body=`${crmFiscalBreadcrumb()}${crmFiscalTabs()}${crmFiscalToolbar()}${crmFiscalTable()}`;
  return crmFidelityPage('accounting','invoices','Notas Fiscais','Fonte operacional dos documentos fiscais da Valtren',actions,body);
}
function crmFiscalLegacyInvoicesRoute(){
  const current=location.hash||'#/crm/financeiro/invoices';
  if(current.startsWith('#/crm/financeiro/invoices'))history.replaceState(null,'',current.replace('#/crm/financeiro/invoices','#/crm/financeiro/notas-fiscais'));
  return crmFiscalDocumentsPage();
}
function crmFiscalModalMount(html){
  document.getElementById('crm-fiscal-modal-root')?.remove();
  const root=document.createElement('div');root.id='crm-fiscal-modal-root';root.className='crm-ref-modal-root crm-fiscal-modal-root';root.innerHTML=html;
  document.body.appendChild(root);document.body.classList.add('crm-rel-modal-open');
}
function crmFiscalCloseModal(){document.getElementById('crm-fiscal-modal-root')?.remove();document.body.classList.remove('crm-rel-modal-open');}
function crmFiscalOpenCreate(){
  const body=`<section class="crm-fiscal-create-choice"><h3>Qual tipo de nota deseja registrar?</h3><p>A direção fiscal é independente da movimentação bancária.</p><div><button type="button" data-action="crm-fiscal-create-direction" data-direction="incoming">${icon('download',20)}<strong>Entrada</strong><span>Documento recebido pela Valtren</span></button><button type="button" data-action="crm-fiscal-create-direction" data-direction="outgoing">${icon('upload',20)}<strong>Saída</strong><span>Documento emitido pela Valtren</span></button></div></section>`;
  crmFiscalModalMount(`<div class="crm-ref-modal-backdrop" data-action="crm-fiscal-close-modal"></div><section class="crm-ref-modal"><header><h2>Criar Nota</h2><button type="button" data-action="crm-fiscal-close-modal">×</button></header><div class="crm-ref-modal-body">${body}</div><footer><button type="button" class="secondary" data-action="crm-fiscal-close-modal">Cancelar</button></footer></section>`);
}
function crmFiscalItemRow(index){
  return `<div class="crm-fiscal-line" data-fiscal-item-row><input name="itemDescription" placeholder="Descrição do item" required><input name="itemQuantity" type="number" min="0.0001" step="0.0001" value="1" aria-label="Quantidade"><input name="itemUnit" value="un" aria-label="Unidade"><input name="itemUnitPrice" type="number" min="0" step="0.01" value="0" aria-label="Valor unitário"><input name="itemDiscount" type="number" min="0" step="0.01" value="0" aria-label="Desconto"><button type="button" data-action="crm-fiscal-remove-line" aria-label="Remover item">×</button></div>`;
}
function crmFiscalTaxRow(index){
  return `<div class="crm-fiscal-line tax" data-fiscal-tax-row><input name="taxType" placeholder="Tipo do tributo"><input name="taxCode" placeholder="Código"><input name="taxBase" type="number" min="0" step="0.01" placeholder="Base"><input name="taxRate" type="number" min="0" step="0.0001" placeholder="%"><input name="taxAmount" type="number" min="0" step="0.01" placeholder="Valor"><select name="taxTreatment"><option value="informational">Informativo</option><option value="added">Adicionado ao total</option></select><button type="button" data-action="crm-fiscal-remove-line" aria-label="Remover tributo">×</button></div>`;
}
function crmFiscalRetentionRow(index){
  return `<div class="crm-fiscal-line retention" data-fiscal-retention-row><input name="retentionType" placeholder="Tipo da retenção"><input name="retentionBase" type="number" min="0" step="0.01" placeholder="Base"><input name="retentionRate" type="number" min="0" step="0.0001" placeholder="%"><input name="retentionAmount" type="number" min="0" step="0.01" placeholder="Valor"><button type="button" data-action="crm-fiscal-remove-line" aria-label="Remover retenção">×</button></div>`;
}
function crmFiscalOpenForm(direction){
  const incoming=direction==='incoming',products=crmFiscalProducts(),services=crmFiscalServices(),units=crmFiscalUnits(),contracts=crmFiscalContracts(),company=crmFiscalCompanySettings();
  const body=`<input type="hidden" name="direction" value="${direction}">
    <section class="crm-fiscal-form-section"><header><h3>${incoming?'Nota de Entrada':'Nota de Saída'}</h3><p>${incoming?'Documento recebido de fornecedor/emitente.':'Documento emitido pela Valtren para cliente/tomador.'}</p></header>
      <div class="crm-fiscal-form-grid">
        <label><span>${incoming?'Fornecedor / Emitente':'Cliente / Tomador'} *</span><select name="counterparty" required>${crmFiscalPartyOptions()}</select></label>
        <label><span>Número</span><input name="number" placeholder="Preencher quando existir"></label>
        <label><span>Série</span><input name="series"></label>
        <label><span>Tipo documental *</span><select name="documentType"><option value="service">Nota Fiscal de Serviço</option><option value="product">Nota Fiscal de Produto</option><option value="other">Outro Documento Fiscal</option></select></label>
        <label><span>Modelo</span><input name="model" placeholder="Opcional"></label>
        <label><span>Data de emissão</span><input name="issueDate" type="date"></label>
        <label><span>Competência fiscal</span><input name="competenceDate" type="date"></label>
        <label><span>Status fiscal *</span><select name="status"><option value="draft">Rascunho</option><option value="pending">Pendente</option>${incoming?'<option value="received">Recebida</option>':'<option value="issued">Emitida · registro interno</option>'}<option value="rejected">Rejeitada</option></select></label>
        <label><span>Moeda *</span><input name="currency" value="${esc(company.currency||'BRL')}" maxlength="3" required></label>
        <label><span>Chave de acesso</span><input name="accessKey" placeholder="Não será gerada pelo sistema"></label>
        <label><span>ID externo</span><input name="externalId"></label>
      </div>
      <label class="full"><span>Descrição</span><textarea name="description" placeholder="Descrição geral da operação fiscal"></textarea></label>
    </section>
    <section class="crm-fiscal-form-section"><header><h3>Itens</h3><button type="button" data-action="crm-fiscal-add-item">${icon('plus',14)} Adicionar item</button></header><div class="crm-fiscal-lines" id="crm-fiscal-items">${crmFiscalItemRow(0)}</div><div class="crm-fiscal-form-grid compact"><label><span>Desconto do documento</span><input name="discountAmount" type="number" min="0" step="0.01" value="0"></label><label><span>Deduções</span><input name="deductionAmount" type="number" min="0" step="0.01" value="0"></label></div></section>
    <section class="crm-fiscal-form-section"><header><h3>Tributos</h3><button type="button" data-action="crm-fiscal-add-tax">${icon('plus',14)} Adicionar tributo</button></header><p class="crm-fiscal-help">Registre somente dados fiscais reais. Nenhuma alíquota é inferida automaticamente.</p><div class="crm-fiscal-lines" id="crm-fiscal-taxes">${crmFiscalTaxRow(0)}</div></section>
    <section class="crm-fiscal-form-section"><header><h3>Retenções</h3><button type="button" data-action="crm-fiscal-add-retention">${icon('plus',14)} Adicionar retenção</button></header><div class="crm-fiscal-lines" id="crm-fiscal-retentions">${crmFiscalRetentionRow(0)}</div></section>
    <section class="crm-fiscal-form-section"><header><h3>Relacionamentos</h3><p>Somente referências; os cadastros pertencem aos módulos responsáveis.</p></header><div class="crm-fiscal-form-grid">
      <label><span>Produto/Sistema</span><select name="productId" ${products.length?'':'disabled'}>${crmFiscalSelectOptions(products,'','Sem produtos cadastrados')}</select></label>
      <label><span>Serviço</span><select name="serviceId" ${services.length?'':'disabled'}>${crmFiscalSelectOptions(services,'','Sem serviços cadastrados')}</select></label>
      <label><span>Unidade de Negócio</span><select name="businessUnitId" ${units.length?'':'disabled'}>${crmFiscalSelectOptions(units,'','Sem unidades cadastradas')}</select></label>
      <label><span>Contrato</span><select name="contractId" ${contracts.length?'':'disabled'}>${crmFiscalSelectOptions(contracts,'','Sem contratos disponíveis')}</select></label>
    </div></section>
    <section class="crm-fiscal-form-section"><header><h3>Documentos e anexos</h3><p>Este ambiente registra metadados/referências. Não simula armazenamento de XML/PDF nem DANFE oficial.</p></header><div class="crm-fiscal-form-grid">
      <label><span>XML · nome do arquivo</span><input name="xmlFileName"></label><label><span>XML · hash</span><input name="xmlHash"></label><label><span>XML · referência de storage</span><input name="xmlStorageReference"></label>
      <label><span>PDF · nome do arquivo</span><input name="pdfFileName"></label><label><span>PDF · referência de storage</span><input name="pdfStorageReference"></label>
    </div><label class="full"><span>Observações</span><textarea name="notes"></textarea></label></section>`;
  crmFiscalModalMount(crmRefModal(`Criar Nota Fiscal · ${incoming?'Entrada':'Saída'}`,body,'crm-fiscal-create-form',true).replace('id="crm-ref-modal-root"',''));
}
function crmFiscalRowsFromForm(form,selector,names,mapper){
  return [...form.querySelectorAll(selector)].map((row)=>{const obj={};names.forEach((name)=>obj[name]=row.querySelector(`[name="${name}"]`)?.value??'');return mapper(obj);}).filter((row)=>Object.values(row).some((value)=>String(value||'').trim()&&String(value)!=='0'));
}
function crmFiscalCreateFromForm(form){
  const fd=new FormData(form),counterparty=crmFiscalParseParty(fd.get('counterparty'));
  const items=crmFiscalRowsFromForm(form,'[data-fiscal-item-row]',['itemDescription','itemQuantity','itemUnit','itemUnitPrice','itemDiscount'],(x)=>({description:x.itemDescription,quantity:x.itemQuantity,unit:x.itemUnit,unitPrice:x.itemUnitPrice,discountAmount:x.itemDiscount}));
  const taxes=crmFiscalRowsFromForm(form,'[data-fiscal-tax-row]',['taxType','taxCode','taxBase','taxRate','taxAmount','taxTreatment'],(x)=>({taxType:x.taxType,taxCode:x.taxCode,baseAmount:x.taxBase,rate:x.taxRate,amount:x.taxAmount,treatment:x.taxTreatment})).filter((x)=>x.taxType||x.taxCode||x.baseAmount||x.rate||x.amount);
  const retentions=crmFiscalRowsFromForm(form,'[data-fiscal-retention-row]',['retentionType','retentionBase','retentionRate','retentionAmount'],(x)=>({type:x.retentionType,baseAmount:x.retentionBase,rate:x.retentionRate,amount:x.retentionAmount})).filter((x)=>x.type||x.baseAmount||x.rate||x.amount);
  const xmlMetadata=fd.get('xmlFileName')||fd.get('xmlHash')||fd.get('xmlStorageReference')?{fileName:fd.get('xmlFileName'),hash:fd.get('xmlHash'),storageReference:fd.get('xmlStorageReference'),mimeType:'application/xml',source:'metadata'}:{};
  const pdfMetadata=fd.get('pdfFileName')||fd.get('pdfStorageReference')?{fileName:fd.get('pdfFileName'),storageReference:fd.get('pdfStorageReference'),mimeType:'application/pdf',source:'metadata'}:{};
  return crmFiscalService().createDocument({
    direction:fd.get('direction'),documentType:fd.get('documentType'),model:fd.get('model'),number:fd.get('number'),series:fd.get('series'),
    externalId:fd.get('externalId'),accessKey:fd.get('accessKey'),status:fd.get('status'),issueDate:fd.get('issueDate'),competenceDate:fd.get('competenceDate'),
    counterpartyType:counterparty.type,counterpartyId:counterparty.id,currency:String(fd.get('currency')||'').toUpperCase(),
    description:fd.get('description'),discountAmount:fd.get('discountAmount'),deductionAmount:fd.get('deductionAmount'),items,taxes,retentions,
    productId:fd.get('productId'),serviceId:fd.get('serviceId'),businessUnitId:fd.get('businessUnitId'),contractId:fd.get('contractId'),
    xmlMetadata,pdfMetadata,notes:fd.get('notes'),source:'manual'
  });
}
function crmFiscalDetailSection(title,body){return `<section class="crm-fiscal-detail-section"><h3>${esc(title)}</h3>${body}</section>`;}
function crmFiscalOpenDetail(id){
  const service=crmFiscalService(),doc=service.getDocument(id);if(!doc)return;
  document.getElementById('crm-fiscal-drawer')?.remove();
  const settlement=service.settlement(id),items=service.documentItems(id),taxes=service.documentTaxes(id),retentions=service.documentRetentions(id),attachments=service.documentAttachments(id),links=service.documentLinks(id),suggestions=service.suggestTransactions(id,6),finance=crmFinanceService();
  const table=(headers,rows,empty)=>rows.length?`<div class="crm-fiscal-detail-table"><table><thead><tr>${headers.map((x)=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`:`<p class="crm-fiscal-muted">${esc(empty)}</p>`;
  const linkedRows=links.map((link)=>{const tx=finance.getTransaction(link.transactionId);if(!tx)return '';return `<tr><td>${esc(tx.transactionDate||'—')}</td><td>${esc(tx.originalDescription||'Sem descrição')}</td><td>${esc(crmFinanceAccountLabel(tx.financialAccountId))}</td><td>${crmFiscalMoney(tx.amount,tx.currency)}</td><td>${esc(crmFinanceStatusLabel(tx.status))}</td><td>${esc(crmFinanceReconLabel(tx.reconciliationStatus))}</td><td><button type="button" data-action="crm-fiscal-view-transaction" data-id="${esc(tx.id)}">Ver em Transações</button><button type="button" data-action="crm-fiscal-unlink-transaction" data-document="${esc(id)}" data-transaction="${esc(tx.id)}">Desvincular</button></td></tr>`;});
  const suggestionRows=suggestions.map(({tx,score,reasons})=>`<tr><td>${esc(tx.transactionDate||'—')}</td><td>${esc(tx.originalDescription||'Sem descrição')}</td><td>${crmFiscalMoney(tx.amount,tx.currency)}</td><td>${esc(crmFinanceCounterpartyLabel(tx))}</td><td>${score} · ${esc(reasons.join(', '))}</td><td><button type="button" data-action="crm-fiscal-link-transaction" data-document="${esc(id)}" data-transaction="${esc(tx.id)}">Vincular</button></td></tr>`);
  const historyRows=service.data.history.filter((row)=>row.documentId===id).slice().reverse().map((row)=>`<tr><td>${esc(row.at)}</td><td>${esc(row.action)}</td><td>${esc(row.actorId||'Sistema')}</td></tr>`);
  const html=`<aside class="crm-fiscal-drawer" id="crm-fiscal-drawer"><header><div><small>${esc(crmFiscalDirectionLabel(doc.direction))}</small><h2>Nota Fiscal ${esc(doc.number||'sem número')}</h2><p>${esc(crmFiscalStatusLabel(doc.status))} · ${esc(crmFiscalSourceLabel(doc.source,doc.integrationValidated))}</p></div><button type="button" data-action="crm-fiscal-close-drawer">×</button></header><div class="crm-fiscal-drawer-body">
    ${doc.missingInstitutionalData?`<div class="crm-fiscal-warning">${icon('alert',16)} Dados institucionais da Valtren estão incompletos em Configurações → Empresa. Nenhum dado foi inventado.</div>`:''}
    ${doc.potentialDuplicate?`<div class="crm-fiscal-warning">${icon('alert',16)} Possível duplicidade detectada por emitente/destinatário + número + série.</div>`:''}
    ${doc.reconciliationStatus==='inconsistent'?`<div class="crm-fiscal-warning">${icon('alert',16)} Totais importados/informados não reconciliam: ${esc(doc.reconciliationIssues.join(', '))}.</div>`:''}
    ${crmFiscalDetailSection('Dados gerais',`<dl class="crm-fiscal-dl"><div><dt>Direção</dt><dd>${esc(crmFiscalDirectionLabel(doc.direction))}</dd></div><div><dt>Tipo</dt><dd>${esc(crmFiscalDocumentTypeLabel(doc.documentType))}</dd></div><div><dt>Número / Série</dt><dd>${esc(doc.number||'—')} ${doc.series?`/ ${esc(doc.series)}`:''}</dd></div><div><dt>Emissão</dt><dd>${esc(doc.issueDate||'—')}</dd></div><div><dt>Competência fiscal</dt><dd>${esc(doc.competenceDate||'—')}</dd></div><div><dt>Moeda</dt><dd>${esc(doc.currency)}</dd></div><div><dt>Valor bruto</dt><dd>${crmFiscalMoney(doc.totalAmount,doc.currency)}</dd></div><div><dt>Valor líquido</dt><dd>${crmFiscalMoney(doc.netAmount,doc.currency)}</dd></div><div><dt>Status financeiro</dt><dd>${esc(crmFiscalFinancialStatusLabel(settlement.status))}</dd></div><div><dt>Saldo</dt><dd>${crmFiscalMoney(settlement.balance,doc.currency)}</dd></div></dl>`) }
    ${crmFiscalDetailSection('Partes',`<dl class="crm-fiscal-dl"><div><dt>Emitente</dt><dd>${esc(crmFiscalPartyLabel(doc.issuerPartyType,doc.issuerPartyId))}</dd></div><div><dt>Destinatário</dt><dd>${esc(crmFiscalPartyLabel(doc.recipientPartyType,doc.recipientPartyId))}</dd></div><div><dt>${doc.direction==='incoming'?'Fornecedor':'Cliente'}</dt><dd>${esc(crmFiscalPartyLabel(doc.counterpartyType,doc.counterpartyId))}</dd></div></dl>`) }
    ${crmFiscalDetailSection('Itens',table(['Descrição','Qtd.','Un.','Unitário','Desconto','Total'],items.map((x)=>`<tr><td>${esc(x.description)}</td><td>${x.quantity}</td><td>${esc(x.unit)}</td><td>${crmFiscalMoney(x.unitPrice,doc.currency)}</td><td>${crmFiscalMoney(x.discountAmount,doc.currency)}</td><td>${crmFiscalMoney(x.totalAmount,doc.currency)}</td></tr>`),'Nenhum item individualizado neste documento.'))}
    ${crmFiscalDetailSection('Tributos',table(['Tipo','Código','Base','Alíquota','Valor','Tratamento'],taxes.map((x)=>`<tr><td>${esc(x.taxType)}</td><td>${esc(x.taxCode||'—')}</td><td>${crmFiscalMoney(x.baseAmount,doc.currency)}</td><td>${x.rate==null?'—':`${x.rate}%`}</td><td>${crmFiscalMoney(x.amount,doc.currency)}</td><td>${esc(x.treatment==='added'?'Adicionado':'Informativo')}</td></tr>`),'Nenhum tributo registrado.'))}
    ${crmFiscalDetailSection('Retenções',table(['Tipo','Base','Alíquota','Valor'],retentions.map((x)=>`<tr><td>${esc(x.type)}</td><td>${crmFiscalMoney(x.baseAmount,doc.currency)}</td><td>${x.rate==null?'—':`${x.rate}%`}</td><td>${crmFiscalMoney(x.amount,doc.currency)}</td></tr>`),'Nenhuma retenção registrada.'))}
    ${crmFiscalDetailSection('Relacionamentos',`<dl class="crm-fiscal-dl"><div><dt>Produto/Sistema</dt><dd>${esc(crmFiscalProducts().find((x)=>x.id===doc.productId)?.name||doc.productId||'—')}</dd></div><div><dt>Serviço</dt><dd>${esc(crmFiscalServices().find((x)=>x.id===doc.serviceId)?.name||doc.serviceId||'—')}</dd></div><div><dt>Unidade</dt><dd>${esc(crmFiscalUnits().find((x)=>x.id===doc.businessUnitId)?.name||doc.businessUnitId||'—')}</dd></div><div><dt>Contrato</dt><dd>${esc(crmFiscalContracts().find((x)=>x.id===doc.contractId)?.name||doc.contractId||'—')}</dd></div></dl>`) }
    ${crmFiscalDetailSection('Transações vinculadas',`${table(['Data','Descrição','Conta','Valor','Status','Conciliação','Ação'],linkedRows.filter(Boolean),'Nenhuma transação vinculada.')}<div class="crm-fiscal-settlement"><strong>Liquidado: ${crmFiscalMoney(settlement.settledAmount,doc.currency)}</strong><span>Saldo: ${crmFiscalMoney(settlement.balance,doc.currency)}</span></div>${suggestions.length?`<h4>Sugestões de correspondência</h4>${table(['Data','Descrição','Valor','Contraparte','Critérios','Ação'],suggestionRows,'')}`:'<p class="crm-fiscal-muted">Nenhuma sugestão segura disponível. Nenhum vínculo é realizado automaticamente.</p>'}`)}
    ${crmFiscalDetailSection('Documentos e anexos',attachments.length?`<ul class="crm-fiscal-attachments">${attachments.map((x)=>`<li><strong>${esc(x.kind.toUpperCase())}</strong><span>${esc(x.fileName||'Sem nome')}</span><small>${esc(x.storageReference||'Somente metadata; arquivo não armazenado neste módulo')}</small></li>`).join('')}</ul>`:'<p class="crm-fiscal-muted">Nenhum XML, PDF ou anexo referenciado.</p>')}
    ${crmFiscalDetailSection('Observações',`<p>${esc(doc.notes||doc.description||'Sem observações.')}</p>`)}
    ${crmFiscalDetailSection('Histórico',table(['Data/Hora','Evento','Usuário'],historyRows,'Nenhum evento.'))}
  </div><footer>${doc.status!=='cancelled'&&doc.status!=='archived'?'<button type="button" class="secondary" data-action="crm-fiscal-mark-cancelled" data-id="'+esc(doc.id)+'">Marcar como cancelada · registro</button>':''}<button type="button" data-action="crm-fiscal-close-drawer">Fechar</button></footer></aside>`;
  document.body.insertAdjacentHTML('beforeend',html);
}
function crmFiscalCloseDrawer(){document.getElementById('crm-fiscal-drawer')?.remove();}
function crmFiscalAccountingFeed(filters={}){return crmFiscalService().accountingFeed(filters);}
function crmFiscalRerender(){if(typeof renderCurrentWithoutReset==='function')renderCurrentWithoutReset();else if(typeof render==='function')render();}
function crmFiscalRenderDetail(id){crmFiscalCloseDrawer();crmFiscalOpenDetail(id);}

if(!window.__valtrenFiscalBound){
  window.__valtrenFiscalBound=true;
  let fiscalSearchTimer=null;
  document.addEventListener('click',(event)=>{
    const t=event.target.closest('[data-action]');if(!t)return;const action=t.dataset.action;
    if(action==='crm-fiscal-create'){event.preventDefault();crmFiscalOpenCreate();return;}
    if(action==='crm-fiscal-create-direction'){event.preventDefault();crmFiscalOpenForm(t.dataset.direction);return;}
    if(action==='crm-fiscal-direction'){event.preventDefault();crmFiscalSetQuery({direction:t.dataset.direction,page:1});return;}
    if(action==='crm-fiscal-page'){event.preventDefault();crmFiscalSetQuery({page:t.dataset.page});return;}
    if(action==='crm-fiscal-detail'){event.preventDefault();crmFiscalOpenDetail(t.dataset.id);return;}
    if(action==='crm-fiscal-close-drawer'){event.preventDefault();crmFiscalCloseDrawer();return;}
    if(action==='crm-fiscal-close-modal'||(action==='crm-ref-modal-close'&&t.closest('#crm-fiscal-modal-root'))||(event.target.classList.contains('crm-ref-modal-backdrop')&&event.target.closest('#crm-fiscal-modal-root'))){event.preventDefault();crmFiscalCloseModal();return;}
    if(action==='crm-fiscal-add-item'){event.preventDefault();document.getElementById('crm-fiscal-items')?.insertAdjacentHTML('beforeend',crmFiscalItemRow(document.querySelectorAll('[data-fiscal-item-row]').length));return;}
    if(action==='crm-fiscal-add-tax'){event.preventDefault();document.getElementById('crm-fiscal-taxes')?.insertAdjacentHTML('beforeend',crmFiscalTaxRow(document.querySelectorAll('[data-fiscal-tax-row]').length));return;}
    if(action==='crm-fiscal-add-retention'){event.preventDefault();document.getElementById('crm-fiscal-retentions')?.insertAdjacentHTML('beforeend',crmFiscalRetentionRow(document.querySelectorAll('[data-fiscal-retention-row]').length));return;}
    if(action==='crm-fiscal-remove-line'){event.preventDefault();t.closest('.crm-fiscal-line')?.remove();return;}
    if(action==='crm-fiscal-link-transaction'){event.preventDefault();try{crmFiscalService().linkTransaction(t.dataset.document,t.dataset.transaction);crmFiscalRenderDetail(t.dataset.document);crmFiscalRerender();}catch(error){alert(error.message);}return;}
    if(action==='crm-fiscal-unlink-transaction'){event.preventDefault();crmFiscalService().unlinkTransaction(t.dataset.document,t.dataset.transaction);crmFiscalRenderDetail(t.dataset.document);crmFiscalRerender();return;}
    if(action==='crm-fiscal-view-transaction'){event.preventDefault();const tx=crmFinanceService().getTransaction(t.dataset.id);if(tx)location.hash=`#/crm/financeiro?status=${encodeURIComponent(tx.status)}&q=${encodeURIComponent(tx.externalId||tx.originalDescription||tx.id)}`;return;}
    if(action==='crm-fiscal-mark-cancelled'){event.preventDefault();if(confirm('Isto apenas registra que o documento foi cancelado externamente/manual. Não executa cancelamento oficial.')){crmFiscalService().markCancelled(t.dataset.id,{source:'manual-record'});crmFiscalRenderDetail(t.dataset.id);crmFiscalRerender();}return;}
  });
  document.addEventListener('submit',(event)=>{
    const form=event.target;if(!(form instanceof HTMLFormElement))return;
    if(form.id==='crm-fiscal-direction-form'){event.preventDefault();return;}
    if(form.id==='crm-fiscal-create-form'){event.preventDefault();try{const doc=crmFiscalCreateFromForm(form);crmFiscalCloseModal();crmFiscalSetQuery({direction:doc.direction,page:1});}catch(error){alert(error.message);}return;}
  });
  document.addEventListener('input',(event)=>{
    const t=event.target;if(t?.id!=='crm-fiscal-search')return;clearTimeout(fiscalSearchTimer);fiscalSearchTimer=setTimeout(()=>crmFiscalSetQuery({q:t.value,page:1}),250);
  });
  document.addEventListener('change',(event)=>{
    const t=event.target;if(!t?.id)return;
    const map={
      'crm-fiscal-from':'from','crm-fiscal-to':'to','crm-fiscal-status':'status','crm-fiscal-financial':'financial',
      'crm-fiscal-party':'party','crm-fiscal-product':'product','crm-fiscal-service':'service','crm-fiscal-unit':'unit','crm-fiscal-linked':'linked'
    };
    if(map[t.id])crmFiscalSetQuery({[map[t.id]]:t.value,page:1});
  });
  document.addEventListener('keydown',(event)=>{
    if(event.key==='Escape'){if(document.getElementById('crm-fiscal-modal-root'))crmFiscalCloseModal();else crmFiscalCloseDrawer();}
  });
}