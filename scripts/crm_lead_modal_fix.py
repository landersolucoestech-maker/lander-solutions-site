from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-lead-modal-v3"
MARKER = "/* VALTREN CRM LEAD MODAL FIX */"

OLD_LEAD_BLOCK = r'''    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-form-grid two">${crmRelField('Nome *','nome',lead.name || '','text','required')}${crmRelField('Empresa','empresa',lead.company || '')}${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(lead.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title">'''

NEW_LEAD_BLOCK = r'''    } else {
      body += crmRelSection('Tipo de Pessoa', `<div class="crm-rel-form-grid two">${crmRelSelect('Tipo de Pessoa *','tipo_pessoa',lead.tipo_pessoa || 'pessoa_fisica',[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}</div>`);
      body += `<div class="crm-lead-pf">${crmRelSection('Identificação — Pessoa Física', `<div class="crm-rel-form-grid two">${crmRelField('Nome completo *','nome_lead_pf',lead.tipo_pessoa==='pessoa_juridica'?'':(lead.name || ''),'text','required')}${crmRelField('CPF','cpf',lead.cpf || '')}${crmRelField('RG','rg',lead.rg || '')}${crmRelField('Número do Passaporte','passaporte',lead.passport || '')}</div>`)}</div>`;
      body += `<div class="crm-lead-pj">${crmRelSection('Identificação — Pessoa Jurídica', `<div class="crm-rel-form-grid two">${crmRelField('Razão Social *','razao_social_lead',lead.tipo_pessoa==='pessoa_juridica'?(lead.name || ''):'','text','required')}${crmRelField('Nome Fantasia','nome_fantasia_lead',lead.tipo_pessoa==='pessoa_juridica'?(lead.company || ''):'')}${crmRelField('CNPJ','cnpj',lead.cnpj || '')}</div>`)}</div>`;
      body += crmRelSection('Contato', `<div class="crm-rel-form-grid two">${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Interesse', `<div class="crm-rel-form-grid three">${crmRelSelect('Interesse/Serviço','interesse_servico',lead.interestService || '',[['','Selecione'],['Assessoria para visto de turismo','Assessoria para visto de turismo'],['Renovação de visto','Renovação de visto'],['Visto de estudante','Visto de estudante'],['Visto de trabalho','Visto de trabalho'],['Visto de negócios','Visto de negócios'],['Outro','Outro']])}${crmRelSelect('Tipo de visto/Interesse','tipo_visto_interesse',lead.visaInterest || '',[['','Selecione'],['B1/B2','B1/B2'],['F-1','F-1'],['J-1','J-1'],['H-1B','H-1B'],['L-1','L-1'],['O-1','O-1'],['EB','EB'],['Outro','Outro']])}${crmRelSelect('Destino de interesse','destino_interesse',lead.interestDestination || '',[['','Selecione'],['Estados Unidos','Estados Unidos'],['Canadá','Canadá'],['Outro','Outro']])}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      if (isEdit) body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(lead.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal${isContact ? '' : ' crm-rel-lead-modal'}" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title">'''

OLD_LEAD_DEFAULT = "    const lead = item || {stage:'Novo',status:'Aberto',priority:'Média',source:'Site',interactions:[]};"
NEW_LEAD_DEFAULT = "    const lead = item || {tipo_pessoa:'pessoa_fisica',stage:'Novo',status:'Aberto',priority:'Média',source:'Site',cpf:'',rg:'',passport:'',cnpj:'',interestService:'',visaInterest:'',interestDestination:'',interactions:[]};"

OLD_OPEN_TOGGLE = "    if (kind === 'contacts' && mode !== 'view') crmRelToggleContactType();"
NEW_OPEN_TOGGLE = "    if (kind === 'contacts' && mode !== 'view') crmRelToggleContactType();\n    if (kind === 'leads' && mode !== 'view') crmRelToggleLeadType(false);"

OLD_LEAD_VIEW = r'''    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome',item.name)}${crmRelViewRow('Empresa',item.company)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Origem',item.source)}${crmRelViewRow('Etapa',item.stage)}${crmRelViewRow('Prioridade',item.priority)}${crmRelViewRow('Responsável',item.responsible)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    }'''

