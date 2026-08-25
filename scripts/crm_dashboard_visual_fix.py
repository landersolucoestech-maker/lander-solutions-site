from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-dashboard-visual-v2"
MARKER = "/* VALTREN CRM DASHBOARD VISUAL FIX */"

PATCH = r'''
/* VALTREN CRM DASHBOARD VISUAL FIX */
.crm-app-shell{
  display:block!important;
  min-height:100vh!important;
  padding-left:250px!important;
}
.crm-sidebar{
  position:fixed!important;
  top:0!important;
  bottom:0!important;
  left:0!important;
  width:250px!important;
  height:100vh!important;
  box-sizing:border-box!important;
  overflow-y:auto!important;
  overscroll-behavior:contain;
  z-index:100!important;
}
.crm-main{
  width:100%!important;
  min-width:0!important;
  margin-left:0!important;
}

/* Portfólio de produtos: visual claro e consistente */
.crm-venture-card{
  background:#FFFFFF!important;
  border:1px solid rgba(11,29,58,.12)!important;
  border-top:3px solid #D4AF37!important;
  box-shadow:0 1px 2px rgba(11,29,58,.04)!important;
  overflow:hidden!important;
}
.crm-venture-card header{
  background:#FFFFFF!important;
  color:#0B1D3A!important;
  border:0!important;
  border-bottom:1px solid rgba(11,29,58,.09)!important;
  padding:0 0 12px!important;
  margin:0 0 12px!important;
  box-shadow:none!important;
}
.crm-venture-card header>div,
.crm-venture-card header h3,
.crm-venture-card header p,
.crm-venture-card header strong,
.crm-venture-card dl,
.crm-venture-card dl>div{
  background:transparent!important;
}
.crm-venture-card h3{
  color:#0B1D3A!important;
}
.crm-venture-card p{
  color:#6F7B8B!important;
}
.crm-venture-card header>strong{
  color:#B8891F!important;
}
.crm-venture-card dt{
  color:#778291!important;
}
.crm-venture-card dd{
  color:#0B1D3A!important;
}
.crm-status.development{
  background:#FFF7DF!important;
  color:#85620D!important;
  border:1px solid rgba(212,175,55,.36)!important;
}
.crm-status.active{
  border:1px solid rgba(38,115,77,.16)!important;
}

@media(max-width:980px) and (min-width:761px){
  .crm-app-shell{padding-left:210px!important;}
  .crm-sidebar{width:210px!important;}
}
@media(max-width:760px){
  .crm-app-shell{padding-left:0!important;}
  .crm-sidebar{
    position:static!important;
    width:auto!important;
    height:auto!important;
    overflow:visible!important;
  }
}
'''


def apply_crm_dashboard_visual_fix() -> int:
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM DASHBOARD VISUAL FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + PATCH.strip() + "\n", encoding="utf-8")

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

    print("Visual do Dashboard CRM corrigido: cards claros e sidebar fixo.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard_visual_fix()
