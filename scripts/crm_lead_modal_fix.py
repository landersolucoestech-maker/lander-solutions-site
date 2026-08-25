from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-lead-reference-fields-v3"
MARKER = "/* VALTREN CRM LEAD MODAL FIX */"

FORM_MODAL = r'''  function crmRelFormModal(kind,mode,item){
    const isContact = kind === 'contacts';
    const isEdit = mode === 'edit';
    const title = isContact ? (isEdit ? 'Editar Contato' : 'Novo Contato') : (isEdit ? 'Editar Lead' : 'Novo Lead');
    const subtitle = isContact ? (isEdit ? 'Atualize os dados do contato' : 'Cadastre um novo contato no relacionamento operacional') : (isEdit ? 'Atualize os dados do lead' : 'Cadastre um novo lead no relacionamento operacional');
    const contact = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',interactions:[]};
    const lead = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',stage:'Novo',source:'',interactions:[]};
    const record = isContact ? contact : lead;
    const classificationTitle = isContact ? 'Classificação do Contato' : 'Classificação do Lead';
    const profileLabel = isContact ? 'Perfil do Contato *' : 'Perfil do Lead *';
    const statusLabel = isContact ? 'Status do Contato' : 'Status do Lead';
    let body = '';
    body += crmRelSection(classificationTitle, `<div class="crm-rel-form-grid three">${crmRelSelect('Tipo *','tipo_pessoa',record.tipo_pessoa || 'pessoa_fisica',[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',record.segment || 'Cliente',[['Cliente','Cliente'],['Parceiro','Parceiro'],['Fornecedor','Fornecedor'],['Prestador de Serviços','Prestador de Serviços'],['Investidor','Investidor'],['Órgão','Órgão']])}${crmRelField(profileLabel,'perfil',record.profile || '','text','required')}</div>`);
    body += `<div class="crm-contact-pf">${crmRelSection('Dados da Pessoa Física', `<div class="crm-rel-photo-row"><div class="crm-rel-avatar-placeholder">Foto</div><label class="crm-rel-upload-link">Selecionar foto<input type="file" name="foto" accept="image/*"></label></div><div class="crm-rel-form-grid two">${crmRelField('Nome completo *','nome_pf',record.tipo_pessoa!=='pessoa_juridica'?record.name:'','text','required')}${crmRelField('CPF','cpf',record.cpf || '')}${crmRelField('Email','email',record.email || '','email')}${crmRelField('Telefone','telefone',record.phone || '')}${crmRelField('Instagram','instagram',record.instagram || '')}${crmRelField('Função','funcao',record.function || '')}</div>`)}</div>`;
    body += `<div class="crm-contact-pj">${crmRelSection('Dados da Pessoa Jurídica', `<div class="crm-rel-form-grid two">${crmRelField('Razão Social *','razao_social',record.tipo_pessoa==='pessoa_juridica'?record.name:'','text','required')}${crmRelField('Nome Fantasia','nome_fantasia',record.company || '')}${crmRelField('CNPJ','cnpj',record.cnpj || '')}${crmRelField('Email','email_pj',record.email || '','email')}${crmRelField('Instagram','instagram_pj',record.instagram || '')}${crmRelField('Telefone','telefone_pj',record.phone || '')}</div>`)}</div>`;
    body += crmRelSection('Endereço', `<div class="crm-rel-form-grid two">${crmRelField('Logradouro','logradouro',record.address || '')}${crmRelField('Número','numero',record.addressNumber || '')}${crmRelField('Complemento','complemento',record.addressComplement || '')}${crmRelField('Bairro','bairro',record.neighborhood || '')}${crmRelField('Cidade','cidade',(record.city || '').split(' / ')[0] || '')}${crmRelSelect('Estado','estado',(record.city || '').split(' / ')[1] || '',[['','UF'],['SP','SP'],['RJ','RJ'],['MG','MG'],['PR','PR'],['RS','RS'],['SC','SC'],['BA','BA'],['PE','PE'],['CE','CE'],['GO','GO'],['DF','DF']])}${crmRelField('CEP','cep',record.zipCode || '')}</div>`);
    body += crmRelSection('Classificação', `<div class="crm-rel-form-grid two">${crmRelSelect(statusLabel,'status',record.status || 'Ativo',[['Ativo','Ativo'],['Inativo','Inativo'],['Negociando','Negociando'],['Bloqueado','Bloqueado'],['Favorito','Favorito']])}${crmRelSelect('Prioridade','prioridade',record.priority || 'Média',[['Baixa','Baixa'],['Média','Média'],['Alta','Alta'],['Estratégico','Estratégico']])}</div>`);
    body += `<div class="crm-contact-pj">${crmRelSection('Responsável', `<div class="crm-rel-form-grid two">${crmRelField('Nome do Responsável','responsavel_nome',record.responsible || '')}${crmRelField('Cargo do Responsável','responsavel_cargo',record.responsibleRole || '')}${crmRelField('Email do Responsável','responsavel_email',record.responsibleEmail || '','email')}${crmRelField('Telefone do Responsável','responsavel_telefone',record.responsiblePhone || '')}</div>`)}</div>`;
    body += crmRelSection('Anexos', `<label class="crm-rel-attachment-box">Adicionar arquivos<input type="file" name="attachments" multiple></label><p class="crm-rel-muted">Os anexos são demonstrativos neste protótipo.</p>`);
    body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',record.notes || '',isContact ? 'Anotações sobre o contato, contexto operacional, histórico relevante...' : 'Anotações sobre o lead, contexto comercial e histórico relevante...'));
    body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(record.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal${isContact ? '' : ' crm-rel-lead-modal'}" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title"><div class="crm-rel-modal-header"><div><h2 id="crm-rel-modal-title">${esc(title)}</h2><p>${esc(subtitle)}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><form id="crm-rel-form" data-kind="${kind}" data-mode="${mode}" data-id="${esc(item?.id || '')}"><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Cancelar</button><button type="submit" class="crm-rel-primary">${isEdit ? 'Salvar alterações' : (isContact ? 'Criar Contato' : 'Criar Lead')}</button></div></form></div>`;
  }
'''