NEW_LEAD_VIEW = r'''    } else {
      const leadType = item.tipo_pessoa || 'pessoa_fisica';
      body += crmRelSection('Tipo de Pessoa', `<div class="crm-rel-view-grid">${crmRelViewRow('Tipo de Pessoa',leadType==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}</div>`);
      if (leadType === 'pessoa_juridica') {
        body += crmRelSection('Identificação — Pessoa Jurídica', `<div class="crm-rel-view-grid">${crmRelViewRow('Razão Social',item.name)}${crmRelViewRow('Nome Fantasia',item.company)}${crmRelViewRow('CNPJ',item.cnpj)}</div>`);
      } else {
        body += crmRelSection('Identificação — Pessoa Física', `<div class="crm-rel-view-grid">${crmRelViewRow('Nome completo',item.name)}${crmRelViewRow('CPF',item.cpf)}${crmRelViewRow('RG',item.rg)}${crmRelViewRow('Número do Passaporte',item.passport)}</div>`);
      }
      body += crmRelSection('Contato', `<div class="crm-rel-view-grid">${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}</div>`);
      body += crmRelSection('Interesse', `<div class="crm-rel-view-grid">${crmRelViewRow('Interesse/Serviço',item.interestService)}${crmRelViewRow('Tipo de visto/Interesse',item.visaInterest)}${crmRelViewRow('Destino de interesse',item.interestDestination)}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-view-grid">${crmRelViewRow('Origem',item.source)}${crmRelViewRow('Etapa',item.stage)}${crmRelViewRow('Prioridade',item.priority)}${crmRelViewRow('Responsável',item.responsible)}</div>`);
      if (item.notes) body += crmRelSection('Observações', `<p class="crm-rel-view-note">${esc(item.notes)}</p>`);
    }'''

OLD_LEAD_SAVE = r'''    } else {
      const name = String(data.get('nome') || '');
      if (!name.trim()) return;
      const item = {id,name,company:String(data.get('empresa') || ''),email:String(data.get('email') || ''),phone:String(data.get('telefone') || ''),source:String(data.get('origem') || ''),stage:String(data.get('etapa') || 'Novo'),responsible:String(data.get('responsavel') || 'Equipe Valtren'),status:'Aberto',priority:String(data.get('prioridade') || 'Média'),notes:String(data.get('observacoes') || ''),interactions};
      const index = state.crmRelLeads.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);
    }'''

NEW_LEAD_SAVE = r'''    } else {
      const type = String(data.get('tipo_pessoa') || 'pessoa_fisica');
      const name = type === 'pessoa_juridica' ? String(data.get('razao_social_lead') || '') : String(data.get('nome_lead_pf') || '');
      if (!name.trim()) return;
      const item = {
        id,tipo_pessoa:type,name,
        company:type==='pessoa_juridica'?String(data.get('nome_fantasia_lead') || ''):'',
        cpf:type==='pessoa_fisica'?String(data.get('cpf') || ''):'',
        rg:type==='pessoa_fisica'?String(data.get('rg') || ''):'',
        passport:type==='pessoa_fisica'?String(data.get('passaporte') || ''):'',
        cnpj:type==='pessoa_juridica'?String(data.get('cnpj') || ''):'',
        email:String(data.get('email') || ''),phone:String(data.get('telefone') || ''),
        interestService:String(data.get('interesse_servico') || ''),
        visaInterest:String(data.get('tipo_visto_interesse') || ''),
        interestDestination:String(data.get('destino_interesse') || ''),
        source:String(data.get('origem') || ''),stage:String(data.get('etapa') || 'Novo'),
        responsible:String(data.get('responsavel') || 'Equipe Valtren'),status:'Aberto',
        priority:String(data.get('prioridade') || 'Média'),notes:String(data.get('observacoes') || ''),interactions
      };
      const index = state.crmRelLeads.findIndex((row) => row.id === id);
      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);
    }'''

OLD_TOGGLE_FUNCTION = r'''  function crmRelToggleContactType(){
    const form = document.getElementById('crm-rel-form');
    if (!form || form.dataset.kind !== 'contacts') return;
    const type = form.querySelector('[name="tipo_pessoa"]')?.value || 'pessoa_fisica';
    form.querySelectorAll('.crm-contact-pf').forEach((el) => { el.hidden = type !== 'pessoa_fisica'; });
    form.querySelectorAll('.crm-contact-pj').forEach((el) => { el.hidden = type !== 'pessoa_juridica'; });
  }
'''

