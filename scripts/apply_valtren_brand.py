from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BRAND_CSS = ASSETS / "valtren-brand.css"

TEXT_SUFFIXES = {
    ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".md",
    ".txt", ".xml", ".webmanifest", ".bat", ".yml", ".yaml",
}
SKIP_DIRS = {".git", ".bootstrap", "node_modules"}

DISPLAY_REPLACEMENTS = (
    ("LANDER SOLUTIONS", "VALTREN SOLUTIONS"),
    ("Lander Solutions", "Valtren Solutions"),
    ("lander solutions", "valtren solutions"),
)

ASSET_REPLACEMENTS = (
    ("assets/logo-horizontal-light.webp", "assets/valtren-logo-light.svg"),
    ("assets/logo-horizontal.webp", "assets/valtren-logo.svg"),
    ("assets/logo-mark.webp", "assets/valtren-mark.svg"),
    ("logo-horizontal-light.webp", "valtren-logo-light.svg"),
    ("logo-horizontal.webp", "valtren-logo.svg"),
    ("logo-mark.webp", "valtren-mark.svg"),
)

CSS = r'''@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Raleway:wght@600;700&display=swap');

:root {
  --valtren-navy: #0B1D3A;
  --valtren-gold: #D4AF37;
  --valtren-gold-light: #F0D477;
  --valtren-gold-dark: #B8891F;
  --valtren-white: #FFFFFF;
  --valtren-charcoal: #1E1E1E;
  --valtren-slate: #475569;
  --valtren-navy-soft: #132B50;
  --valtren-border: rgba(11, 29, 58, .14);
  --valtren-gold-border: rgba(212, 175, 55, .42);
  --valtren-shadow: 0 18px 50px rgba(11, 29, 58, .12);

  --primary: var(--valtren-navy);
  --primary-color: var(--valtren-navy);
  --color-primary: var(--valtren-navy);
  --brand-primary: var(--valtren-navy);
  --secondary: var(--valtren-gold);
  --secondary-color: var(--valtren-gold);
  --color-secondary: var(--valtren-gold);
  --accent: var(--valtren-gold);
  --accent-color: var(--valtren-gold);
  --color-accent: var(--valtren-gold);
  --background: var(--valtren-white);
  --background-color: var(--valtren-white);
  --surface: var(--valtren-white);
  --foreground: var(--valtren-navy);
  --text-color: var(--valtren-navy);
  --muted-color: var(--valtren-slate);
  --border-color: var(--valtren-border);
  --focus-color: var(--valtren-gold);
}

html { scroll-behavior: smooth; }
body {
  font-family: 'Montserrat', Arial, sans-serif !important;
  color: var(--valtren-navy);
  background: var(--valtren-white);
}
h1, h2, h3, h4, h5, h6,
.display, .title, [class*="heading"] {
  font-family: 'Raleway', Arial, sans-serif !important;
  font-weight: 700;
  letter-spacing: .012em;
}
::selection { background: var(--valtren-gold); color: var(--valtren-navy); }
:focus-visible { outline: 2px solid var(--valtren-gold) !important; outline-offset: 3px; }

a { color: var(--valtren-navy); text-decoration-color: rgba(212,175,55,.65); }
a:hover { color: var(--valtren-gold-dark); }

header, .site-header, .app-header, .main-header, .navbar, .topbar,
[class~="site-nav"], [class~="main-nav"] {
  background: var(--valtren-navy) !important;
  color: var(--valtren-white) !important;
  border-color: var(--valtren-gold-border) !important;
}
header a, .site-header a, .app-header a, .main-header a, .navbar a, .topbar a {
  color: var(--valtren-white) !important;
}
header a:hover, .site-header a:hover, .app-header a:hover, .main-header a:hover,
.navbar a:hover, .topbar a:hover,
header a[aria-current="page"], .navbar a[aria-current="page"] {
  color: var(--valtren-gold) !important;
}
header img[src*="valtren-logo"], .site-header img[src*="valtren-logo"],
.navbar img[src*="valtren-logo"] {
  width: auto !important;
  max-width: min(330px, 58vw) !important;
  max-height: 58px !important;
  object-fit: contain;
}

.hero, [class~="hero"], [class^="hero-"], [class*=" hero-"] {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  background: linear-gradient(135deg, #0B1D3A 0%, #071327 72%, #0B1D3A 100%) !important;
  color: var(--valtren-white) !important;
}
.hero::before, [class~="hero"]::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  opacity: .42;
  background-image:
    linear-gradient(135deg, transparent 49.65%, rgba(212,175,55,.24) 49.8%, rgba(212,175,55,.24) 50.2%, transparent 50.35%),
    linear-gradient(45deg, transparent 49.75%, rgba(212,175,55,.10) 49.9%, rgba(212,175,55,.10) 50.1%, transparent 50.25%);
  background-size: 430px 430px, 610px 610px;
  background-position: right -110px top -80px, right -190px bottom -220px;
}
.hero h1, .hero h2, .hero h3, .hero p,
[class~="hero"] h1, [class~="hero"] h2, [class~="hero"] p {
  color: inherit !important;
}
.hero strong, .hero em, .hero .eyebrow, .hero [class*="accent"] { color: var(--valtren-gold) !important; }

.btn-primary, .button-primary, [data-variant="primary"],
button[type="submit"], input[type="submit"] {
  background: linear-gradient(135deg, var(--valtren-gold-light), var(--valtren-gold)) !important;
  color: var(--valtren-navy) !important;
  border: 1px solid var(--valtren-gold) !important;
  font-family: 'Montserrat', Arial, sans-serif !important;
  font-weight: 600 !important;
  box-shadow: 0 8px 24px rgba(212,175,55,.18);
  transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
}
.btn-primary:hover, .button-primary:hover, [data-variant="primary"]:hover,
button[type="submit"]:hover, input[type="submit"]:hover {
  filter: brightness(.96);
  transform: translateY(-1px);
  box-shadow: 0 12px 30px rgba(212,175,55,.25);
}
.btn-secondary, .button-secondary, [data-variant="secondary"] {
  background: transparent !important;
  color: var(--valtren-navy) !important;
  border-color: var(--valtren-gold) !important;
}
.hero .btn-secondary, .hero .button-secondary, .hero [data-variant="secondary"] {
  color: var(--valtren-white) !important;
}

.card, [class$="-card"], [class*=" card"], .panel, [class$="-panel"] {
  border-color: var(--valtren-border) !important;
  box-shadow: var(--valtren-shadow);
}
.card:hover, [class$="-card"]:hover { border-color: var(--valtren-gold-border) !important; }
input, textarea, select {
  font-family: 'Montserrat', Arial, sans-serif !important;
  border-color: rgba(71,85,105,.28) !important;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--valtren-gold) !important;
  box-shadow: 0 0 0 3px rgba(212,175,55,.14) !important;
}
table thead, table th { font-family: 'Raleway', Arial, sans-serif !important; color: var(--valtren-navy); }
.badge, [class*="badge"], .tag, [class*="tag"] { border-color: var(--valtren-gold-border); }

.sidebar, .admin-sidebar, [class~="sidebar"] {
  border-color: var(--valtren-gold-border) !important;
}
.admin-sidebar, .dashboard .sidebar, body[class*="admin"] .sidebar {
  background: var(--valtren-navy) !important;
  color: var(--valtren-white) !important;
}
.admin-sidebar a, .dashboard .sidebar a, body[class*="admin"] .sidebar a { color: rgba(255,255,255,.86) !important; }
.admin-sidebar a:hover, .admin-sidebar a[aria-current="page"],
.dashboard .sidebar a:hover, .dashboard .sidebar a[aria-current="page"] {
  color: var(--valtren-gold) !important;
  background: rgba(212,175,55,.10) !important;
}

footer, .site-footer, .main-footer {
  background: var(--valtren-navy) !important;
  color: rgba(255,255,255,.84) !important;
  border-color: var(--valtren-gold-border) !important;
}
footer a, .site-footer a, .main-footer a { color: var(--valtren-white) !important; }
footer a:hover, .site-footer a:hover, .main-footer a:hover { color: var(--valtren-gold) !important; }

[data-theme="dark"], html.dark, body.dark, .dark-theme {
  --background: var(--valtren-navy);
  --background-color: var(--valtren-navy);
  --surface: var(--valtren-charcoal);
  --foreground: var(--valtren-white);
  --text-color: var(--valtren-white);
  --muted-color: #A7B1C2;
  --border-color: rgba(212,175,55,.22);
  color: var(--valtren-white);
  background: var(--valtren-navy);
}
[data-theme="dark"] .card, html.dark .card, body.dark .card,
[data-theme="dark"] .panel, html.dark .panel, body.dark .panel {
  background: var(--valtren-charcoal) !important;
  color: var(--valtren-white) !important;
  border-color: rgba(212,175,55,.20) !important;
}
[data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3,
html.dark h1, html.dark h2, html.dark h3, body.dark h1, body.dark h2, body.dark h3 {
  color: var(--valtren-white);
}

@media (max-width: 768px) {
  header img[src*="valtren-logo"], .site-header img[src*="valtren-logo"], .navbar img[src*="valtren-logo"] {
    max-width: 245px !important;
    max-height: 48px !important;
  }
  .hero::before, [class~="hero"]::before { opacity: .25; background-size: 300px 300px, 430px 430px; }
}
'''


