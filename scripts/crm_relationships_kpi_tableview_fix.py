from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260824-crm-kpi-tableview-v3"
MARKER = "/* VALTREN CRM KPI TABLEVIEW */"

CSS_PATCH = r'''
/* VALTREN CRM KPI TABLEVIEW */
.crm-rel-kpi-grid{
  display:grid;
  grid-template-columns:repeat(var(--crm-rel-kpi-count,3),minmax(0,1fr));
  gap:12px;
  width:100%;
  margin:16px 0;
}
.crm-rel-kpi-card{
  min-height:96px;
  box-sizing:border-box;
  padding:16px 18px;
  border:1px solid rgba(11,29,58,.10);
  border-radius:12px;
  background:#FFFFFF;
  display:flex;
  flex-direction:column;
  align-items:flex-start;
  justify-content:center;
  text-align:left;
}
.crm-rel-kpi-card span{
  display:block;
  margin:0 0 8px;
  color:#6E7988;
  font:700 10px/1.2 Raleway,Arial,sans-serif;
  text-transform:uppercase;
  letter-spacing:.05em;
}
.crm-rel-kpi-card strong{
  display:block;
  margin:0;
  color:#0B1D3A;
  font:700 24px/1 Raleway,Arial,sans-serif;
}

.crm-rel-table th,
.crm-rel-table td{
  box-sizing:border-box!important;
  padding:13px 16px!important;
  text-align:left!important;
  vertical-align:middle!important;
}
.crm-rel-table th{line-height:1.25!important;}
.crm-rel-table td{line-height:1.45!important;}
.crm-rel-table td>strong,
.crm-rel-table td>span,
.crm-rel-table td>small{text-align:left!important;}
.crm-rel-actions-cell{text-align:left!important;}
.crm-rel-actions{vertical-align:middle!important;}
.crm-rel-check{width:44px!important;text-align:left!important;}
.crm-rel-table tbody tr{min-height:48px;}

@media(max-width:980px){
  .crm-rel-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media(max-width:600px){
  .crm-rel-kpi-grid{grid-template-columns:1fr;}
  .crm-rel-table th,.crm-rel-table td{padding:12px 14px!important;}
}
'''


def apply_crm_relationships_kpi_tableview_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    old_count = "    const count = isContacts ? state.crmRelContacts.length : state.crmRelLeads.length;"
    new_count = """    const count = isContacts ? state.crmRelContacts.length : state.crmRelLeads.length;\n    const totalContacts = state.crmRelContacts.length;\n    const totalClients = state.crmRelContacts.filter((item) => String(item.segment || '').toLowerCase() === 'cliente').length;\n    const totalLeads = state.crmRelLeads.length;\n    const totalQualified = state.crmRelLeads.filter((item) => String(item.stage || '').toLowerCase() === 'qualificado').length;\n    const totalConverted = state.crmRelLeads.filter((item) => String(item.stage || '').toLowerCase() === 'convertido').length;\n    const kpiCards = isContacts\n      ? [['Total de Contatos',totalContacts],['Clientes',totalClients]]\n      : [['Leads',totalLeads],['Qualificados',totalQualified],['Convertidos',totalConverted]];\n    const kpiMarkup = `<section class=\"crm-rel-kpi-grid\" style=\"--crm-rel-kpi-count:${kpiCards.length}\" aria-label=\"Indicadores ${isContacts ? 'de contatos' : 'de leads'}\">${kpiCards.map(([label,value]) => `<article class=\"crm-rel-kpi-card\"><span>${esc(label)}</span><strong>${value}</strong></article>`).join('')}</section>`;"""
    if old_count not in app:
        raise RuntimeError("Definição de count do CRM não encontrada")
    app = app.replace(old_count, new_count, 1)

    tabs_pattern = re.compile(
        r'(<nav class="crm-rel-tabs" aria-label="Abas do CRM">.*?</nav>)\s*(<div class="crm-rel-toolbar">)',
        re.S,
    )
    app, count = tabs_pattern.subn(r'${kpiMarkup}\n\n          \1\n\n          \2', app, count=1)
    if count != 1:
        raise RuntimeError(f"Âncora estrutural das abas do CRM não encontrada: {count}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM KPI TABLEVIEW \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", original)
        updated = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("KPIs posicionados acima das abas e TableView padronizado.")
    return 1


if __name__ == "__main__":
    apply_crm_relationships_kpi_tableview_fix()
