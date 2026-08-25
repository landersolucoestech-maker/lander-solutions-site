from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS_VERSION = "20260824-crm-lead-origin-v1"


def apply_crm_lead_origin_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    app = app.replace(
        "    const lead = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',stage:'Novo',source:'',interactions:[]};",
        "    const lead = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',status:'Ativo',priority:'Média',stage:'Novo',source:'Website',interactions:[]};",
        1,
    )

    app = app.replace(
        "    const profileLabel = isContact ? 'Perfil do Contato *' : 'Perfil do Lead *';\n",
        "    const leadOriginOptions = [['Website','Website'],['WhatsApp','WhatsApp'],['Email','Email'],['Google','Google'],['Instagram','Instagram'],['TikTok','TikTok'],['Indicação','Indicação'],['Telefone','Telefone']];\n",
        1,
    )

    old_form = "${crmRelField(profileLabel,'perfil',record.profile || '','text','required')}"
    new_form = "${isContact ? crmRelField('Perfil do Contato *','perfil',record.profile || '','text','required') : crmRelSelect('Origem do Lead *','origem',record.source || 'Website',leadOriginOptions)}"
    if old_form not in app:
        raise RuntimeError("Campo Perfil do Lead não encontrado no formulário")
    app = app.replace(old_form, new_form, 1)

    old_view = "${crmRelViewRow(isContact ? 'Perfil do Contato' : 'Perfil do Lead',item.profile)}"
    new_view = "${isContact ? crmRelViewRow('Perfil do Contato',item.profile) : crmRelViewRow('Origem do Lead',item.source)}"
    if old_view not in app:
        raise RuntimeError("Perfil do Lead não encontrado na visualização")
    app = app.replace(old_view, new_view, 1)

    old_save = "segment:String(data.get('categoria') || ''),profile:String(data.get('perfil') || ''),phone,email,city,"
    new_save = "segment:String(data.get('categoria') || ''),source:String(data.get('origem') || 'Website'),phone,email,city,"
    if old_save not in app:
        raise RuntimeError("Perfil do Lead não encontrado no salvamento")
    app = app.replace(old_save, new_save, 1)

    app = app.replace(
        "        source:previous.source || '',stage:previous.stage || 'Novo'",
        "        stage:previous.stage || 'Novo'",
        1,
    )

    APP.write_text(app, encoding="utf-8")

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

    print("Perfil do Lead removido e Origem do Lead adicionada.")
    return 1


if __name__ == "__main__":
    apply_crm_lead_origin_fix()
