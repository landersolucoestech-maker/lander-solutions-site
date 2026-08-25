from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-header-modal-fix-v1"
MARKER = "/* VALTREN CRM HEADER MODAL FIX */"

OPEN_CLOSE = r'''  function crmRelOpenModal(kind,mode,id=''){
    crmRelEnsureState();
    document.getElementById('crm-rel-modal-root')?.remove();
    const list = kind === 'contacts' ? state.crmRelContacts : state.crmRelLeads;
    const item = list.find((row) => row.id === id) || null;
    const root = document.createElement('div');
    root.id = 'crm-rel-modal-root';
    root.className = 'crm-rel-modal-root';
    root.innerHTML = mode === 'view' ? crmRelViewModal(kind,item) : crmRelFormModal(kind,mode,item);
    document.body.appendChild(root);
    document.body.classList.add('crm-rel-modal-open');
    if (kind === 'contacts' && mode !== 'view') crmRelToggleContactType();
    requestAnimationFrame(() => root.querySelector('input:not([type="hidden"]), select, textarea, button')?.focus());
  }

  function crmRelCloseModal(){
    document.getElementById('crm-rel-modal-root')?.remove();
    document.body.classList.remove('crm-rel-modal-open');
  }
'''

FORM_MODAL = r'''  function crmRelFormModal(kind,mode,item){
    const isContact = kind === 'contacts';
    const isEdit = mode === 'edit';
    const title = isContact ? (isEdit ? 'Editar Contato' : 'Novo Contato') : (isEdit ? 'Editar Lead' : 'Novo Lead');
    const subtitle = isContact ? (isEdit ? 'Atualize os dados do contato' : 'Cadastre um novo contato no relacionamento operacional') : (isEdit ? 'Atualize os dados do lead' : 'Cadastre um novo lead comercial');
    const contact = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',interactions:[]};
    const lead = item || {stage:'Novo',status:'Aberto',priority:'Média',source:'Site',interactions:[]};
    let body = '';
    if (isContact) {
      body += crmRelSection('Classificação do Contato', `<div class="crm-rel-form-grid three">${crmRelSelect('Tipo de Contato *','tipo_pessoa',contact.tipo_pessoa,[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',contact.segment,[['Cliente','Cliente'],['Parceiro','Parceiro'],['Fornecedor','Fornecedor'],['Prestador de Serviços','Prestador de Serviços'],['Investidor','Investidor'],['Órgão','Órgão']])}${crmRelField('Perfil do Contato *','perfil',contact.profile || '','text','required')}</div>`);
      body += `<div class="crm-contact-pf">${crmRelSection('Dados da Pessoa Física', `<div class="crm-rel-photo-row"><div class="crm-rel-avatar-placeholder">Foto</div><label class="crm-rel-upload-link">Selecionar foto<input type="file" name="foto" accept="image/*"></label></div><div class="crm-rel-form-grid two">${crmRelField('Nome completo *','nome_pf',contact.tipo_pessoa==='pessoa_fisica'?contact.name:'','text','required')}${crmRelField('CPF','cpf',contact.cpf || '')}${crmRelField('Email','email',contact.email || '','email')}${crmRelField('Telefone','telefone',contact.phone || '')}${crmRelField('Instagram','instagram',contact.instagram || '')}${crmRelField('Função','funcao',contact.function || '')}</div>`)}</div>`;
      body += `<div class="crm-contact-pj">${crmRelSection('Dados da Pessoa Jurídica', `<div class="crm-rel-form-grid two">${crmRelField('Razão Social *','razao_social',contact.tipo_pessoa==='pessoa_juridica'?contact.name:'','text','required')}${crmRelField('Nome Fantasia','nome_fantasia',contact.company || '')}${crmRelField('CNPJ','cnpj',contact.cnpj || '')}${crmRelField('Email','email_pj',contact.email || '','email')}${crmRelField('Instagram','instagram_pj',contact.instagram || '')}${crmRelField('Telefone','telefone_pj',contact.phone || '')}</div>`)}</div>`;
      body += crmRelSection('Endereço', `<div class="crm-rel-form-grid two">${crmRelField('Logradouro','logradouro',contact.address || '')}${crmRelField('Número','numero',contact.addressNumber || '')}${crmRelField('Complemento','complemento',contact.addressComplement || '')}${crmRelField('Bairro','bairro',contact.neighborhood || '')}${crmRelField('Cidade','cidade',(contact.city || '').split(' / ')[0] || '')}${crmRelSelect('Estado','estado',(contact.city || '').split(' / ')[1] || '',[['','UF'],['SP','SP'],['RJ','RJ'],['MG','MG'],['PR','PR'],['RS','RS'],['SC','SC'],['BA','BA'],['PE','PE'],['CE','CE'],['GO','GO'],['DF','DF']])}${crmRelField('CEP','cep',contact.zipCode || '')}</div>`);
      body += crmRelSection('Classificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Status do Contato','status',contact.status,[['Ativo','Ativo'],['Inativo','Inativo'],['Negociando','Negociando'],['Bloqueado','Bloqueado'],['Favorito','Favorito']])}${crmRelSelect('Prioridade','prioridade',contact.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta'],['Estratégico','Estratégico']])}</div>`);
      body += `<div class="crm-contact-pj">${crmRelSection('Responsável', `<div class="crm-rel-form-grid two">${crmRelField('Nome do Responsável','responsavel_nome',contact.responsible || '')}${crmRelField('Cargo do Responsável','responsavel_cargo',contact.responsibleRole || '')}${crmRelField('Email do Responsável','responsavel_email',contact.responsibleEmail || '','email')}${crmRelField('Telefone do Responsável','responsavel_telefone',contact.responsiblePhone || '')}</div>`)}</div>`;
      body += crmRelSection('Anexos', `<label class="crm-rel-attachment-box">Adicionar arquivos<input type="file" name="attachments" multiple></label><p class="crm-rel-muted">Os anexos são demonstrativos neste protótipo.</p>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',contact.notes || '','Anotações sobre o contato, contexto operacional, histórico relevante...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(contact.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-form-grid two">${crmRelField('Nome *','nome',lead.name || '','text','required')}${crmRelField('Empresa','empresa',lead.company || '')}${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(lead.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title"><div class="crm-rel-modal-header"><div><h2 id="crm-rel-modal-title">${esc(title)}</h2><p>${esc(subtitle)}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><form id="crm-rel-form" data-kind="${kind}" data-mode="${mode}" data-id="${esc(item?.id || '')}"><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Cancelar</button><button type="submit" class="crm-rel-primary">${isEdit ? 'Salvar alterações' : (isContact ? 'Criar Contato' : 'Criar Lead')}</button></div></form></div>`;
  }
'''

