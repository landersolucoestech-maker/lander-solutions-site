from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-lead-modal-v2"
MARKER = "/* VALTREN CRM LEAD MODAL FIX */"

OLD_LEAD_BLOCK = r'''    } else {
      body += crmRelSection('Dados do Lead', `<div class="crm-rel-form-grid two">${crmRelField('Nome *','nome',lead.name || '','text','required')}${crmRelField('Empresa','empresa',lead.company || '')}${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(lead.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title">'''

NEW_LEAD_BLOCK = r'''    } else {
      body += crmRelSection('Identificação', `<div class="crm-rel-form-grid two">${crmRelField('Nome *','nome',lead.name || '','text','required')}${crmRelField('Empresa','empresa',lead.company || '')}</div>`);
      body += crmRelSection('Contato', `<div class="crm-rel-form-grid two">${crmRelField('Email','email',lead.email || '','email')}${crmRelField('Telefone','telefone',lead.phone || '')}</div>`);
      body += crmRelSection('Qualificação', `<div class="crm-rel-form-grid two">${crmRelSelect('Origem','origem',lead.source,[['Site','Site'],['Indicação','Indicação'],['Landing page','Landing page'],['Prospecção','Prospecção'],['Outro','Outro']])}${crmRelSelect('Etapa','etapa',lead.stage,[['Novo','Novo'],['Em contato','Em contato'],['Qualificado','Qualificado'],['Proposta','Proposta'],['Convertido','Convertido']])}${crmRelSelect('Prioridade','prioridade',lead.priority,[['Baixa','Baixa'],['Média','Média'],['Alta','Alta']])}${crmRelField('Responsável','responsavel',lead.responsible || '')}</div>`);
      body += crmRelSection('Observações', crmRelTextArea('Notas','observacoes',lead.notes || '','Contexto comercial, necessidade e próximos passos...'));
      if (isEdit) body += crmRelSection('Histórico de Interações', `<div class="crm-rel-interactions" id="crm-rel-interactions">${(lead.interactions || []).map((it) => crmRelInteractionRow(it)).join('')}</div><button type="button" class="crm-rel-secondary" data-action="crm-rel-add-interaction">${icon('plus',14)} Adicionar interação</button>`);
    }
    return `<div class="crm-rel-modal-backdrop" data-action="crm-rel-close-modal"></div><div class="crm-rel-modal${isContact ? '' : ' crm-rel-lead-modal'}" role="dialog" aria-modal="true" aria-labelledby="crm-rel-modal-title">'''

CSS_PATCH = r'''
/* VALTREN CRM LEAD MODAL FIX */
.crm-rel-lead-modal{
  width:min(820px,calc(100vw - 48px))!important;
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
@media(max-width:760px){
  .crm-rel-lead-modal{width:100%!important;max-width:none!important;}
  .crm-rel-lead-modal .crm-rel-modal-header,
  .crm-rel-lead-modal .crm-rel-modal-body,
  .crm-rel-lead-modal .crm-rel-modal-footer{padding-left:16px!important;padding-right:16px!important;}
}
'''


def apply_crm_lead_modal_fix() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")
    if OLD_LEAD_BLOCK not in app:
        raise RuntimeError("Bloco atual do modal de Lead não encontrado")
    app = app.replace(OLD_LEAD_BLOCK, NEW_LEAD_BLOCK, 1)
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

    print("Modal Novo Lead corrigido: estrutura, histórico e layout ajustados.")
    return 1


if __name__ == "__main__":
    apply_crm_lead_modal_fix()
