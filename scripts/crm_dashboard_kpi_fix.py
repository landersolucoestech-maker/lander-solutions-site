from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-dashboard-kpis-v1"
MARKER = "/* VALTREN CRM DASHBOARD KPI FIX */"

KPI_BLOCK = r'''    const kpis = `<div class="crm-kpi-grid">
      ${money('Faturamento Bruto','R$ 275.000')}
      ${money('Custos e Impostos','R$ 147.000')}
      ${money('Resultado Distribuível','R$ 128.000')}
      ${money('Repasses Pendentes','R$ 35.000')}
    </div>`;'''

CSS_PATCH = r'''
/* VALTREN CRM DASHBOARD KPI FIX */
.crm-kpi-grid{
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
}
@media(max-width:980px){
  .crm-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;}
}
@media(max-width:440px){
  .crm-kpi-grid{grid-template-columns:1fr!important;}
}
'''


def apply_crm_dashboard_kpi_fix() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")
    pattern = r"    const kpis = `<div class=\"crm-kpi-grid\">.*?</div>`;"
    updated_app, count = re.subn(pattern, KPI_BLOCK, app, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Bloco de KPIs do Dashboard não encontrado ou ambíguo: {count}")
    APP.write_text(updated_app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM DASHBOARD KPI FIX \*/.*\Z", "", css, flags=re.S)
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

    print("KPIs do Dashboard CRM reduzidos aos quatro indicadores definidos.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard_kpi_fix()
