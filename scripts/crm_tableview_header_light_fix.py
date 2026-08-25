from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-tableview-header-light-v1"

CSS_PATCH = r'''
/* VALTREN CRM TABLEVIEW HEADER LIGHT FIX */
/*
 * Todos os cabeçalhos internos de tableviews do CRM devem permanecer claros.
 * O azul-marinho fica restrito ao chrome principal (sidebar/topbar), nunca às
 * barras acima das tabelas, onde ele estava comprometendo a legibilidade.
 */
.crm-app-shell .crm-workspace .crm-ref-table-card > header,
.crm-app-shell .crm-workspace .crm-fidelity-table > header,
.crm-app-shell .crm-workspace .crm-rel-table-card > .crm-rel-list-header,
.crm-app-shell .crm-workspace [class*="table-card"] > header,
.crm-app-shell .crm-workspace [class*="table-card"] > .crm-rel-list-header{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  border-bottom:1px solid #E2E8F0!important;
  box-shadow:none!important;
}

.crm-app-shell .crm-workspace .crm-ref-table-card > header h1,
.crm-app-shell .crm-workspace .crm-ref-table-card > header h2,
.crm-app-shell .crm-workspace .crm-ref-table-card > header h3,
.crm-app-shell .crm-workspace .crm-ref-table-card > header strong,
.crm-app-shell .crm-workspace .crm-fidelity-table > header h1,
.crm-app-shell .crm-workspace .crm-fidelity-table > header h2,
.crm-app-shell .crm-workspace .crm-fidelity-table > header h3,
.crm-app-shell .crm-workspace .crm-fidelity-table > header strong,
.crm-app-shell .crm-workspace .crm-rel-list-header h1,
.crm-app-shell .crm-workspace .crm-rel-list-header h2,
.crm-app-shell .crm-workspace .crm-rel-list-header h3,
.crm-app-shell .crm-workspace .crm-rel-list-header strong{
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  opacity:1!important;
  visibility:visible!important;
}

.crm-app-shell .crm-workspace .crm-ref-table-card > header p,
.crm-app-shell .crm-workspace .crm-ref-table-card > header small,
.crm-app-shell .crm-workspace .crm-ref-table-card > header > span,
.crm-app-shell .crm-workspace .crm-fidelity-table > header p,
.crm-app-shell .crm-workspace .crm-fidelity-table > header small,
.crm-app-shell .crm-workspace .crm-fidelity-table > header > span,
.crm-app-shell .crm-workspace .crm-rel-list-header p,
.crm-app-shell .crm-workspace .crm-rel-list-header small,
.crm-app-shell .crm-workspace .crm-rel-list-header span{
  color:#64748B!important;
  -webkit-text-fill-color:#64748B!important;
  opacity:1!important;
  visibility:visible!important;
}

.crm-app-shell .crm-workspace .crm-ref-table-card > header svg,
.crm-app-shell .crm-workspace .crm-fidelity-table > header svg,
.crm-app-shell .crm-workspace .crm-rel-list-header svg{
  color:#64748B!important;
  stroke:currentColor!important;
  opacity:1!important;
}

html[data-theme="dark"] .crm-app-shell .crm-workspace .crm-ref-table-card > header,
html[data-theme="dark"] .crm-app-shell .crm-workspace .crm-fidelity-table > header,
html[data-theme="dark"] .crm-app-shell .crm-workspace .crm-rel-table-card > .crm-rel-list-header,
html[data-theme="dark"] .crm-app-shell .crm-workspace [class*="table-card"] > header,
html[data-theme="dark"] .crm-app-shell .crm-workspace [class*="table-card"] > .crm-rel-list-header{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  color-scheme:light!important;
}
'''


def apply_crm_tableview_header_light_fix() -> int:
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM TABLEVIEW HEADER LIGHT FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Cabeçalhos dos tableviews do CRM padronizados em superfície clara e texto legível em todos os módulos.")
    return 1


if __name__ == "__main__":
    apply_crm_tableview_header_light_fix()