INTERACTION_ROW = r'''  function crmRelInteractionRow(item={}){
    return `<div class="crm-rel-interaction-row"><div class="crm-rel-form-grid three">${crmRelSelect('Tipo','interacao_tipo',item.type || 'WhatsApp',[['WhatsApp','WhatsApp'],['E-mail','E-mail'],['Ligação','Ligação'],['Reunião','Reunião'],['Nota','Nota']])}${crmRelField('Data','interacao_data',item.date || '', 'date')}${crmRelField('Horário','interacao_horario',item.time || '', 'time')}</div>${crmRelTextArea('Descrição','interacao_descricao',item.text || '','Descreva a interação...')}<button type="button" class="crm-rel-remove-interaction" data-action="crm-rel-remove-interaction">Remover interação</button></div>`;
  }
'''

VIEW_MODAL = r'''  function crmRelViewModal(kind,item){
    if (!item) return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div>`;
    const isContact = kind === 'contacts';
    let body = '';
    if (isContact) {
      body += crmRelSection('Classificação do Contato', `<div class="crm-rel-view-grid">${crmRelViewRow('Tipo de Contato',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}${crmRelViewRow('Perfil',item.profile)}</div>`);
      body += crmRelSection(item.tipo_pessoa==='pessoa_juridica'?'Dados da Pessoa Jurídica':'Dados da Pessoa Física', `<div class="crm-rel-view-grid">${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Razão Social':'Nome Completo',item.name)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Nome Fantasia':'Função',item.tipo_pessoa==='pessoa_juridica'?item.company:item.function)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'CNPJ':'CPF',item.tipo_pessoa==='pessoa_juridica'?item.cnpj:item.cpf)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}${crmRelViewRow('Instagram',item.instagram)}</div>`);
      body += crmRelSection('Endereço', `<div class="crm-rel-view-grid">${crmRelViewRow('Logradouro',item.address)}${crmRelViewRow('Número',item.addressNumber)}${crmRelViewRow('Complemento',item.addressComplement)}${crmRelViewRow('Bairro',item.neighborhood)}${crmRelViewRow('Cidade / UF',item.city)}${crmRelViewRow('CEP',item.zipCode)}</div>`);
      body += crmRelSection('Classificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Status do Contato',item.status)}${crmRelViewRow('Prioridade',item.priority)}</div>`);
      if (item.tipo_pessoa === 'pessoa_juridica') body += crmRelSection('Responsável', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome do Responsável',item.responsible)}${crmRelViewRow('Cargo',item.responsibleRole)}${crmRelViewRow('Email',item.responsibleEmail)}${crmRelViewRow('Telefone',item.responsiblePhone)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome',item.name)}${crmRelViewRow('Empresa',item.company)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Origem',item.source)}${crmRelViewRow('Etapa',item.stage)}${crmRelViewRow('Prioridade',item.priority)}${crmRelViewRow('Responsável',item.responsible)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    }
    const interactions = item.interactions || [];
    body += crmRelSection('Histórico de Interações', interactions.length ? `<div class="crm-rel-view-timeline">${interactions.map((it) => `<article><span>${esc(it.type || 'Interação')}${it.date ? ` · ${esc(it.date)}` : ''}${it.time ? ` · ${esc(it.time)}` : ''}</span><p>${esc(it.text || '')}</p></article>`).join('')}</div>` : `<p class="crm-rel-muted">Nenhuma interação registrada.</p>`);
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal crm-rel-view-modal" role="dialog" aria-modal="true" aria-labelledby="crm-rel-view-title"><div class="crm-rel-modal-header"><div><h2 id="crm-rel-view-title">${esc(item.name)}</h2><p>${isContact ? esc(item.company || item.segment) : esc(item.company || 'Lead')}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Fechar</button><button type="button" class="crm-rel-primary" data-action="crm-rel-edit" data-kind="${kind}" data-id="${esc(item.id)}">Editar</button></div></div>`;
  }
'''