VIEW_MODAL = r'''  function crmRelViewModal(kind,item){
    if (!item) return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div>`;
    const isContact = kind === 'contacts';
    const classificationTitle = isContact ? 'Classificação do Contato' : 'Classificação do Lead';
    const statusLabel = isContact ? 'Status do Contato' : 'Status do Lead';
    let body = '';
    body += crmRelSection(classificationTitle, `<div class="crm-rel-view-grid">${crmRelViewRow('Tipo',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}${crmRelViewRow(isContact ? 'Perfil do Contato' : 'Perfil do Lead',item.profile)}</div>`);
    body += crmRelSection(item.tipo_pessoa==='pessoa_juridica'?'Dados da Pessoa Jurídica':'Dados da Pessoa Física', `<div class="crm-rel-view-grid">${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Razão Social':'Nome Completo',item.name)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Nome Fantasia':'Função',item.tipo_pessoa==='pessoa_juridica'?item.company:item.function)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'CNPJ':'CPF',item.tipo_pessoa==='pessoa_juridica'?item.cnpj:item.cpf)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}${crmRelViewRow('Instagram',item.instagram)}</div>`);
    body += crmRelSection('Endereço', `<div class="crm-rel-view-grid">${crmRelViewRow('Logradouro',item.address)}${crmRelViewRow('Número',item.addressNumber)}${crmRelViewRow('Complemento',item.addressComplement)}${crmRelViewRow('Bairro',item.neighborhood)}${crmRelViewRow('Cidade / UF',item.city)}${crmRelViewRow('CEP',item.zipCode)}</div>`);
    body += crmRelSection('Classificação', `<div class="crm-rel-view-grid">${crmRelViewRow(statusLabel,item.status)}${crmRelViewRow('Prioridade',item.priority)}</div>`);
    if (item.tipo_pessoa === 'pessoa_juridica') body += crmRelSection('Responsável', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome do Responsável',item.responsible)}${crmRelViewRow('Cargo do Responsável',item.responsibleRole)}${crmRelViewRow('Email do Responsável',item.responsibleEmail)}${crmRelViewRow('Telefone do Responsável',item.responsiblePhone)}</div>`);
    if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    const interactions = item.interactions || [];
    body += crmRelSection('Histórico de Interações', interactions.length ? `<div class="crm-rel-view-timeline">${interactions.map((it) => `<article><span>${esc(it.type || 'Interação')}${it.date ? ` · ${esc(it.date)}` : ''}${it.time ? ` · ${esc(it.time)}` : ''}</span><p>${esc(it.text || '')}</p></article>`).join('')}</div>` : `<p class="crm-rel-muted">Nenhuma interação registrada.</p>`);
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal crm-rel-view-modal" role="dialog" aria-modal="true" aria-labelledby="crm-rel-view-title"><div class="crm-rel-modal-header"><div><h2 id="crm-rel-view-title">${esc(item.name)}</h2><p>${isContact ? esc(item.company || item.segment) : esc(item.company || item.segment || 'Lead')}</p></div><button type="button" data-action="crm-rel-close-modal" aria-label="Fechar">${icon('close',18)}</button></div><div class="crm-rel-modal-body">${body}</div><div class="crm-rel-modal-footer"><button type="button" class="crm-rel-secondary" data-action="crm-rel-close-modal">Fechar</button><button type="button" class="crm-rel-primary" data-action="crm-rel-edit" data-kind="${kind}" data-id="${esc(item.id)}">Editar</button></div></div>`;
  }
'''

