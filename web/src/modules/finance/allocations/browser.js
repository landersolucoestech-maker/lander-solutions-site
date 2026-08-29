// VALTREN COST ALLOCATIONS BROWSER
function crmCostAllocationProducts(){return typeof crmFinanceProducts==='function'?crmFinanceProducts():[];}
function crmCostAllocationServices(){const rows=[state.businessServices,state.crmBusinessServices,state.negociosServices].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&x.name).map((x)=>({id:String(x.id),name:String(x.name),status:x.status||'active'}));}
function crmCostAllocationUnits(){const rows=[state.businessUnits,state.crmBusinessUnits,state.negociosBusinessUnits].find(Array.isArray)||[];return rows.filter((x)=>x&&x.id&&x.name).map((x)=>({id:String(x.id),name:String(x.name),status:x.status||'active'}));}
function crmCostAllocationResolveDestination(type,id){if(type==='corporate')return true;if(type==='product')return crmCostAllocationProducts().some((x)=>x.id===id);if(type==='service')return crmCostAllocationServices().some((x)=>x.id===id);if(type==='business_unit')return crmCostAllocationUnits().some((x)=>x.id===id);return false;}
function crmCostAllocationService(){
  if(typeof ValtrenCostAllocationCore==='undefined')throw new Error('ValtrenCostAllocationCore indisponível');
  if(typeof crmFinanceService!=='function')throw new Error('Financeiro → Transações canônico indisponível');
  state.crmCostAllocations=ValtrenCostAllocationCore.ensureState(state.crmCostAllocations);
  if(!state.__crmCostAllocationService||state.__crmCostAllocationService.data!==state.crmCostAllocations){
    state.__crmCostAllocationService=ValtrenCostAllocationCore.createService(state.crmCostAllocations,{financeService:()=>crmFinanceService(),actorProvider:()=>state.crmUserId||state.crmUserName||null,resolveDestination:crmCostAllocationResolveDestination});
  }
  const service=state.__crmCostAllocationService;
  if(!service.data.metadata.legacyMigrated)service.migrateLegacyTransactionAllocations();
  return service;
}
function crmCostAllocationMoney(value,currency='BRL'){return Number(value||0).toLocaleString('pt-BR',{style:'currency',currency:currency||'BRL'});}
function crmCostAllocationMethodLabel(value){return {percentage:'Percentual',fixed:'Valor fixo',equal:'Divisão igual',driver:'Direcionador'}[value]||value||'—';}
function crmCostAllocationStatusLabel(value){return {draft:'Rascunho',review:'Em revisão',approved:'Aprovado',posted:'Postado',reversed:'Estornado'}[value]||value||'—';}
function crmCostAllocationStatusClass(value){return `status-${String(value||'draft').replace(/[^a-z]/g,'')}`;}
function crmCostAllocationDestinationLabel(line){
  if(!line)return '—';
  if(line.destinationType==='corporate')return 'Corporativo';
  if(line.destinationType==='product')return crmCostAllocationProducts().find((x)=>x.id===line.destinationId)?.name||line.destinationId;
  if(line.destinationType==='service')return crmCostAllocationServices().find((x)=>x.id===line.destinationId)?.name||line.destinationId;
  if(line.destinationType==='business_unit')return crmCostAllocationUnits().find((x)=>x.id===line.destinationId)?.name||line.destinationId;
  return line.destinationId||line.destinationType;
}
function crmCostAllocationPeriodRange(period,q){
  const today=new Date(),iso=(d)=>d.toISOString().slice(0,10);
  if(period==='month')return [iso(new Date(today.getFullYear(),today.getMonth(),1)),iso(today)];
  if(period==='quarter'){const m=Math.floor(today.getMonth()/3)*3;return [iso(new Date(today.getFullYear(),m,1)),iso(today)];}
  if(period==='year')return [iso(new Date(today.getFullYear(),0,1)),iso(today)];
  if(period==='custom')return [q.get('from')||'',q.get('to')||''];
  return ['',''];
}
function crmCostAllocationCurrentFilters(){
  const q=routeInfo().query,status=['draft','review','approved','posted','reversed'].includes(q.get('status'))?q.get('status'):'all',method=ValtrenCostAllocationCore.METHODS.includes(q.get('method'))?q.get('method'):'',period=q.get('period')||'all',[from,to]=crmCostAllocationPeriodRange(period,q),page=Math.max(1,Number(q.get('page')||1));
  let destinationType='',destinationId='';
  if(q.get('corporate')==='1')destinationType='corporate';
  else if(q.get('product')){destinationType='product';destinationId=q.get('product');}
  else if(q.get('service')){destinationType='service';destinationId=q.get('service');}
  else if(q.get('unit')){destinationType='business_unit';destinationId=q.get('unit');}
  return {status,method,period,from,to,page,limit:50,search:q.get('q')||'',accountId:q.get('account')||'',categoryId:q.get('category')||'',destinationType,destinationId,responsible:q.get('responsible')||''};
}
function crmCostAllocationSetQuery(changes){
  const q=new URLSearchParams(routeInfo().query||new URLSearchParams());
  Object.entries(changes).forEach(([key,value])=>{if(value==null||value===''||value===false||value==='all')q.delete(key);else q.set(key,value===true?'1':String(value));});
  location.hash=`#/crm/financeiro/rateios${q.toString()?`?${q.toString()}`:''}`;
}
function crmCostAllocationSourceLabel(tx){return tx?`${tx.transactionDate||'—'} · ${tx.originalDescription||tx.id}`:'Transação não encontrada';}
function crmCostAllocationEligibleTransactions(){
  const service=crmFinanceService();
  return (service.data.transactions||[]).filter((tx)=>tx&&!tx.isDemo&&tx.status!=='excluded'&&tx.financialNature==='expense'&&tx.direction==='outflow').sort((a,b)=>String(b.transactionDate||'').localeCompare(String(a.transactionDate||'')));
}
function crmCostAllocationSourceOptions(selected=''){
  const finance=crmFinanceService(),alloc=crmCostAllocationService(),rows=crmCostAllocationEligibleTransactions();
  if(!rows.length)return '<option value="">Nenhuma despesa elegível</option>';
  return `<option value="">Selecione uma despesa/transação</option>${rows.map((tx)=>{const active=alloc.activePostedForTransaction(tx.id),account=finance.getAccount(tx.financialAccountId),category=finance.getCategory(tx.categoryId);const suffix=active?` · já rateada (${active.id})`:'';return `<option value="${esc(tx.id)}" ${selected===tx.id?'selected':''}>${esc(`${tx.transactionDate||'—'} · ${tx.originalDescription||tx.id} · ${account?.name||'Conta'} · ${category?.name||'Sem categoria'} · ${crmCostAllocationMoney(tx.amount,tx.currency)} · ${tx.status==='posted'?'Lançada':'Pendente'}${suffix}`)}</option>`;}).join('')}`;
}
function crmCostAllocationDestinationOptions(selectedType='corporate',selectedId=''){
  const selected=(type,id='')=>selectedType===type&&selectedId===id?'selected':'';
  const productOptions=crmCostAllocationProducts().map((x)=>`<option value="product:${esc(x.id)}" ${selected('product',x.id)}>${esc(`Produto · ${x.name}`)}</option>`).join('');
  const serviceOptions=crmCostAllocationServices().map((x)=>`<option value="service:${esc(x.id)}" ${selected('service',x.id)}>${esc(`Serviço · ${x.name}`)}</option>`).join('');
  const unitOptions=crmCostAllocationUnits().map((x)=>`<option value="business_unit:${esc(x.id)}" ${selected('business_unit',x.id)}>${esc(`Unidade de Negócio · ${x.name}`)}</option>`).join('');
  return `<option value="corporate:" ${selected('corporate','')}>Corporativo</option>${productOptions}${serviceOptions}${unitOptions}`;
}
function crmCostAllocationParseDestination(value=''){const [destinationType,...rest]=String(value).split(':');return {destinationType,destinationId:rest.join(':')};}
function crmCostAllocationMethodOptions(value='percentage'){return [['percentage','Percentual'],['fixed','Valor fixo'],['equal','Divisão igual'],['driver','Direcionador']].map(([id,label])=>`<option value="${id}" ${id===value?'selected':''}>${label}</option>`).join('');}
function crmCostAllocationToolbar(filters){
  const finance=crmFinanceService(),products=crmCostAllocationProducts(),services=crmCostAllocationServices(),units=crmCostAllocationUnits();
  return `<section class="crm-alloc-toolbar"><label class="crm-alloc-search">${icon('search',15)}<input id="crm-alloc-search" type="search" value="${esc(filters.search)}" placeholder="Buscar descrição, conta, categoria, responsável, destino ou referência"></label><select id="crm-alloc-period"><option value="all" ${filters.period==='all'?'selected':''}>Todo período</option><option value="month" ${filters.period==='month'?'selected':''}>Este mês</option><option value="quarter" ${filters.period==='quarter'?'selected':''}>Este trimestre</option><option value="year" ${filters.period==='year'?'selected':''}>Este ano</option><option value="custom" ${filters.period==='custom'?'selected':''}>Personalizado</option></select>${filters.period==='custom'?`<input id="crm-alloc-from" type="date" value="${esc(filters.from)}"><input id="crm-alloc-to" type="date" value="${esc(filters.to)}">`:''}<select id="crm-alloc-method"><option value="">Todos os métodos</option>${[['percentage','Percentual'],['fixed','Valor fixo'],['equal','Divisão igual'],['driver','Direcionador']].map(([id,label])=>`<option value="${id}" ${filters.method===id?'selected':''}>${label}</option>`).join('')}</select><details class="crm-alloc-more"><summary>Mais filtros</summary><div><select id="crm-alloc-account"><option value="">Todas as contas</option>${finance.data.accounts.filter((x)=>x.status!=='inactive'&&!x.isDemo).map((x)=>`<option value="${esc(x.id)}" ${filters.accountId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><select id="crm-alloc-category"><option value="">Todas as categorias</option>${finance.data.categories.filter((x)=>x.status==='active').map((x)=>`<option value="${esc(x.id)}" ${filters.categoryId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><select id="crm-alloc-product"><option value="">Todos os Produtos</option>${products.map((x)=>`<option value="${esc(x.id)}" ${filters.destinationType==='product'&&filters.destinationId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><select id="crm-alloc-service"><option value="">Todos os Serviços</option>${services.map((x)=>`<option value="${esc(x.id)}" ${filters.destinationType==='service'&&filters.destinationId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><select id="crm-alloc-unit"><option value="">Todas as Unidades</option>${units.map((x)=>`<option value="${esc(x.id)}" ${filters.destinationType==='business_unit'&&filters.destinationId===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><label class="crm-alloc-check"><input id="crm-alloc-corporate" type="checkbox" ${filters.destinationType==='corporate'?'checked':''}> Corporativo</label><input id="crm-alloc-responsible" value="${esc(filters.responsible)}" placeholder="Responsável / usuário"></div></details></section>`;
}
function crmCostAllocationTabs(filters){
  const service=crmCostAllocationService(),count=(status)=>service.query({status,limit:50}).total;
  return `<nav class="crm-alloc-tabs" aria-label="Status dos Rateios">${[['all','Todos'],['draft','Rascunhos'],['review','Em revisão'],['approved','Aprovados'],['posted','Postados'],['reversed','Estornados']].map(([id,label])=>`<button type="button" class="${filters.status===id?'active':''}" data-action="crm-alloc-status" data-status="${id}">${label}<span>${id==='all'?service.query({limit:50}).total:count(id)}</span></button>`).join('')}</nav>`;
}
function crmCostAllocationActions(row){
  if(row.status==='draft')return `<button type="button" data-action="crm-alloc-edit" data-id="${esc(row.id)}">Editar</button><button type="button" data-action="crm-alloc-review" data-id="${esc(row.id)}">Enviar para revisão</button><button type="button" data-action="crm-alloc-delete" data-id="${esc(row.id)}">Excluir rascunho</button>`;
  if(row.status==='review')return `<button type="button" data-action="crm-alloc-approve" data-id="${esc(row.id)}">Aprovar</button><button type="button" data-action="crm-alloc-return" data-id="${esc(row.id)}">Devolver para ajuste</button>`;
  if(row.status==='approved')return `<button type="button" data-action="crm-alloc-post" data-id="${esc(row.id)}">Postar</button>`;
  if(row.status==='posted')return `<button type="button" data-action="crm-alloc-reverse" data-id="${esc(row.id)}">Estornar</button><button type="button" data-action="crm-alloc-version" data-id="${esc(row.id)}">Criar nova versão</button>`;
  if(row.status==='reversed')return `<button type="button" data-action="crm-alloc-version" data-id="${esc(row.id)}">Criar nova versão</button>`;
  return '';
}
function crmCostAllocationTable(result){
  const service=crmCostAllocationService(),finance=crmFinanceService();
  if(!result.rows.length)return `<section class="crm-alloc-empty"><strong>Nenhum rateio encontrado.</strong><span>Os rateios de custos e despesas compartilhadas aparecerão aqui.</span></section>`;
  return `<section class="crm-alloc-table-card"><div class="crm-alloc-table-wrap"><table class="crm-alloc-table"><thead><tr><th>Data</th><th>Origem</th><th>Descrição</th><th>Valor</th><th>Método</th><th>Destinos</th><th>Status</th><th>Período</th><th>Responsável</th><th>Ação</th></tr></thead><tbody>${result.rows.map((row)=>{const tx=finance.getTransaction(row.sourceTransactionId),lines=service.getLines(row.id);return `<tr><td>${esc(row.effectiveDate||'—')}</td><td><strong>${esc(tx?.originalDescription||row.sourceTransactionId)}</strong><small>${esc(finance.getAccount(tx?.financialAccountId)?.name||'—')}</small></td><td>${esc(row.name||row.description||'Rateio')}<small>v${row.version}${row.consistencyStatus==='needs_review'?' · Necessita revisão':''}</small></td><td class="money">${crmCostAllocationMoney(row.basisAmount,tx?.currency||'BRL')}</td><td>${esc(crmCostAllocationMethodLabel(row.method))}</td><td>${lines.length} destino${lines.length===1?'':'s'}</td><td><span class="crm-alloc-status ${crmCostAllocationStatusClass(row.status)}">${esc(crmCostAllocationStatusLabel(row.status))}</span>${row.consistencyStatus==='needs_review'?'<small class="crm-alloc-warning">Inconsistente</small>':''}</td><td>${esc(row.accountingPeriod||'—')}</td><td>${esc(row.postedBy||row.approvedBy||row.createdBy||'—')}</td><td><button type="button" class="crm-alloc-link" data-action="crm-alloc-detail" data-id="${esc(row.id)}">Ver</button></td></tr>`;}).join('')}</tbody></table></div></section>`;
}
function crmCostAllocationPagination(result,filters){
  const pages=Math.max(1,Math.ceil(result.total/result.limit));if(pages<=1)return '';
  return `<nav class="crm-alloc-pagination"><button type="button" data-action="crm-alloc-page" data-page="${Math.max(1,filters.page-1)}" ${filters.page<=1?'disabled':''}>Anterior</button><span>Página ${filters.page} de ${pages} · ${result.total} rateio${result.total===1?'':'s'}</span><button type="button" data-action="crm-alloc-page" data-page="${Math.min(pages,filters.page+1)}" ${filters.page>=pages?'disabled':''}>Próxima</button></nav>`;
}
function crmCostAllocationsPage(){
  const service=crmCostAllocationService(),filters=crmCostAllocationCurrentFilters(),result=service.query(filters),breadcrumb=crmArchitectureBreadcrumb([{label:'Financeiro',href:'#/crm/financeiro'},{label:'Rateios',href:'#/crm/financeiro/rateios'}]);
  const actions=`<button type="button" class="primary" data-action="crm-alloc-new">${icon('plus',15)} Novo Rateio</button>`;
  const body=`${breadcrumb}${crmCostAllocationTabs(filters)}${crmCostAllocationToolbar(filters)}${crmCostAllocationTable(result)}${crmCostAllocationPagination(result,filters)}`;
  return crmFidelityPage('accounting','rateios','Rateios','Distribuição analítica formal de custos e despesas existentes. Rateio não cria nova transação.',actions,body);
}
function crmCostAllocationOverlay(html){let host=document.getElementById('crm-alloc-overlay');if(!host){host=document.createElement('div');host.id='crm-alloc-overlay';document.body.appendChild(host);}host.innerHTML=html;}
function crmCostAllocationClose(){const host=document.getElementById('crm-alloc-overlay');if(host)host.innerHTML='';}
function crmCostAllocationModal(title,body,wide=true){return `<div class="crm-alloc-backdrop" data-action="crm-alloc-close"></div><div class="crm-alloc-modal ${wide?'wide':''}" role="dialog" aria-modal="true"><header><div><span>Financeiro / Rateios</span><h2>${esc(title)}</h2></div><button type="button" data-action="crm-alloc-close">×</button></header><div class="crm-alloc-modal-body">${body}</div></div>`;}
function crmCostAllocationLineEditor(method,index,line={}){
  const share=line.percentage??line.amount??'',driver=line.driverValue??'';
  return `<div class="crm-alloc-line" data-alloc-line><label><span>Destino</span><select name="destination_${index}">${crmCostAllocationDestinationOptions(line.destinationType||'corporate',line.destinationId||'')}</select></label><label class="crm-alloc-share"><span>${method==='fixed'?'Valor':method==='equal'?'Divisão':method==='driver'?'Percentual derivado':'Percentual'}</span><input name="share_${index}" type="number" min="0" step="0.0001" value="${esc(method==='driver'||method==='equal'?'':share)}" ${method==='equal'||method==='driver'?'disabled':''} placeholder="${method==='fixed'?'0,00':'0,0000'}"></label><label class="crm-alloc-driver"><span>Driver</span><input name="driver_${index}" type="number" min="0" step="0.0001" value="${esc(driver)}" ${method==='driver'?'':'disabled'} placeholder="Valor do direcionador"></label><label><span>Observação</span><input name="note_${index}" value="${esc(line.note||'')}" placeholder="Opcional"></label><button type="button" data-action="crm-alloc-line-remove" aria-label="Remover destino">×</button></div>`;
}
function crmCostAllocationEditorLines(method,lines){const rows=lines?.length?lines:[{destinationType:'corporate',destinationId:'',percentage:100}];return rows.map((line,index)=>crmCostAllocationLineEditor(method,index,line)).join('');}
function crmCostAllocationOpenEditor(id='',presetSource=''){
  const service=crmCostAllocationService(),row=id?service.getAllocation(id):null;
  if(row&&row.status!=='draft'){alert('Somente Rascunhos podem ser editados.');return;}
  const q=routeInfo().query,sourceId=presetSource||row?.sourceTransactionId||q.get('source')||'',method=row?.method||'percentage',lines=row?service.getLines(row.id):[{destinationType:'corporate',destinationId:'',percentage:100}],tx=sourceId?crmFinanceService().getTransaction(sourceId):null;
  if(!row&&sourceId){const active=service.activePostedForTransaction(sourceId);if(active){crmCostAllocationOpenDetail(active.id);return;}}
  const body=`<form id="crm-alloc-editor"><input type="hidden" name="allocationId" value="${esc(row?.id||'')}"><nav class="crm-alloc-steps"><button type="button" class="active" data-action="crm-alloc-step" data-step="1">1. Despesa</button><button type="button" data-action="crm-alloc-step" data-step="2">2. Método</button><button type="button" data-action="crm-alloc-step" data-step="3">3. Destinos</button><button type="button" data-action="crm-alloc-step" data-step="4">4. Prévia</button></nav><section data-alloc-step-panel="1"><h3>Despesa/Transação de origem</h3><label class="crm-alloc-field"><span>Despesa *</span><select name="sourceTransactionId" required>${crmCostAllocationSourceOptions(sourceId)}</select></label><div id="crm-alloc-source-summary">${tx?crmCostAllocationSourceSummary(tx):'<p>Selecione uma despesa para continuar.</p>'}</div></section><section data-alloc-step-panel="2" hidden><h3>Método de distribuição</h3><div class="crm-alloc-form-grid"><label class="crm-alloc-field"><span>Método *</span><select name="method">${crmCostAllocationMethodOptions(method)}</select></label><label class="crm-alloc-check"><input name="allowPartial" type="checkbox" ${row?.allowPartial?'checked':''}> Permitir rateio parcial explicitamente</label><label class="crm-alloc-field"><span>Nome</span><input name="name" value="${esc(row?.name||tx?.originalDescription||'')}" placeholder="Identificação do Rateio"></label><label class="crm-alloc-field"><span>Período contábil</span><input name="accountingPeriod" value="${esc(row?.accountingPeriod||'')}" placeholder="Ex.: 2026-08"></label><label class="crm-alloc-field"><span>Data de vigência</span><input name="effectiveDate" type="date" value="${esc(row?.effectiveDate||tx?.transactionDate||new Date().toISOString().slice(0,10))}"></label><label class="crm-alloc-field full"><span>Descrição / critério</span><textarea name="description">${esc(row?.description||'')}</textarea></label></div><p class="crm-alloc-note">Direcionador aceita valores informados pelo usuário. O sistema não inventa headcount, receita, consumo, horas ou qualquer driver real.</p></section><section data-alloc-step-panel="3" hidden><div class="crm-alloc-step-head"><div><h3>Destinos</h3><p>Edite as linhas diretamente. Corporativo é dimensão própria; Produto, Serviço e Unidade usam referências existentes.</p></div><button type="button" class="secondary" data-action="crm-alloc-line-add">+ Adicionar destino</button></div><div id="crm-alloc-lines">${crmCostAllocationEditorLines(method,lines)}</div><label class="crm-alloc-field full"><span>Observações</span><textarea name="notes">${esc(row?.notes||'')}</textarea></label></section><section data-alloc-step-panel="4" hidden><h3>Prévia e memória de cálculo</h3><div id="crm-alloc-preview"></div></section><footer class="crm-alloc-editor-footer"><button type="button" class="secondary" data-action="crm-alloc-prev">Voltar</button><div><button type="button" class="secondary" data-action="crm-alloc-save">Salvar rascunho</button><button type="button" class="primary" data-action="crm-alloc-next">Continuar</button><button type="button" class="primary" data-action="crm-alloc-submit-review" hidden>Enviar para revisão</button></div></footer></form>`;
  crmCostAllocationOverlay(crmCostAllocationModal(row?'Editar Rateio':'Novo Rateio',body,true));crmCostAllocationEditorSetStep(1);
}
function crmCostAllocationSourceSummary(tx){if(!tx)return '<p>Transação não encontrada.</p>';const finance=crmFinanceService(),account=finance.getAccount(tx.financialAccountId),category=finance.getCategory(tx.categoryId);return `<dl class="crm-alloc-source-summary"><div><dt>Data</dt><dd>${esc(tx.transactionDate||'—')}</dd></div><div><dt>Descrição</dt><dd>${esc(tx.originalDescription||'—')}</dd></div><div><dt>Conta</dt><dd>${esc(account?.name||'—')}</dd></div><div><dt>Categoria</dt><dd>${esc(category?.name||'—')}</dd></div><div><dt>Valor</dt><dd>${esc(crmCostAllocationMoney(tx.amount,tx.currency))}</dd></div><div><dt>Status</dt><dd>${esc(tx.status==='posted'?'Lançada':'Pendente')}</dd></div></dl>`;}
function crmCostAllocationEditorSetStep(step){
  const form=document.getElementById('crm-alloc-editor');if(!form)return;step=Math.max(1,Math.min(4,Number(step)||1));form.dataset.step=String(step);
  form.querySelectorAll('[data-alloc-step-panel]').forEach((panel)=>panel.hidden=Number(panel.dataset.allocStepPanel)!==step);
  form.querySelectorAll('[data-action="crm-alloc-step"]').forEach((btn)=>btn.classList.toggle('active',Number(btn.dataset.step)===step));
  const next=form.querySelector('[data-action="crm-alloc-next"]'),submit=form.querySelector('[data-action="crm-alloc-submit-review"]'),prev=form.querySelector('[data-action="crm-alloc-prev"]');if(next)next.hidden=step===4;if(submit)submit.hidden=step!==4;if(prev)prev.disabled=step===1;
  if(step===4)crmCostAllocationRenderPreview();
}
function crmCostAllocationReadLines(){
  const form=document.getElementById('crm-alloc-editor');if(!form)return [];const method=form.elements.method.value;
  return [...form.querySelectorAll('[data-alloc-line]')].map((row)=>{const destination=crmCostAllocationParseDestination(row.querySelector('select[name^="destination_"]')?.value||'corporate:'),share=row.querySelector('input[name^="share_"]')?.value,driver=row.querySelector('input[name^="driver_"]')?.value,note=row.querySelector('input[name^="note_"]')?.value||'';const line={...destination,note};if(method==='percentage')line.percentage=share;if(method==='fixed')line.amount=share;if(method==='driver')line.driverValue=driver;return line;});
}
function crmCostAllocationEditorPayload(){
  const form=document.getElementById('crm-alloc-editor');if(!form)throw new Error('Editor indisponível');const sourceTransactionId=form.elements.sourceTransactionId.value,tx=crmFinanceService().getTransaction(sourceTransactionId);if(!tx)throw new Error('Selecione uma despesa válida');
  return {allocationId:form.elements.allocationId.value,sourceTransactionId,method:form.elements.method.value,allowPartial:!!form.elements.allowPartial.checked,name:form.elements.name.value,accountingPeriod:form.elements.accountingPeriod.value,effectiveDate:form.elements.effectiveDate.value,description:form.elements.description.value,notes:form.elements.notes.value,lines:crmCostAllocationReadLines(),basisAmount:tx.amount,currency:tx.currency};
}
function crmCostAllocationRenderPreview(){
  const target=document.getElementById('crm-alloc-preview');if(!target)return;try{const payload=crmCostAllocationEditorPayload(),result=crmCostAllocationService().calculate(payload.method,payload.basisAmount,payload.lines,payload.allowPartial);target.innerHTML=`<div class="crm-alloc-preview-summary"><article><span>Valor original</span><strong>${crmCostAllocationMoney(result.basisAmount,payload.currency)}</strong></article><article><span>Distribuído</span><strong>${crmCostAllocationMoney(result.distributedAmount,payload.currency)}</strong></article><article><span>Saldo não distribuído</span><strong>${crmCostAllocationMoney(result.unallocatedAmount,payload.currency)}</strong></article><article><span>Percentual total</span><strong>${result.totalPercentage.toLocaleString('pt-BR',{maximumFractionDigits:6})}%</strong></article></div><div class="crm-alloc-memory-table"><table><thead><tr><th>Destino</th><th>Base/Driver</th><th>Percentual</th><th>Valor</th></tr></thead><tbody>${result.lines.map((line)=>`<tr><td>${esc(crmCostAllocationDestinationLabel(line))}</td><td>${line.driverValue==null?'—':esc(String(line.driverValue))}</td><td>${Number(line.percentage||0).toLocaleString('pt-BR',{maximumFractionDigits:6})}%</td><td>${crmCostAllocationMoney(line.amount,payload.currency)}</td></tr>`).join('')}</tbody><tfoot><tr><th>Total</th><th></th><th>${result.totalPercentage.toLocaleString('pt-BR',{maximumFractionDigits:6})}%</th><th>${crmCostAllocationMoney(result.distributedAmount,payload.currency)}</th></tr></tfoot></table></div>${result.unallocatedAmount?'<p class="crm-alloc-warning-box">Existe saldo não distribuído. O Rateio está explicitamente parcial.</p>':'<p class="crm-alloc-ok-box">Distribuição reconciliada até o centavo.</p>'}`;}catch(error){target.innerHTML=`<div class="crm-alloc-error"><strong>Prévia inválida</strong><span>${esc(error.message)}</span></div>`;}
}
function crmCostAllocationPersistDraft(sendReview=false){
  try{
    const payload=crmCostAllocationEditorPayload(),service=crmCostAllocationService(),active=service.activePostedForTransaction(payload.sourceTransactionId,payload.allocationId);
    if(active)throw new Error(`A transação já possui Rateio postado ativo (${active.id}). Estorne-o antes de substituir a distribuição.`);
    let row=payload.allocationId?service.updateDraft(payload.allocationId,payload):service.createAllocation(payload);
    if(payload.allocationId)service.replaceLines(row.id,payload.lines);
    if(sendReview)row=service.sendToReview(row.id);
    crmCostAllocationClose();crmCostAllocationRefresh();
  }catch(error){alert(error.message);}
}
function crmCostAllocationOpenDetail(id){
  const service=crmCostAllocationService(),row=service.getAllocation(id);if(!row)return;service.refreshConsistency(id);const tx=crmFinanceService().getTransaction(row.sourceTransactionId),lines=service.getLines(id),memory=service.memory(id),history=service.data.history.filter((x)=>x.allocationId===id).slice().reverse(),issues=row.consistencyIssues||[];
  const body=`<div class="crm-alloc-detail-actions">${crmCostAllocationActions(row)}</div>${issues.length?`<div class="crm-alloc-warning-box"><strong>Rateio necessita revisão</strong><span>${esc(issues.join(' · '))}. A memória original foi preservada e o efeito dimensional não é recalculado silenciosamente.</span></div>`:''}<section class="crm-alloc-detail-section"><h3>Resumo</h3><dl class="crm-alloc-detail-grid"><div><dt>Status</dt><dd>${esc(crmCostAllocationStatusLabel(row.status))}</dd></div><div><dt>Versão</dt><dd>${row.version}</dd></div><div><dt>Método</dt><dd>${esc(crmCostAllocationMethodLabel(row.method))}</dd></div><div><dt>Valor-base</dt><dd>${crmCostAllocationMoney(row.basisAmount,tx?.currency||'BRL')}</dd></div><div><dt>Distribuído</dt><dd>${crmCostAllocationMoney(row.distributedAmount,tx?.currency||'BRL')}</dd></div><div><dt>Saldo</dt><dd>${crmCostAllocationMoney(row.unallocatedAmount,tx?.currency||'BRL')}</dd></div><div><dt>Percentual</dt><dd>${Number(row.totalPercentage||0).toLocaleString('pt-BR',{maximumFractionDigits:6})}%</dd></div><div><dt>Período</dt><dd>${esc(row.accountingPeriod||'—')}</dd></div></dl></section><section class="crm-alloc-detail-section"><h3>Transação de origem</h3>${crmCostAllocationSourceSummary(tx)}<a class="crm-alloc-button-link" href="#/crm/financeiro?focus=${encodeURIComponent(row.sourceTransactionId)}">Ver em Transações</a></section><section class="crm-alloc-detail-section"><h3>Memória de cálculo</h3><div class="crm-alloc-memory-table"><table><thead><tr><th>Destino</th><th>Base/Driver</th><th>Percentual</th><th>Valor</th></tr></thead><tbody>${lines.map((line)=>`<tr><td>${esc(crmCostAllocationDestinationLabel(line))}</td><td>${line.driverValue==null?'—':esc(String(line.driverValue))}</td><td>${Number(line.percentage||0).toLocaleString('pt-BR',{maximumFractionDigits:6})}%</td><td>${crmCostAllocationMoney(line.amount,tx?.currency||'BRL')}</td></tr>`).join('')}</tbody><tfoot><tr><th>Total</th><th></th><th>${Number(memory.totalPercentage||0).toLocaleString('pt-BR',{maximumFractionDigits:6})}%</th><th>${crmCostAllocationMoney(memory.distributedAmount,tx?.currency||'BRL')}</th></tr></tfoot></table></div></section><section class="crm-alloc-detail-section"><h3>Status e workflow</h3><dl class="crm-alloc-detail-grid"><div><dt>Criado</dt><dd>${esc(row.createdAt||'—')} · ${esc(row.createdBy||'—')}</dd></div><div><dt>Revisado</dt><dd>${esc(row.reviewedAt||'—')} · ${esc(row.reviewedBy||'—')}</dd></div><div><dt>Aprovado</dt><dd>${esc(row.approvedAt||'—')} · ${esc(row.approvedBy||'—')}</dd></div><div><dt>Postado</dt><dd>${esc(row.postedAt||'—')} · ${esc(row.postedBy||'—')}</dd></div><div><dt>Estornado</dt><dd>${esc(row.reversedAt||'—')} · ${esc(row.reversedBy||'—')}</dd></div></dl></section><section class="crm-alloc-detail-section"><h3>Contabilidade</h3><p>${row.status==='posted'&&row.consistencyStatus==='consistent'?'Rateio postado: a projeção efetiva está disponível em transaction.allocations e pode ser consumida pela análise dimensional. A DRE geral continua usando o valor original uma única vez.':'Sem efeito dimensional oficial neste estado.'}</p></section><section class="crm-alloc-detail-section"><h3>Observações</h3><p>${esc(row.notes||'Nenhuma observação.')}</p></section><section class="crm-alloc-detail-section"><h3>Histórico</h3>${history.length?`<div class="crm-alloc-history">${history.map((event)=>`<article><strong>${esc(event.action)}</strong><span>${esc(event.at)}</span><small>${esc(event.actorId||'Sistema')}</small></article>`).join('')}</div>`:'<p>Nenhum evento registrado.</p>'}</section>`;
  crmCostAllocationOverlay(`<div class="crm-alloc-backdrop" data-action="crm-alloc-close"></div><aside class="crm-alloc-drawer"><header><div><span>Financeiro / Rateios</span><h2>${esc(row.name||'Rateio')}</h2><p>${esc(crmCostAllocationSourceLabel(tx))}</p></div><button type="button" data-action="crm-alloc-close">×</button></header><div class="crm-alloc-drawer-body">${body}</div></aside>`);
}
function crmCostAllocationRefresh(){if(typeof renderCurrentWithoutReset==='function')renderCurrentWithoutReset();}
function crmCostAllocationWorkflow(id,action){
  const service=crmCostAllocationService();try{
    if(action==='review')service.sendToReview(id);
    else if(action==='approve')service.approve(id);
    else if(action==='return'){const reason=prompt('Motivo do ajuste:','')||'';service.returnToDraft(id,reason);}
    else if(action==='post')service.post(id);
    else if(action==='reverse'){const reason=prompt('Motivo do estorno:','')||'';service.reverse(id,reason);}
    else if(action==='delete'){if(!confirm('Excluir este rascunho sem efeito?'))return;service.removeDraft(id);}
    else if(action==='version'){const row=service.createNewVersion(id);crmCostAllocationClose();crmCostAllocationOpenEditor(row.id);return;}
    crmCostAllocationClose();crmCostAllocationRefresh();
  }catch(error){alert(error.message);}
}
if(!window.__valtrenCostAllocationsBound){
  window.__valtrenCostAllocationsBound=true;
  document.addEventListener('click',(event)=>{
    const target=event.target.closest('[data-action]');if(!target)return;const action=target.dataset.action||'';
    if(action==='crm-alloc-new'){crmCostAllocationOpenEditor('',routeInfo().query.get('source')||'');return;}
    if(action==='crm-alloc-close'){crmCostAllocationClose();return;}
    if(action==='crm-alloc-detail'){crmCostAllocationOpenDetail(target.dataset.id);return;}
    if(action==='crm-alloc-edit'){crmCostAllocationOpenEditor(target.dataset.id);return;}
    if(action==='crm-alloc-review'){crmCostAllocationWorkflow(target.dataset.id,'review');return;}
    if(action==='crm-alloc-approve'){crmCostAllocationWorkflow(target.dataset.id,'approve');return;}
    if(action==='crm-alloc-return'){crmCostAllocationWorkflow(target.dataset.id,'return');return;}
    if(action==='crm-alloc-delete'){crmCostAllocationWorkflow(target.dataset.id,'delete');return;}
    if(action==='crm-alloc-post'){crmCostAllocationWorkflow(target.dataset.id,'post');return;}
    if(action==='crm-alloc-reverse'){crmCostAllocationWorkflow(target.dataset.id,'reverse');return;}
    if(action==='crm-alloc-version'){crmCostAllocationWorkflow(target.dataset.id,'version');return;}
    if(action==='crm-alloc-status'){crmCostAllocationSetQuery({status:target.dataset.status,page:1});return;}
    if(action==='crm-alloc-page'){crmCostAllocationSetQuery({page:target.dataset.page});return;}
    if(action==='crm-alloc-step'){crmCostAllocationEditorSetStep(target.dataset.step);return;}
    if(action==='crm-alloc-prev'){const form=document.getElementById('crm-alloc-editor');crmCostAllocationEditorSetStep(Number(form?.dataset.step||1)-1);return;}
    if(action==='crm-alloc-next'){const form=document.getElementById('crm-alloc-editor');crmCostAllocationEditorSetStep(Number(form?.dataset.step||1)+1);return;}
    if(action==='crm-alloc-save'){crmCostAllocationPersistDraft(false);return;}
    if(action==='crm-alloc-submit-review'){crmCostAllocationPersistDraft(true);return;}
    if(action==='crm-alloc-line-add'){const form=document.getElementById('crm-alloc-editor'),box=document.getElementById('crm-alloc-lines');if(!form||!box)return;const index=box.querySelectorAll('[data-alloc-line]').length;box.insertAdjacentHTML('beforeend',crmCostAllocationLineEditor(form.elements.method.value,index,{}));return;}
    if(action==='crm-alloc-line-remove'){const row=target.closest('[data-alloc-line]'),box=document.getElementById('crm-alloc-lines');row?.remove();if(box){const method=document.getElementById('crm-alloc-editor')?.elements.method.value||'percentage';const lines=crmCostAllocationReadLines();box.innerHTML=crmCostAllocationEditorLines(method,lines);}return;}
  });
  document.addEventListener('change',(event)=>{
    const form=document.getElementById('crm-alloc-editor');
    if(form&&event.target===form.elements.sourceTransactionId){const tx=crmFinanceService().getTransaction(event.target.value),summary=document.getElementById('crm-alloc-source-summary');if(summary)summary.innerHTML=tx?crmCostAllocationSourceSummary(tx):'<p>Selecione uma despesa para continuar.</p>';if(tx&&!form.elements.name.value)form.elements.name.value=tx.originalDescription||'';return;}
    if(form&&event.target===form.elements.method){const lines=crmCostAllocationReadLines(),box=document.getElementById('crm-alloc-lines');if(box)box.innerHTML=crmCostAllocationEditorLines(event.target.value,lines);return;}
    if(event.target.id==='crm-alloc-period'){crmCostAllocationSetQuery({period:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-from'){crmCostAllocationSetQuery({from:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-to'){crmCostAllocationSetQuery({to:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-method'){crmCostAllocationSetQuery({method:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-account'){crmCostAllocationSetQuery({account:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-category'){crmCostAllocationSetQuery({category:event.target.value,page:1});return;}
    if(event.target.id==='crm-alloc-product'){crmCostAllocationSetQuery({product:event.target.value,service:'',unit:'',corporate:false,page:1});return;}
    if(event.target.id==='crm-alloc-service'){crmCostAllocationSetQuery({service:event.target.value,product:'',unit:'',corporate:false,page:1});return;}
    if(event.target.id==='crm-alloc-unit'){crmCostAllocationSetQuery({unit:event.target.value,product:'',service:'',corporate:false,page:1});return;}
    if(event.target.id==='crm-alloc-corporate'){crmCostAllocationSetQuery({corporate:event.target.checked,product:'',service:'',unit:'',page:1});return;}
  });
  document.addEventListener('input',(event)=>{
    if(event.target.id==='crm-alloc-search'){clearTimeout(window.__crmAllocSearchTimer);window.__crmAllocSearchTimer=setTimeout(()=>crmCostAllocationSetQuery({q:event.target.value,page:1}),250);}
    if(event.target.id==='crm-alloc-responsible'){clearTimeout(window.__crmAllocResponsibleTimer);window.__crmAllocResponsibleTimer=setTimeout(()=>crmCostAllocationSetQuery({responsible:event.target.value,page:1}),350);}
  });
}