SAVE_FORM = r'''  function crmRelSaveForm(form){
    crmRelEnsureState();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const kind = form.dataset.kind;
    const mode = form.dataset.mode;
    const id = form.dataset.id || (kind === 'contacts' ? `c${Date.now()}` : `l${Date.now()}`);
    const interactions = [...form.querySelectorAll('.crm-rel-interaction-row')].map((row) => ({
      type: row.querySelector('[name="interacao_tipo"]')?.value || 'Nota',
      date: row.querySelector('[name="interacao_data"]')?.value || '',
      time: row.querySelector('[name="interacao_horario"]')?.value || '',
      text: row.querySelector('[name="interacao_descricao"]')?.value || ''
    })).filter((it) => it.text || it.date || it.time);
    if (kind === 'contacts') {
      const type = String(data.get('tipo_pessoa') || 'pessoa_fisica');
      const stateName = type === 'pessoa_juridica' ? String(data.get('razao_social') || '') : String(data.get('nome_pf') || '');
      if (!stateName.trim()) return;
      const email = type === 'pessoa_juridica' ? String(data.get('email_pj') || '') : String(data.get('email') || '');
      const phone = type === 'pessoa_juridica' ? String(data.get('telefone_pj') || '') : String(data.get('telefone') || '');
      const instagram = type === 'pessoa_juridica' ? String(data.get('instagram_pj') || '') : String(data.get('instagram') || '');
      const city = [String(data.get('cidade') || ''),String(data.get('estado') || '')].filter(Boolean).join(' / ');
      const item = {
        id,tipo_pessoa:type,name:stateName,
        company:type==='pessoa_juridica'?String(data.get('nome_fantasia') || ''):'',
        segment:String(data.get('categoria') || ''),profile:String(data.get('perfil') || ''),phone,email,city,
        responsible:type==='pessoa_juridica'?String(data.get('responsavel_nome') || ''):'Equipe Valtren',
        responsibleRole:type==='pessoa_juridica'?String(data.get('responsavel_cargo') || ''):'',
        responsibleEmail:type==='pessoa_juridica'?String(data.get('responsavel_email') || ''):'',
        responsiblePhone:type==='pessoa_juridica'?String(data.get('responsavel_telefone') || ''):'',
        status:String(data.get('status') || 'Ativo'),priority:String(data.get('prioridade') || 'Média'),
        cpf:String(data.get('cpf') || ''),cnpj:String(data.get('cnpj') || ''),instagram,function:String(data.get('funcao') || ''),
        address:String(data.get('logradouro') || ''),addressNumber:String(data.get('numero') || ''),addressComplement:String(data.get('complemento') || ''),neighborhood:String(data.get('bairro') || ''),zipCode:String(data.get('cep') || ''),
        notes:String(data.get('observacoes') || ''),interactions
      };
      const index = state.crmRelContacts.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelContacts[index] = {...state.crmRelContacts[index],...item}; else state.crmRelContacts.unshift(item);
    } else {
      const name = String(data.get('nome') || '');
      if (!name.trim()) return;
      const item = {id,name,company:String(data.get('empresa') || ''),email:String(data.get('email') || ''),phone:String(data.get('telefone') || ''),source:String(data.get('origem') || ''),stage:String(data.get('etapa') || 'Novo'),responsible:String(data.get('responsavel') || 'Equipe Valtren'),status:'Aberto',priority:String(data.get('prioridade') || 'Média'),notes:String(data.get('observacoes') || ''),interactions};
      const index = state.crmRelLeads.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);
    }
    crmRelCloseModal();
    renderCurrentWithoutReset();
  }
'''

