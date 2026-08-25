from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-header-text-visibility-v1"

CSS_PATCH = r'''
/* VALTREN CRM HEADER TEXT VISIBILITY FIX */
.crm-app-shell .crm-topbar .crm-header-create,
.crm-app-shell .crm-topbar .crm-header-create span,
.crm-app-shell .crm-topbar .crm-header-create svg{
  opacity:1!important;
  visibility:visible!important;
}

.crm-app-shell .crm-topbar .crm-header-create-contact,
.crm-app-shell .crm-topbar .crm-header-create-contact span,
.crm-app-shell .crm-topbar .crm-header-create-agenda,
.crm-app-shell .crm-topbar .crm-header-create-agenda span{
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
}

.crm-app-shell .crm-topbar .crm-header-create-lead,
.crm-app-shell .crm-topbar .crm-header-create-lead span{
  color:#FFFFFF!important;
  -webkit-text-fill-color:#FFFFFF!important;
}

.crm-app-shell .crm-topbar .crm-header-user-button,
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-user-copy strong,
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-user-copy small,
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-caret{
  opacity:1!important;
  visibility:visible!important;
}

.crm-app-shell .crm-topbar .crm-header-user-button,
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-user-copy strong{
  color:#FFFFFF!important;
  -webkit-text-fill-color:#FFFFFF!important;
}
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-user-copy small,
.crm-app-shell .crm-topbar .crm-header-user-button .crm-header-caret{
  color:rgba(255,255,255,.72)!important;
  -webkit-text-fill-color:rgba(255,255,255,.72)!important;
}

.crm-app-shell .crm-topbar .crm-header-avatar{
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
}
'''


def apply_crm_header_text_visibility_fix() -> int:
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM HEADER TEXT VISIBILITY FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Contraste dos textos dos botões do cabeçalho do CRM corrigido.")
    return 1


if __name__ == "__main__":
    apply_crm_header_text_visibility_fix()