TOGGLE = r'''  function crmRelToggleContactType(){
    const form = document.getElementById('crm-rel-form');
    if (!form) return;
    const type = form.querySelector('[name="tipo_pessoa"]')?.value || 'pessoa_fisica';
    form.querySelectorAll('.crm-contact-pf').forEach((el) => {
      const show = type === 'pessoa_fisica';
      el.hidden = !show;
      el.querySelectorAll('input,select,textarea,button').forEach((field) => { field.disabled = !show; });
    });
    form.querySelectorAll('.crm-contact-pj').forEach((el) => {
      const show = type === 'pessoa_juridica';
      el.hidden = !show;
      el.querySelectorAll('input,select,textarea,button').forEach((field) => { field.disabled = !show; });
    });
  }
'''

LEAD_SAVE = r'''    } else {
      const type = String(data.get('tipo_pessoa') || 'pessoa_fisica');
      const stateName = type === 'pessoa_juridica' ? String(data.get('razao_social') || '') : String(data.get('nome_pf') || '');
      if (!stateName.trim()) return;
      const email = type === 'pessoa_juridica' ? String(data.get('email_pj') || '') : String(data.get('email') || '');
      const phone = type === 'pessoa_juridica' ? String(data.get('telefone_pj') || '') : String(data.get('telefone') || '');
      const instagram = type === 'pessoa_juridica' ? String(data.get('instagram_pj') || '') : String(data.get('instagram') || '');
      const city = [String(data.get('cidade') || ''),String(data.get('estado') || '')].filter(Boolean).join(' / ');
      const previous = state.crmRelLeads.find((row) => row.id === id) || {};
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
        notes:String(data.get('observacoes') || ''),interactions,
        source:previous.source || '',stage:previous.stage || 'Novo'
      };
      const index = state.crmRelLeads.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);
    }
    crmRelCloseModal();'''

CSS_PATCH = r'''
/* VALTREN CRM LEAD MODAL FIX */
.crm-rel-lead-modal{width:min(900px,calc(100vw - 48px))!important;}
@media(max-width:760px){.crm-rel-lead-modal{width:100%!important;max-width:none!important;}}
'''


def apply_crm_lead_modal_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    app, count = re.subn(
        r"  function crmRelFormModal\(kind,mode,item\)\{.*?\n  \}\n\n  function crmRelInteractionRow",
        FORM_MODAL + "\n  function crmRelInteractionRow",
        app,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("crmRelFormModal não encontrado")

    app, count = re.subn(
        r"  function crmRelViewModal\(kind,item\)\{.*?\n  \}\n\n  function crmRelToggleContactType",
        VIEW_MODAL + "\n  function crmRelToggleContactType",
        app,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("crmRelViewModal não encontrado")

    app, count = re.subn(
        r"  function crmRelToggleContactType\(\)\{.*?\n  \}\n\n  function crmRelApplyFilters",
        TOGGLE + "\n  function crmRelApplyFilters",
        app,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("crmRelToggleContactType não encontrado")

    app = app.replace(
        "    if (kind === 'contacts' && mode !== 'view') crmRelToggleContactType();",
        "    if (mode !== 'view') crmRelToggleContactType();",
        1,
    )

    pattern = re.compile(
        r"    \} else \{\n      const name = String\(data.get\('nome'\).*?\n      if \(mode === 'edit' && index >= 0\) state.crmRelLeads\[index\] = \{\.\.\.state.crmRelLeads\[index\],\.\.\.item\}; else state.crmRelLeads.unshift\(item\);\n    \}\n    crmRelCloseModal\(\);",
        re.S,
    )
    app, count = pattern.subn(LEAD_SAVE, app, count=1)
    if count != 1:
        raise RuntimeError("bloco de salvamento de Lead não encontrado")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM LEAD MODAL FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

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

    print("Modal de Lead alinhado aos campos da referência anexada.")
    return 1


if __name__ == "__main__":
    apply_crm_lead_modal_fix()