KEYBOARD = r'''
  if (!window.__valtrenCrmModalKeyboardBound) {
    window.__valtrenCrmModalKeyboardBound = true;
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && document.getElementById('crm-rel-modal-root')) crmRelCloseModal();
    });
  }

'''

CSS_PATCH = r'''
/* VALTREN CRM HEADER MODAL FIX */
.crm-app-shell .crm-topbar{background:#0B1D3A!important;border-bottom:1px solid rgba(212,175,55,.28)!important;}
.crm-app-shell .crm-topbar>div>span{color:#D4AF37!important;opacity:1!important;}
.crm-app-shell .crm-topbar h1{color:#FFFFFF!important;opacity:1!important;}
.crm-app-shell .crm-topbar p{color:rgba(255,255,255,.78)!important;opacity:1!important;}
.crm-app-shell .crm-topbar .crm-demo-badge{color:#6E5312!important;}
body.crm-rel-modal-open{overflow:hidden!important;}
.crm-rel-modal-root{align-items:center!important;justify-items:center!important;overflow:auto!important;}
.crm-rel-modal{width:min(960px,calc(100vw - 48px))!important;max-height:calc(100vh - 48px)!important;background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(11,29,58,.12)!important;}
.crm-rel-modal-header{flex:0 0 auto!important;background:#FFFFFF!important;color:#0B1D3A!important;}
.crm-rel-modal-header h2{color:#0B1D3A!important;}.crm-rel-modal-header p{color:#64748B!important;}
.crm-rel-modal form{flex:1 1 auto!important;min-height:0!important;overflow:hidden!important;}
.crm-rel-modal-body{flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;overscroll-behavior:contain!important;background:#FFFFFF!important;}
.crm-rel-view-modal .crm-rel-modal-body{flex:1 1 auto!important;}
.crm-rel-modal-footer{flex:0 0 auto!important;position:relative!important;z-index:2!important;background:#FFFFFF!important;box-shadow:0 -8px 20px rgba(11,29,58,.04)!important;}
.crm-rel-form-section{background:#FFFFFF!important;}.crm-rel-form-section>h3{color:#475569!important;font-weight:800!important;}.crm-rel-field>span{color:#334155!important;}
.crm-rel-field input,.crm-rel-field select,.crm-rel-field textarea{background:#FFFFFF!important;color:#0B1D3A!important;border-color:rgba(11,29,58,.18)!important;}
.crm-rel-field input::placeholder,.crm-rel-field textarea::placeholder{color:#94A3B8!important;}
.crm-contact-pf[hidden],.crm-contact-pj[hidden]{display:none!important;}
.crm-rel-view-row strong{color:#0B1D3A!important;}.crm-rel-view-note,.crm-rel-view-timeline article{background:#F8FAFC!important;color:#334155!important;}.crm-rel-secondary{background:#FFFFFF!important;color:#0B1D3A!important;}
@media(max-width:760px){.crm-rel-modal-root{padding:0!important;align-items:stretch!important;}.crm-rel-modal{width:100%!important;max-height:100vh!important;min-height:100vh!important;border-radius:0!important;}.crm-rel-modal-header,.crm-rel-modal-footer{padding-left:16px!important;padding-right:16px!important;}.crm-rel-modal-body{padding:16px!important;}}
'''