NEW_TOGGLE_FUNCTION = OLD_TOGGLE_FUNCTION + r'''
  function crmRelToggleLeadType(clearInactive=false){
    const form = document.getElementById('crm-rel-form');
    if (!form || form.dataset.kind !== 'leads') return;
    const type = form.querySelector('[name="tipo_pessoa"]')?.value || 'pessoa_fisica';
    const pf = [...form.querySelectorAll('.crm-lead-pf')];
    const pj = [...form.querySelectorAll('.crm-lead-pj')];
    pf.forEach((el) => { el.hidden = type !== 'pessoa_fisica'; });
    pj.forEach((el) => { el.hidden = type !== 'pessoa_juridica'; });
    form.querySelector('[name="nome_lead_pf"]')?.toggleAttribute('required', type === 'pessoa_fisica');
    form.querySelector('[name="razao_social_lead"]')?.toggleAttribute('required', type === 'pessoa_juridica');
    if (clearInactive) {
      const inactive = type === 'pessoa_fisica' ? pj : pf;
      inactive.forEach((section) => section.querySelectorAll('input,select,textarea').forEach((field) => { if (field.type !== 'hidden') field.value = ''; }));
    }
  }
'''

OLD_CHANGE_HANDLER = "      if (event.target?.matches?.('[name=\"tipo_pessoa\"]')) crmRelToggleContactType();"
NEW_CHANGE_HANDLER = "      if (event.target?.matches?.('[name=\"tipo_pessoa\"]')) { crmRelToggleContactType(); crmRelToggleLeadType(true); }"

CSS_PATCH = r'''
/* VALTREN CRM LEAD MODAL FIX */
.crm-rel-lead-modal{
  width:min(900px,calc(100vw - 48px))!important;
}
.crm-rel-lead-modal .crm-rel-modal-header{
  padding:20px 24px!important;
}
.crm-rel-lead-modal .crm-rel-modal-body{
  padding:20px 24px!important;
  gap:16px!important;
}
.crm-rel-lead-modal .crm-rel-form-section{
  gap:10px!important;
}
.crm-rel-lead-modal .crm-rel-form-section>h3{
  padding-bottom:8px!important;
  color:#334155!important;
}
.crm-rel-lead-modal .crm-rel-modal-footer{
  padding:14px 24px!important;
}
.crm-rel-lead-modal .crm-rel-modal-footer .crm-rel-primary,
.crm-rel-lead-modal .crm-rel-modal-footer .crm-rel-secondary{
  min-width:112px;
}
.crm-rel-lead-modal .crm-lead-pf[hidden],
.crm-rel-lead-modal .crm-lead-pj[hidden]{display:none!important;}
@media(max-width:760px){
  .crm-rel-lead-modal{width:100%!important;max-width:none!important;}
  .crm-rel-lead-modal .crm-rel-modal-header,
  .crm-rel-lead-modal .crm-rel-modal-body,
  .crm-rel-lead-modal .crm-rel-modal-footer{padding-left:16px!important;padding-right:16px!important;}
}
'''


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Trecho não encontrado: {label}")
    return text.replace(old, new, 1)


def apply_crm_lead_modal_fix() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")
    app = _replace_once(app, OLD_LEAD_DEFAULT, NEW_LEAD_DEFAULT, "lead default")
    app = _replace_once(app, OLD_LEAD_BLOCK, NEW_LEAD_BLOCK, "formulário Lead")
    app = _replace_once(app, OLD_OPEN_TOGGLE, NEW_OPEN_TOGGLE, "abertura modal Lead")
    app = _replace_once(app, OLD_LEAD_VIEW, NEW_LEAD_VIEW, "visualização Lead")
    app = _replace_once(app, OLD_LEAD_SAVE, NEW_LEAD_SAVE, "salvamento Lead")
    app = _replace_once(app, OLD_TOGGLE_FUNCTION, NEW_TOGGLE_FUNCTION, "toggle PF/PJ Lead")
    app = _replace_once(app, OLD_CHANGE_HANDLER, NEW_CHANGE_HANDLER, "evento PF/PJ Lead")
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

    print("Modal Lead corrigido com PF/PJ, documentos e campos de interesse definidos.")
    return 1


if __name__ == "__main__":
    apply_crm_lead_modal_fix()