def _brand_text(text: str) -> str:
    for old, new in DISPLAY_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in ASSET_REPLACEMENTS:
        text = text.replace(old, new)
    text = re.sub(r"(?<![\w-])LANDER(?![\w-])", "VALTREN", text)
    text = re.sub(r"(?<![\w-])Lander(?![\w-])", "Valtren", text)
    return text


def _patch_html(path: Path, text: str) -> str:
    rel_assets = os.path.relpath(ASSETS, path.parent).replace(os.sep, "/")
    css_href = f"{rel_assets}/valtren-brand.css?v=20260824"
    favicon_href = f"{rel_assets}/valtren-mark.svg"

    if "data-valtren-brand=\"stylesheet\"" not in text:
        link = f'<link rel="stylesheet" href="{css_href}" data-valtren-brand="stylesheet">'
        text = re.sub(r"</head\s*>", f"  {link}\n</head>", text, count=1, flags=re.I)
    if "data-valtren-brand=\"favicon\"" not in text:
        icon = f'<link rel="icon" type="image/svg+xml" href="{favicon_href}" data-valtren-brand="favicon">'
        text = re.sub(r"</head\s*>", f"  {icon}\n</head>", text, count=1, flags=re.I)

    text = re.sub(
        r'<meta\s+[^>]*name=["\']theme-color["\'][^>]*>',
        '<meta name="theme-color" content="#0B1D3A">',
        text,
        flags=re.I,
    )
    if 'name="theme-color"' not in text.lower() and "name='theme-color'" not in text.lower():
        text = re.sub(
            r"</head\s*>",
            '  <meta name="theme-color" content="#0B1D3A">\n</head>',
            text,
            count=1,
            flags=re.I,
        )
    return text


def apply_branding() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    BRAND_CSS.write_text(CSS, encoding="utf-8")

    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.resolve() == Path(__file__).resolve() or path.resolve() == BRAND_CSS.resolve():
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = _brand_text(original)
        if path.suffix.lower() in {".html", ".htm"}:
            updated = _patch_html(path, updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Identidade visual Valtren aplicada em {changed} arquivo(s).")
    return changed


if __name__ == "__main__":
    apply_branding()
