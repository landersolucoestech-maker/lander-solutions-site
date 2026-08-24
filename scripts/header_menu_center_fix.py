from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_CSS = ROOT / "assets" / "valtren-brand.css"
VERSION = "20260824-header-center"
MARKER = "/* VALTREN HEADER MENU CENTER */"

PATCH = r'''
/* VALTREN HEADER MENU CENTER */
@media (min-width: 901px){
  .site-header .header-inner{
    display:grid!important;
    grid-template-columns:minmax(250px,1fr) auto minmax(250px,1fr)!important;
    align-items:center!important;
    column-gap:24px!important;
  }
  .site-header .brand{
    justify-self:start!important;
  }
  .site-header .desktop-nav{
    justify-self:center!important;
    margin:0!important;
    width:max-content!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
  }
  .site-header .header-actions{
    justify-self:end!important;
    margin-left:0!important;
  }
}
'''


def center_header_menu() -> int:
    changed = 0

    if not BRAND_CSS.exists():
        raise FileNotFoundError(BRAND_CSS)

    css = BRAND_CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN HEADER MENU CENTER \*/.*\Z", "", css, flags=re.S)
    BRAND_CSS.write_text(css.rstrip() + "\n\n" + PATCH.strip() + "\n", encoding="utf-8")
    changed += 1

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Menu do cabeçalho centralizado em {changed} arquivo(s).")
    return changed


if __name__ == "__main__":
    center_header_menu()