def _replace_one(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Falha ao corrigir {label}: encontrados {count}")
    return updated


def apply_crm_header_modal_fix() -> int:
    app = APP.read_text(encoding="utf-8")
    app = _replace_one(app, r"  function crmRelOpenModal\(kind,mode,id=''\)\{.*?\n  function crmRelFormModal", OPEN_CLOSE + "\n  function crmRelFormModal", "abertura/fechamento dos modais")
    app = _replace_one(app, r"  function crmRelFormModal\(kind,mode,item\)\{.*?\n  function crmRelInteractionRow", FORM_MODAL + "\n  function crmRelInteractionRow", "formulários dos modais")
    app = _replace_one(app, r"  function crmRelInteractionRow\(item=\{\}\)\{.*?\n  \}\n\n  function crmRelViewRow", INTERACTION_ROW + "\n  function crmRelViewRow", "histórico de interações")
    app = _replace_one(app, r"  function crmRelViewModal\(kind,item\)\{.*?\n  \}\n\n  function crmRelToggleContactType", VIEW_MODAL + "\n  function crmRelToggleContactType", "modal de visualização")
    app = _replace_one(app, r"  function crmRelSaveForm\(form\)\{.*?\n  \}\n\n  if \(!window\.__valtrenCrmRelationshipsBound\)", SAVE_FORM + "\n  if (!window.__valtrenCrmRelationshipsBound)", "salvamento dos modais")
    if "__valtrenCrmModalKeyboardBound" not in app:
        anchor = "  function contactPage(query)"
        if anchor not in app:
            raise RuntimeError("Âncora para teclado dos modais não encontrada")
        app = app.replace(anchor, KEYBOARD + anchor, 1)
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM HEADER MODAL FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CSS_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Cabeçalhos e modais CRM corrigidos.")
    return 1


if __name__ == "__main__":
    apply_crm_header_modal_fix()
