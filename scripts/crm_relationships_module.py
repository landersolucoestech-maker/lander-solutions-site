from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-relationships-v1"
MARKER = "/* VALTREN CRM RELATIONSHIPS */"

JS_BLOCK = r'''  function crmRelEnsureState(){
    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];
    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];
  }

  function crmRelActions(kind,id){
    return `<div class="crm-rel-actions">
      <button type="button" class="crm-rel-more" data-action="crm-rel-row-menu" aria-label="Ações">•••</button>
      <div class="crm-rel-actions-menu" hidden>
        <button type="button" data-action="crm-rel-view" data-kind="${kind}" data-id="${id}">Visualizar</button>
        <button type="button" data-action="crm-rel-edit" data-kind="${kind}" data-id="${id}">Editar</button>
        <button type="button" class="danger" data-action="crm-rel-delete" data-kind="${kind}" data-id="${id}">Excluir</button>
      </div>
    </div>`;
  }

  function crmRelContactRows(){
    crmRelEnsureState();
    return state.crmRelContacts.map((item) => `<tr data-crm-row data-search="${esc([item.name,item.company,item.email,item.phone,item.city,item.segment,item.responsible].join(' ').toLowerCase())}" data-filter="${esc(item.segment.toLowerCase())}">
      <td class="crm-rel-check"><input type="checkbox" data-crm-select="contacts" value="${esc(item.id)}" aria-label="Selecionar contato"></td>
      <td><strong>${esc(item.name)}</strong>${item.company ? `<small>${esc(item.company)}</small>` : ''}</td>
      <td>${esc(item.segment)}</td>
      <td><span>${esc(item.phone || '-')}</span><small>${esc(item.email || '-')}</small></td>
      <td>${esc(item.city || '-')}</td>
      <td>${esc(item.responsible || '-')}</td>
      <td><span class="crm-rel-status">${esc(item.status || '-')}</span></td>
      <td class="crm-rel-actions-cell">${crmRelActions('contacts',item.id)}</td>
    </tr>`).join('');
  }

  function crmRelLeadRows(){
    crmRelEnsureState();
    return state.crmRelLeads.map((item) => `<tr data-crm-row data-search="${esc([item.name,item.company,item.email,item.phone,item.source,item.stage,item.responsible].join(' ').toLowerCase())}" data-filter="${esc(item.stage.toLowerCase())}">
      <td class="crm-rel-check"><input type="checkbox" data-crm-select="leads" value="${esc(item.id)}" aria-label="Selecionar lead"></td>
      <td><strong>${esc(item.name)}</strong><small>${esc(item.company || '-')}</small></td>
      <td>${esc(item.company || '-')}</td>
      <td><span>${esc(item.phone || '-')}</span><small>${esc(item.email || '-')}</small></td>
      <td>${esc(item.source || '-')}</td>
      <td>${esc(item.responsible || '-')}</td>
      <td><span class="crm-rel-status">${esc(item.stage || '-')}</span></td>
      <td class="crm-rel-actions-cell">${crmRelActions('leads',item.id)}</td>
    </tr>`).join('');
  }

  function crmRelationshipsPage(query){
    crmRelEnsureState();
    const tab = query?.get('tab') === 'leads' ? 'leads' : 'contacts';
    const isContacts = tab === 'contacts';
    const count = isContacts ? state.crmRelContacts.length : state.crmRelLeads.length;
    const filterOptions = isContacts
      ? ['Todos','Clientes','Parceiros','Fornecedores','Contratantes','Prestadores']
      : ['Todos','Novo','Em contato','Qualificado','Proposta','Convertido'];
    const filterValues = isContacts
      ? {'Todos':'all','Clientes':'cliente','Parceiros':'parceiro','Fornecedores':'fornecedor','Contratantes':'cliente','Prestadores':'prestador de serviços'}
      : {'Todos':'all','Novo':'novo','Em contato':'em contato','Qualificado':'qualificado','Proposta':'proposta','Convertido':'convertido'};
    const title = isContacts ? 'Contatos estratégicos' : 'Leads';
    const description = isContacts
      ? 'Clientes, parceiros, fornecedores, prestadores e contatos operacionais em uma lista central.'
      : 'Leads comerciais organizados em uma lista central para acompanhamento e evolução.';
    const searchPlaceholder = isContacts
      ? 'Buscar por nome, empresa, email, telefone ou cidade'
      : 'Buscar por nome, empresa, email ou telefone';
    const tableDescription = isContacts
      ? 'Acompanhe contatos, segmentos, canais e responsáveis comerciais'
      : 'Acompanhe leads, origem, etapa e responsável comercial';
    return `<div class="crm-app-shell">
      ${crmRelSidebar('relationships')}
      <main class="crm-main">
        <header class="crm-topbar">
          <div><span>CRM Integrado</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>
        </header>
        <section class="crm-workspace crm-rel-workspace" aria-label="CRM">
          <div class="crm-rel-module-header">
            <div>
              <span>CRM relacionamentos</span>
              <h2>${title}</h2>
              <p>${description}</p>
            </div>
            <button class="crm-rel-primary" type="button" data-action="crm-rel-create" data-kind="${tab}">${icon('plus',16)} ${isContacts ? 'Novo Contato' : 'Novo Lead'}</button>
          </div>

          <nav class="crm-rel-tabs" aria-label="Abas do CRM">
            <a class="${isContacts ? 'active' : ''}" href="#/crm/relationships?tab=contacts">Contatos</a>
            <a class="${!isContacts ? 'active' : ''}" href="#/crm/relationships?tab=leads">Leads</a>
          </nav>

          <div class="crm-rel-toolbar">
            <div class="crm-rel-search"><span>${icon('search',16)}</span><input id="crm-rel-search" type="search" placeholder="${searchPlaceholder}" autocomplete="off"></div>
            <select id="crm-rel-filter" aria-label="Filtro rápido">
              ${filterOptions.map((label) => `<option value="${filterValues[label]}">${label}</option>`).join('')}
            </select>
          </div>

          <section class="crm-rel-table-card">
            <div class="crm-rel-list-header">
              <div><h3>${isContacts ? 'Lista de Contatos' : 'Lista de Leads'}</h3><p>${tableDescription}</p></div>
              <div class="crm-rel-list-actions"><label><input type="checkbox" id="crm-rel-select-all" data-kind="${tab}"> <span id="crm-rel-selected-label">Selecionar todos</span></label><button type="button" id="crm-rel-bulk-delete" class="crm-rel-danger-button" data-action="crm-rel-bulk-delete" data-kind="${tab}" hidden>Excluir selecionados</button><span class="crm-rel-count"><b id="crm-rel-visible-count">${count}</b> ${isContacts ? 'contatos' : 'leads'}</span></div>
            </div>
            <div class="crm-rel-table-wrap">
              <table class="crm-rel-table">
                <thead>${isContacts ? `<tr><th></th><th>Nome</th><th>Segmento</th><th>Contato</th><th>Cidade</th><th>Responsável</th><th>Status</th><th>Ações</th></tr>` : `<tr><th></th><th>Lead</th><th>Empresa</th><th>Contato</th><th>Origem</th><th>Responsável</th><th>Etapa</th><th>Ações</th></tr>`}</thead>
                <tbody>${isContacts ? crmRelContactRows() : crmRelLeadRows()}</tbody>
              </table>
            </div>
            <div class="crm-rel-pagination"><span>Exibindo até 10 itens por página</span><div><button type="button" disabled>Anterior</button><b>1</b><button type="button" disabled>Próxima</button></div></div>
          </section>
        </section>
      </main>
    </div>`;
  }

  function crmRelSection(title,content){ return `<section class="crm-rel-form-section"><h3>${title}</h3>${content}</section>`; }
  function crmRelField(label,name,value='',type='text',extra=''){ return `<label class="crm-rel-field"><span>${label}</span><input type="${type}" name="${name}" value="${esc(value || '')}" ${extra}></label>`; }
  function crmRelSelect(label,name,value,options){ return `<label class="crm-rel-field"><span>${label}</span><select name="${name}">${options.map(([v,l]) => `<option value="${esc(v)}" ${String(value)===String(v)?'selected':''}>${esc(l)}</option>`).join('')}</select></label>`; }
  function crmRelTextArea(label,name,value='',placeholder=''){ return `<label class="crm-rel-field crm-rel-field-full"><span>${label}</span><textarea name="${name}" placeholder="${esc(placeholder)}">${esc(value || '')}</textarea></label>`; }

  function crmRelOpenModal(kind,mode,id=''){
    crmRelEnsureState();
    document.getElementById('crm-rel-modal-root')?.remove();
    const list = kind === 'contacts' ? state.crmRelContacts : state.crmRelLeads;
    const item = list.find((row) => row.id === id) || null;
    const root = document.createElement('div');
    root.id = 'crm-rel-modal-root';
    root.className = 'crm-rel-modal-root';
    root.innerHTML = mode === 'view' ? crmRelViewModal(kind,item) : crmRelFormModal(kind,mode,item);
    document.body.appendChild(root);
    if (kind === 'contacts' && mode !== 'view') crmRelToggleContactType();
  }

  function crmRelCloseModal(){ document.getElementById('crm-rel-modal-root')?.remove(); }

  function crmRelFormModal(kind,mode,item){
    const isContact = kind === 'contacts';
    const isEdit = mode === 'edit';
    const title = isContact ? (isEdit ? 'Editar Contato' : 'Novo Contato') : (isEdit ? 'Editar Lead' : 'Novo Lead');
    const subtitle = isContact ? (isEdit ? 'Edite os dados do contato' : 'Cadastre um novo contato no relacionamento operacional') : (isEdit ? 'Edite os dados do lead' : 'Cadastre um novo lead comercial');
    const contact = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',interactions:[]};
    const lead = item || {stage:'Novo',status:'Aberto',priority:'Média',source:'Site'};
    let body = '';
    if (isContact) {
      body += crmRelSection('Classificação do Contato', `<div class="crm-rel-form-grid three">${crmRelSelect('Tipo de Contato *','tipo_pessoa',contact.tipo_pessoa,[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',contact.segment,[['Cliente','Cliente'],['Parceiro','Parceiro'],['Fornecedor','Fornecedor'],['Prestador de Serviços','Prestador de Serviços'],['Investidor','Investidor'],['Órgão','Órgão']])}${crmRelField('Perfil do Contato *','perfil',contact.profile || '')}</div>`);
      body += `<div class="crm-contact-pf">${crmRelSection('Dados da Pessoa Física', `<div class="crm-rel-photo-row"><div class="crm-rel-avatar-placeholder">Foto</div><label class="crm-rel-upload-link">Selecionar foto<input type="file" name="foto" accept="image/*"></label></div><div class="crm-rel-form-grid two">${crmRelField('Nome completo *','nome_pf',contact.tipo_pessoa==='pessoa_fisica'?contact.name:'')}${crmRelField('CPF','cpf',contact.cpf || '')}${crmRelField('Email','email',contact.email || '','email')}${crmRelField('Telefone','telefone',contact.phone || '')}${crmRelField('Instagram','instagram',contact.instagram || '')}${crmRelField('Função','funcao',contact.function || '')}</div>`)}</div>`;
      body += `<div class="crm-contact-pj">${crmRelSection('Dados da Pessoa Jurídica', `<div class="crm-rel-form-grid two">${crmRelField('Razão Social *','razao_social',contact.tipo_pessoa==='pessoa_juridica'?contact.name:'')}${crmRelField('Nome Fantasia','nome_fantasia',contact.company || '')}${crmRelField('CNPJ','cnpj',contact.cnpj || '')}${crmRelField('Email','email_pj',contact.email || '','email')}${crmRelField('Instagram','instagram_pj',contact.instagram || '')}${crmRelField('Telefone','telefone_pj',contact.phone || '')}</div>`)}</div>`;
      body += crmRelSection('Endereço', `<div class="crm-rel-form-grid two">${crmRelField('Logradouro','logradouro',contact.address || '')}${crmRelField('Número','numero','')}${crmRelField('Complemento','complemento','')}${crmRelField('Bairro','bairro','')}${crmRelField('Cidade','cidade',(contact.city || '').split(' / ')[0] || '')}${crmRelSelect('Estado','estado',(contact.city || '').split(' / ')[1] || '',[['','UF'],['SP','SP'],['RJ','RJ'],['MG','MG'],['PR','PR'],['RS','RS'],['SC','SC'],['BA','BA'],['PE','PE'],['CE','CE'],['GO','GO'],['DF','DF']])}${crmRelField('CEP','cep','')}</div>`);
      body += crmRelSection('Classificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Status do Contato','status',contact.status,[['Ativo','Ativo'],['Inativo','Inativo'],['Negociando','Negociando'],['Bloqueado','Bloqueado'],['Favorito','Favorito']])}${crmRelSelect('Prioridade','prioridade',contact.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta'],['Estratégico','Estratégico']])}</div>`);
      body += `<div class="crm-contact-pj">${crmRelSection('Responsável', `<div class="crm-rel-form-grid two">${crmRelField('Nome do Responsável','responsavel_nome',contact.responsible || '')}${crmRelField('Cargo do Responsável','responsavel_cargo','')}${crmRelField('Email do Responsável','responsavel_email','','email')}${crmRelField('Telefone do Responsável','responsavel_telefone','')}</div>`)}</div>`;
      body += crmRelSection('Anexos', `<label class="crm-rel-attachment-box">Adicionar arquivos<input type="file" name="attachments" multiple></label><p class="crm-rel-muted">Nenhum anexo adicionado.</p>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',contact.notes || '','Anotações sobre o contato, contexto operacional, histórico relevante...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(contact.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-form-grid two">${crmRelField('Nome *','nome',lead.name || '')}${crmRelField('Empresa','empresa',lead.company || '')}${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions"></div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="crm-rel-modal-header"><div><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><form id="crm-rel-form" data-kind="${kind}" data-mode="${mode}" data-id="${esc(item?.id || '')}"><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Cancelar</button><button type="submit" class="crm-rel-primary">${isEdit ? 'Salvar' : (isContact ? 'Criar Contato' : 'Criar Lead')}</button></div></form></div>`;
  }

  function crmRelInteractionRow(item={}){
    return `<div class="crm-rel-interaction-row"><div class="crm-rel-form-grid three">${crmRelSelect('Tipo','interacao_tipo',item.type || 'WhatsApp',[['WhatsApp','WhatsApp'],['E-mail','E-mail'],['Ligação','Ligação'],['Reunião','Reunião'],['Nota','Nota']])}${crmRelField('Data','interacao_data','', 'date')}${crmRelField('Horário','interacao_horario','', 'time')}</div>${crmRelTextArea('Descrição','interacao_descricao',item.text || '','Descreva a interação...')}<button type="button" class="crm-rel-remove-interaction" data-action="crm-rel-remove-interaction">Remover interação</button></div>`;
  }

  function crmRelViewRow(label,value){ return `<div class="crm-rel-view-row"><span>${esc(label)}</span><strong>${esc(value || '—')}</strong></div>`; }
  function crmRelViewModal(kind,item){
    if (!item) return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div>`;
    const isContact = kind === 'contacts';
    let body = '';
    if (isContact) {
      body += crmRelSection('Classificação do Contato', `<div class="crm-rel-view-grid">${crmRelViewRow('Tipo de Contato',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}${crmRelViewRow('Perfil',item.profile)}</div>`);
      body += crmRelSection(item.tipo_pessoa==='pessoa_juridica'?'Dados da Pessoa Jurídica':'Dados da Pessoa Física', `<div class="crm-rel-view-grid">${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Razão Social':'Nome Completo',item.name)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'CNPJ':'CPF',item.tipo_pessoa==='pessoa_juridica'?item.cnpj:item.cpf)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}${crmRelViewRow('Instagram',item.instagram)}${crmRelViewRow('Função',item.function)}</div>`);
      body += crmRelSection('Endereço', `<div class="crm-rel-view-grid">${crmRelViewRow('Endereço',item.address)}${crmRelViewRow('Cidade',item.city)}</div>`);
      body += crmRelSection('Classificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Status do Contato',item.status)}${crmRelViewRow('Prioridade',item.priority)}</div>`);
      if (item.tipo_pessoa === 'pessoa_juridica') body += crmRelSection('Responsável', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome do Responsável',item.responsible)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
      body += crmRelSection('Histórico de Interações', (item.interactions || []).length ? `<div class="crm-rel-view-timeline">${item.interactions.map((it) => `<article><span>${esc(it.type)} · ${esc(it.date)}</span><p>${esc(it.text)}</p></article>`).join('')}</div>` : `<p class="crm-rel-muted">Nenhuma interação registrada.</p>`);
      body += crmRelSection('Timeline', `<div class="crm-rel-timeline-note"><input type="text" placeholder="Registrar uma nota na timeline…"><button type="button" class="crm-rel-secondary">Registrar</button></div><p class="crm-rel-muted">Nenhum evento registrado ainda.</p>`);
    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome',item.name)}${crmRelViewRow('Empresa',item.company)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Origem',item.source)}${crmRelViewRow('Etapa',item.stage)}${crmRelViewRow('Prioridade',item.priority)}${crmRelViewRow('Responsável',item.responsible)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal crm-rel-view-modal" role="dialog" aria-modal="true"><div class="crm-rel-modal-header"><div><h2>${esc(item.name)}</h2><p>${isContact ? esc(item.company || item.segment) : esc(item.company || 'Lead')}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Fechar</button><button type="button" class="crm-rel-primary" data-action="crm-rel-edit" data-kind="${kind}" data-id="${esc(item.id)}">Editar</button></div></div>`;
  }

  function crmRelToggleContactType(){
    const form = document.getElementById('crm-rel-form');
    if (!form || form.dataset.kind !== 'contacts') return;
    const type = form.querySelector('[name="tipo_pessoa"]')?.value || 'pessoa_fisica';
    form.querySelectorAll('.crm-contact-pf').forEach((el) => { el.hidden = type !== 'pessoa_fisica'; });
    form.querySelectorAll('.crm-contact-pj').forEach((el) => { el.hidden = type !== 'pessoa_juridica'; });
  }

  function crmRelApplyFilters(){
    const search = (document.getElementById('crm-rel-search')?.value || '').trim().toLowerCase();
    const filter = (document.getElementById('crm-rel-filter')?.value || 'all').toLowerCase();
    let visible = 0;
    document.querySelectorAll('[data-crm-row]').forEach((row) => {
      const matchesSearch = !search || (row.dataset.search || '').includes(search);
      const matchesFilter = filter === 'all' || (row.dataset.filter || '').includes(filter);
      row.hidden = !(matchesSearch && matchesFilter);
      if (!row.hidden) visible += 1;
    });
    const count = document.getElementById('crm-rel-visible-count');
    if (count) count.textContent = String(visible);
  }

  function crmRelUpdateSelection(){
    const boxes = [...document.querySelectorAll('[data-crm-select]')];
    const selected = boxes.filter((box) => box.checked);
    const label = document.getElementById('crm-rel-selected-label');
    const bulk = document.getElementById('crm-rel-bulk-delete');
    const all = document.getElementById('crm-rel-select-all');
    if (label) label.textContent = selected.length ? `${selected.length} selecionado(s)` : 'Selecionar todos';
    if (bulk) bulk.hidden = selected.length === 0;
    if (all) all.checked = boxes.length > 0 && selected.length === boxes.length;
  }

  function crmRelSaveForm(form){
    crmRelEnsureState();
    const data = new FormData(form);
    const kind = form.dataset.kind;
    const mode = form.dataset.mode;
    const id = form.dataset.id || (kind === 'contacts' ? `c${Date.now()}` : `l${Date.now()}`);
    if (kind === 'contacts') {
      const type = String(data.get('tipo_pessoa') || 'pessoa_fisica');
      const stateName = type === 'pessoa_juridica' ? String(data.get('razao_social') || '') : String(data.get('nome_pf') || '');
      if (!stateName.trim()) return;
      const email = type === 'pessoa_juridica' ? String(data.get('email_pj') || '') : String(data.get('email') || '');
      const phone = type === 'pessoa_juridica' ? String(data.get('telefone_pj') || '') : String(data.get('telefone') || '');
      const instagram = type === 'pessoa_juridica' ? String(data.get('instagram_pj') || '') : String(data.get('instagram') || '');
      const city = [String(data.get('cidade') || ''),String(data.get('estado') || '')].filter(Boolean).join(' / ');
      const interactions = [...form.querySelectorAll('.crm-rel-interaction-row')].map((row) => ({type:row.querySelector('[name="interacao_tipo"]')?.value || 'Nota',date:row.querySelector('[name="interacao_data"]')?.value || '',text:row.querySelector('[name="interacao_descricao"]')?.value || ''})).filter((it) => it.text);
      const item = {id,tipo_pessoa:type,name:stateName,company:type==='pessoa_juridica'?String(data.get('nome_fantasia') || ''):'',segment:String(data.get('categoria') || ''),profile:String(data.get('perfil') || ''),phone,email,city,responsible:type==='pessoa_juridica'?String(data.get('responsavel_nome') || ''):'Equipe Valtren',status:String(data.get('status') || 'Ativo'),priority:String(data.get('prioridade') || 'Média'),cpf:String(data.get('cpf') || ''),cnpj:String(data.get('cnpj') || ''),instagram,function:String(data.get('funcao') || ''),address:String(data.get('logradouro') || ''),notes:String(data.get('observacoes') || ''),interactions};
      const index = state.crmRelContacts.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelContacts[index] = {...state.crmRelContacts[index],...item}; else state.crmRelContacts.unshift(item);
    } else {
      const name = String(data.get('nome') || ''); if (!name.trim()) return;
      const item = {id,name,company:String(data.get('empresa') || ''),email:String(data.get('email') || ''),phone:String(data.get('telefone') || ''),source:String(data.get('origem') || ''),stage:String(data.get('etapa') || 'Novo'),responsible:String(data.get('responsavel') || 'Equipe Valtren'),status:'Aberto',priority:String(data.get('prioridade') || 'Média'),notes:String(data.get('observacoes') || '')};
      const index = state.crmRelLeads.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);
    }
    crmRelCloseModal();
    renderCurrentWithoutReset();
  }

  if (!window.__valtrenCrmRelationshipsBound) {
    window.__valtrenCrmRelationshipsBound = true;
    document.addEventListener('click', (event) => {
      const target = event.target.closest('[data-action]');
      if (!target) {
        document.querySelectorAll('.crm-rel-actions-menu').forEach((menu) => { menu.hidden = true; });
        return;
      }
      const action = target.dataset.action;
      if (action === 'crm-rel-row-menu') {
        event.stopPropagation();
        const menu = target.parentElement?.querySelector('.crm-rel-actions-menu');
        document.querySelectorAll('.crm-rel-actions-menu').forEach((item) => { if (item !== menu) item.hidden = true; });
        if (menu) menu.hidden = !menu.hidden;
      }
      if (action === 'crm-rel-create') crmRelOpenModal(target.dataset.kind || 'contacts','create');
      if (action === 'crm-rel-view') crmRelOpenModal(target.dataset.kind || 'contacts','view',target.dataset.id || '');
      if (action === 'crm-rel-edit') crmRelOpenModal(target.dataset.kind || 'contacts','edit',target.dataset.id || '');
      if (action === 'crm-rel-close-modal') crmRelCloseModal();
      if (action === 'crm-rel-delete') {
        crmRelEnsureState();
        const kind = target.dataset.kind || 'contacts'; const id = target.dataset.id || '';
        if (confirm('Excluir este registro?')) {
          if (kind === 'contacts') state.crmRelContacts = state.crmRelContacts.filter((row) => row.id !== id); else state.crmRelLeads = state.crmRelLeads.filter((row) => row.id !== id);
          renderCurrentWithoutReset();
        }
      }
      if (action === 'crm-rel-bulk-delete') {
        const kind = target.dataset.kind || 'contacts';
        const ids = [...document.querySelectorAll(`[data-crm-select="${kind}"]:checked`)].map((box) => box.value);
        if (ids.length && confirm(`Excluir ${ids.length} registro(s)?`)) {
          if (kind === 'contacts') state.crmRelContacts = state.crmRelContacts.filter((row) => !ids.includes(row.id)); else state.crmRelLeads = state.crmRelLeads.filter((row) => !ids.includes(row.id));
          renderCurrentWithoutReset();
        }
      }
      if (action === 'crm-rel-add-interaction') document.getElementById('crm-rel-interactions')?.insertAdjacentHTML('beforeend',crmRelInteractionRow());
      if (action === 'crm-rel-remove-interaction') target.closest('.crm-rel-interaction-row')?.remove();
    });
    document.addEventListener('input', (event) => { if (event.target?.id === 'crm-rel-search') crmRelApplyFilters(); });
    document.addEventListener('change', (event) => {
      if (event.target?.id === 'crm-rel-filter') crmRelApplyFilters();
      if (event.target?.id === 'crm-rel-select-all') {
        const checked = event.target.checked; document.querySelectorAll('[data-crm-select]').forEach((box) => { box.checked = checked; }); crmRelUpdateSelection();
      }
      if (event.target?.matches?.('[data-crm-select]')) crmRelUpdateSelection();
      if (event.target?.matches?.('[name="tipo_pessoa"]')) crmRelToggleContactType();
    });
    document.addEventListener('submit', (event) => { if (event.target?.id === 'crm-rel-form') { event.preventDefault(); crmRelSaveForm(event.target); } });
  }
'''

