from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BRAND_CSS = ASSETS / "valtren-brand.css"
LOGO = ASSETS / "valtren-logo.svg"
LOGO_VERSION = "20260824-white-wordmark-v2"
CSS_VERSION = "20260824-logo-box-removed-v2"
MARKER = "/* VALTREN LOGO SITE FIX */"

PATCH = r'''
/* VALTREN LOGO SITE FIX */
.site-header .brand{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  padding:0!important;
  box-shadow:none!important;
}
.site-header .brand img{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  padding:0!important;
  box-shadow:none!important;
  filter:none!important;
  opacity:1!important;
}
.footer-brand>img,.admin-sidebar>img{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  padding:0!important;
  box-shadow:none!important;
  filter:none!important;
  opacity:1!important;
}
.admin-login>img,.brand-panel>img{
  background:#0B1D3A!important;
  border:1px solid rgba(212,175,55,.32)!important;
  border-radius:8px!important;
  padding:8px 10px!important;
  filter:none!important;
  opacity:1!important;
}
img[src*="valtren-logo.svg"]{background:transparent!important;filter:none!important;opacity:1!important}
'''


def apply_logo_site_fix() -> int:
    changed = 0

    if LOGO.exists():
        original = LOGO.read_text(encoding="utf-8")
        updated = re.sub(
            r'(<text\s+x="185"\s+y="70"\s+fill=")#[0-9A-Fa-f]{6}("[^>]*>VALTREN</text>)',
            r'\1#FFFFFF\2',
            original,
            count=1,
        )
        if updated != original:
            LOGO.write_text(updated, encoding="utf-8")
            changed += 1

    if BRAND_CSS.exists():
        css = BRAND_CSS.read_text(encoding="utf-8")
        css = re.sub(r"\n?/\* VALTREN LOGO SITE FIX \*/.*\Z", "", css, flags=re.S)
        BRAND_CSS.write_text(css.rstrip() + "\n\n" + PATCH.strip() + "\n", encoding="utf-8")
        changed += 1

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".htm", ".js", ".mjs", ".cjs"}:
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = re.sub(
            r"valtren-logo\.svg(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-logo.svg?v={LOGO_VERSION}",
            original,
        )
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={CSS_VERSION}",
            updated,
        )

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Logo Valtren ajustada no site em {changed} arquivo(s).")
    return changed


if __name__ == "__main__":
    apply_logo_site_fix()