CSS_BLOCK = r'''
/* VALTREN CRM RELATIONSHIPS */
.crm-rel-workspace{max-width:1600px;margin:0 auto;width:100%}
.crm-rel-module-header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding-bottom:20px;border-bottom:1px solid rgba(11,29,58,.10)}
.crm-rel-module-header>div>span{display:block;color:#B8891F;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.12em}.crm-rel-module-header h2{margin:6px 0 0;font-size:25px;color:#0B1D3A}.crm-rel-module-header p{margin:7px 0 0;color:#6C7787;font:12px/1.55 Montserrat,Arial,sans-serif;max-width:760px}
.crm-rel-primary,.crm-rel-secondary,.crm-rel-danger-button{border:0;border-radius:8px;min-height:38px;padding:0 14px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font:700 12px Raleway,Arial,sans-serif;cursor:pointer}.crm-rel-primary{background:#0B1D3A;color:#fff}.crm-rel-primary:hover{background:#12294C}.crm-rel-secondary{background:#fff;border:1px solid rgba(11,29,58,.16);color:#0B1D3A}.crm-rel-danger-button{background:#FFF1F1;border:1px solid #E4B8B8;color:#9B3434;min-height:30px;padding:0 10px;font-size:10px}
.crm-rel-tabs{display:flex;gap:24px;margin:18px 0 0;border-bottom:1px solid rgba(11,29,58,.10)}.crm-rel-tabs a{position:relative;padding:11px 2px 12px;color:#687588;text-decoration:none;font-size:13px;font-weight:700}.crm-rel-tabs a.active{color:#0B1D3A}.crm-rel-tabs a.active:after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:#D4AF37}
.crm-rel-toolbar{display:flex;align-items:center;gap:10px;margin:16px 0}.crm-rel-search{height:38px;flex:1;display:flex;align-items:center;gap:8px;background:#fff;border:1px solid rgba(11,29,58,.12);border-radius:9px;padding:0 12px}.crm-rel-search span{display:flex;color:#7C8796}.crm-rel-search input{border:0!important;outline:0!important;background:transparent!important;width:100%;height:100%;padding:0!important;font:12px Montserrat,Arial,sans-serif;color:#0B1D3A}.crm-rel-toolbar select{height:38px;min-width:160px;border:1px solid rgba(11,29,58,.12);border-radius:9px;background:#fff;color:#0B1D3A;padding:0 10px;font:600 12px Raleway,Arial,sans-serif}
.crm-rel-table-card{background:#fff;border:1px solid rgba(11,29,58,.10);border-radius:12px;overflow:visible}.crm-rel-list-header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 18px;border-bottom:1px solid rgba(11,29,58,.08)}.crm-rel-list-header h3{margin:0;font-size:16px}.crm-rel-list-header p{margin:5px 0 0;color:#7B8695;font:10px/1.45 Montserrat,Arial,sans-serif}.crm-rel-list-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end}.crm-rel-list-actions label{display:flex;align-items:center;gap:7px;color:#6E7988;font-size:10px}.crm-rel-list-actions input{width:15px;height:15px;accent-color:#0B1D3A}.crm-rel-count{font-size:10px;color:#7B8695}.crm-rel-count b{color:#0B1D3A}
.crm-rel-table-wrap{overflow-x:auto;overflow-y:visible}.crm-rel-table{width:100%;border-collapse:collapse;min-width:980px}.crm-rel-table th{background:#F8FAFC;text-align:left;padding:10px 12px;color:#6E7988;font-size:9px;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid rgba(11,29,58,.08)}.crm-rel-table td{padding:12px;border-bottom:1px solid rgba(11,29,58,.07);color:#536071;font:11px/1.45 Montserrat,Arial,sans-serif;vertical-align:middle}.crm-rel-table tbody tr:hover{background:#FBFCFD}.crm-rel-table td strong{display:block;color:#0B1D3A;font:700 12px Raleway,Arial,sans-serif}.crm-rel-table td small{display:block;color:#8993A0;font-size:9px;margin-top:3px}.crm-rel-check{width:36px}.crm-rel-check input{width:15px;height:15px;accent-color:#0B1D3A}.crm-rel-status{display:inline-flex;align-items:center;border:1px solid rgba(11,29,58,.12);border-radius:999px;background:#F7F9FB;padding:4px 7px;font-size:9px;font-weight:700;color:#445164}.crm-rel-actions-cell{width:70px;text-align:right;position:relative}.crm-rel-actions{display:inline-block;position:relative}.crm-rel-more{width:32px;height:30px;border:0;background:transparent;border-radius:7px;color:#64748B;font-size:15px;cursor:pointer}.crm-rel-more:hover{background:#F0F3F6}.crm-rel-actions-menu{position:absolute;z-index:200;right:0;top:34px;min-width:130px;background:#fff;border:1px solid rgba(11,29,58,.12);box-shadow:0 8px 24px rgba(11,29,58,.12);border-radius:8px;padding:5px}.crm-rel-actions-menu button{display:block;width:100%;border:0;background:transparent;text-align:left;border-radius:6px;padding:8px 9px;color:#334155;font-size:11px;cursor:pointer}.crm-rel-actions-menu button:hover{background:#F4F6F8}.crm-rel-actions-menu button.danger{color:#A43E3E}
.crm-rel-pagination{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:12px 18px;color:#86909D;font-size:9px}.crm-rel-pagination>div{display:flex;align-items:center;gap:6px}.crm-rel-pagination button{height:28px;border:1px solid rgba(11,29,58,.10);background:#fff;border-radius:6px;color:#87919D;padding:0 9px;font-size:9px}.crm-rel-pagination b{width:28px;height:28px;display:grid;place-items:center;background:#0B1D3A;color:#fff;border-radius:6px;font-size:9px}
.crm-rel-modal-root{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:24px}.crm-rel-modal-backdrop{position:absolute;inset:0;background:rgba(7,20,40,.58);backdrop-filter:blur(2px)}.crm-rel-modal{position:relative;width:min(920px,100%);max-height:90vh;background:#fff;border-radius:14px;box-shadow:0 24px 80px rgba(0,0,0,.25);overflow:hidden;display:flex;flex-direction:column}.crm-rel-modal-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:19px 22px;border-bottom:1px solid rgba(11,29,58,.09)}.crm-rel-modal-header h2{margin:0;font-size:20px;color:#0B1D3A}.crm-rel-modal-header p{margin:5px 0 0;color:#7C8796;font:10px/1.5 Montserrat,Arial,sans-serif}.crm-rel-modal-header>button{border:0;background:#F3F5F7;color:#5B6777;width:34px;height:34px;border-radius:8px;display:grid;place-items:center;cursor:pointer}.crm-rel-modal form{display:flex;flex-direction:column;min-height:0}.crm-rel-modal-body{padding:18px 22px;overflow-y:auto;display:grid;gap:18px}.crm-rel-modal-footer{display:flex;justify-content:flex-end;gap:9px;padding:14px 22px;border-top:1px solid rgba(11,29,58,.09);background:#FBFCFD}
.crm-rel-form-section{display:grid;gap:12px}.crm-rel-form-section>h3{margin:0;padding-bottom:7px;border-bottom:1px solid rgba(11,29,58,.10);font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:.07em}.crm-rel-form-grid{display:grid;gap:12px}.crm-rel-form-grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.crm-rel-form-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.crm-rel-field{display:grid;gap:6px;min-width:0}.crm-rel-field>span{font-size:10px;font-weight:700;color:#4D5969}.crm-rel-field input,.crm-rel-field select,.crm-rel-field textarea{width:100%;box-sizing:border-box;border:1px solid rgba(11,29,58,.14);border-radius:8px;background:#fff;color:#0B1D3A;font:11px Montserrat,Arial,sans-serif;padding:0 10px;outline:none}.crm-rel-field input,.crm-rel-field select{height:38px}.crm-rel-field textarea{min-height:88px;padding-top:10px;resize:vertical}.crm-rel-field input:focus,.crm-rel-field select:focus,.crm-rel-field textarea:focus{border-color:rgba(212,175,55,.8);box-shadow:0 0 0 3px rgba(212,175,55,.10)}.crm-rel-field-full{grid-column:1/-1}.crm-rel-photo-row{display:flex;align-items:center;gap:12px}.crm-rel-avatar-placeholder{width:62px;height:62px;border-radius:999px;background:#F1F4F6;border:1px dashed rgba(11,29,58,.18);display:grid;place-items:center;color:#8A94A3;font-size:10px}.crm-rel-upload-link{position:relative;color:#9A7319;font-size:10px;font-weight:700;cursor:pointer}.crm-rel-upload-link input{position:absolute;opacity:0;pointer-events:none}.crm-rel-attachment-box{height:70px;border:1px dashed rgba(11,29,58,.18);border-radius:9px;background:#FAFBFC;display:grid;place-items:center;color:#5F6B7A;font-size:10px;font-weight:700;cursor:pointer;position:relative}.crm-rel-attachment-box input{position:absolute;opacity:0}.crm-rel-muted{margin:0;color:#8B95A1;font:italic 9px/1.5 Montserrat,Arial,sans-serif}.crm-rel-interactions{display:grid;gap:10px}.crm-rel-interaction-row{border:1px solid rgba(11,29,58,.10);border-radius:9px;background:#FAFBFC;padding:12px;display:grid;gap:10px}.crm-rel-remove-interaction{justify-self:end;border:0;background:transparent;color:#A43E3E;font-size:9px;cursor:pointer}.crm-rel-view-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px}.crm-rel-view-row{display:grid;grid-template-columns:140px minmax(0,1fr);gap:10px;padding:7px 0;border-bottom:1px solid rgba(11,29,58,.06)}.crm-rel-view-row span{color:#7C8796;font-size:9px}.crm-rel-view-row strong{color:#0B1D3A;font-size:10px;font-weight:700}.crm-rel-view-note{margin:0;background:#F8FAFC;border-radius:8px;padding:12px;color:#526070;font:10px/1.6 Montserrat,Arial,sans-serif}.crm-rel-view-timeline{display:grid;gap:8px}.crm-rel-view-timeline article{border-left:2px solid #D4AF37;padding:7px 10px;background:#FAFBFC}.crm-rel-view-timeline span{font-size:8px;color:#7B8695}.crm-rel-view-timeline p{margin:4px 0 0;color:#334155;font-size:10px}.crm-rel-timeline-note{display:flex;gap:8px}.crm-rel-timeline-note input{height:36px;flex:1;border:1px solid rgba(11,29,58,.14);border-radius:8px;padding:0 10px;font-size:10px}
@media(max-width:980px){.crm-rel-module-header{align-items:flex-start}.crm-rel-list-header{align-items:flex-start}.crm-rel-form-grid.three{grid-template-columns:1fr 1fr}.crm-rel-view-grid{grid-template-columns:1fr}}
@media(max-width:760px){.crm-rel-module-header{flex-direction:column}.crm-rel-primary{width:100%}.crm-rel-tabs{gap:18px}.crm-rel-toolbar{flex-direction:column;align-items:stretch}.crm-rel-toolbar select{width:100%}.crm-rel-list-header{flex-direction:column}.crm-rel-list-actions{justify-content:flex-start}.crm-rel-modal-root{padding:10px}.crm-rel-modal{max-height:94vh}.crm-rel-form-grid.two,.crm-rel-form-grid.three{grid-template-columns:1fr}.crm-rel-view-row{grid-template-columns:1fr;gap:3px}.crm-rel-timeline-note{flex-direction:column}}
'''


def apply_crm_relationships() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")

    dashboard_link = '<a class="active" href="#/crm/dashboard">${icon(\'layers\',18)}<span>Dashboard</span></a>'
    dashboard_with_crm = dashboard_link + '\n          <a href="#/crm/relationships">${icon(\'users\',18)}<span>CRM</span></a>'
    if 'href="#/crm/relationships"' not in app:
        if dashboard_link not in app:
            raise RuntimeError("Link do Dashboard no sidebar CRM não encontrado")
        app = app.replace(dashboard_link, dashboard_with_crm, 1)

    if 'function crmRelationshipsPage(query)' not in app:
        anchor = '  function contactPage(query)'
        if anchor not in app:
            raise RuntimeError("Âncora para o módulo CRM não encontrada")
        app = app.replace(anchor, JS_BLOCK + '\n' + anchor, 1)

    route_line = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query);"
    relationships_line = "    else if (path === '/crm/relationships') app.innerHTML = crmRelationshipsPage(query);"
    if relationships_line not in app:
        if app.count(route_line) < 2:
            raise RuntimeError("Rotas do Dashboard CRM não encontradas nas duas renderizações")
        app = app.replace(route_line, route_line + '\n' + relationships_line)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM RELATIONSHIPS \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={CSS_VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Módulo CRM Relacionamentos aplicado com abas Contatos e Leads e modais Criar/Editar/Ver.")
    return 1


if __name__ == "__main__":
    apply_crm_relationships()
