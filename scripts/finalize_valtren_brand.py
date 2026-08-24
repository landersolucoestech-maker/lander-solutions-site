from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BRAND_CSS = ASSETS / "valtren-brand.css"
TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".md", ".txt", ".xml", ".webmanifest", ".bat", ".yml", ".yaml"}
SKIP_DIRS = {".git", ".bootstrap", "node_modules", "scripts"}
LEGACY_ASSETS = ("logo-horizontal-light.webp", "logo-horizontal.webp", "logo-mark.webp")

REPLACEMENTS = (
    ("LANDER_DEFAULT_CONTENT", "VALTREN_DEFAULT_CONTENT"),
    ("lander-solutions-conteudo", "valtren-solutions-conteudo"),
    ("lander-solutions:", "valtren-solutions:"),
    ("lander-admin", "valtren-admin"),
    (">LS<", ">VS<"),
    ("const logo = state.theme === 'dark' ? 'assets/valtren-logo-light.svg' : 'assets/valtren-logo.svg';", "const logo = 'assets/valtren-logo-light.svg';"),
    ("const color = state.theme === 'dark' ? '#0E151B' : '#0B6A4F';", "const color = '#0B1D3A';"),
    ("--green-dark", "--valtren-accent-dark"),
    ("--green-soft", "--valtren-accent-soft"),
    ("--green", "--valtren-accent"),
    ("#0B6A4F", "#D4AF37"), ("#0b6a4f", "#D4AF37"),
    ("#07513D", "#B8891F"), ("#07513d", "#B8891F"),
    ("#E7F3EF", "#F8F2DF"), ("#e7f3ef", "#F8F2DF"),
    ("#138565", "#F0D477"),
    ("#27A37F", "#D4AF37"), ("#27a37f", "#D4AF37"),
    ("#1D8B6C", "#B8891F"), ("#1d8b6c", "#B8891F"),
    ("#12382F", "#132B50"), ("#12382f", "#132B50"),
    ("#102a24", "#0B1D3A"),
    ("#0A2420", "#071327"), ("#0a2420", "#071327"),
    ("#10241F", "#0B1D3A"), ("#10241f", "#0B1D3A"),
    ("#59c5a2", "#F0D477"), ("#6ee7b7", "#F0D477"),
    ("#77d7b8", "#E6C85B"), ("#a7f3d0", "#F0D477"),
    ("#d1fae5", "#F7E7AF"), ("#c6d8d1", "#CBD5E1"),
    ("#b9cbc5", "#B8C4D4"), ("#dbe7e3", "#D8DEE8"),
    ("#e8f3ef", "#EEF2F7"), ("#b8cdc6", "#D9C46C"),
    ("#dbe4e1", "#E5E7EB"), ("#dce4e1", "#DCE2EA"),
    ("#eff4f2", "#F3F5F8"), ("#f7faf9", "#F8FAFC"),
    ("#eef5f2", "#F1F5F9"), ("#152128", "#132B50"),
    ("#17212b", "#0B1D3A"), ("#C3D1CC", "#CBD5E1"),
    ("#c3d1cc", "#CBD5E1"), ("#30423F", "#334155"),
    ("#30423f", "#334155"), ("#101D1A", "#132B50"),
    ("#101d1a", "#132B50"), ("#263B37", "#26364D"),
    ("#263b37", "#26364D"),
    ("rgba(11,106,79", "rgba(212,175,55"),
    ("rgba(11, 106, 79", "rgba(212, 175, 55"),
    ("rgba(39,163,127", "rgba(212,175,55"),
    ("rgba(39, 163, 127", "rgba(212, 175, 55"),
    ("rgba(110,231,183", "rgba(240,212,119"),
    ("rgba(110, 231, 183", "rgba(240, 212, 119"),
    ("family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700", "family=Montserrat:wght@400;500;600&family=Raleway:wght@600;700"),
    ("'Inter'", "'Montserrat'"), ("Inter,", "Montserrat,"), ("Poppins", "Raleway"),
)

PATCH = r'''
/* VALTREN FINAL IDENTITY */
.site-header{background:rgba(11,29,58,.98)!important;border-color:rgba(212,175,55,.42)!important;color:#fff!important}
.site-header .desktop-nav>a,.site-header .nav-dropdown>button,.site-header .menu-button,.site-header a{color:rgba(255,255,255,.9)!important}
.site-header .desktop-nav>a:hover,.site-header .desktop-nav>a.active,.site-header .nav-dropdown>button:hover,.site-header a:hover{color:#D4AF37!important}
.site-header .mega-menu{background:#fff!important;border-color:rgba(212,175,55,.42)!important}.site-header .mega-menu strong{color:#0B1D3A!important}.site-header .mega-menu a{color:#475569!important}.site-header .mega-menu a:hover,.site-header .mega-menu .mega-all{color:#B8891F!important}
.hero,[class~="hero"],[class^="hero-"],[class*=" hero-"]{background:linear-gradient(135deg,#0B1D3A 0%,#071327 72%,#0B1D3A 100%)!important;color:#fff!important}.hero h1,.hero h2,.hero h3,.hero p{color:inherit!important}.hero .eyebrow,.hero strong,.hero-trust svg{color:#D4AF37!important}.hero-trust{color:rgba(255,255,255,.76)!important}
.button,.btn-primary,.button-primary,button[type="submit"],input[type="submit"]{background:linear-gradient(135deg,#F0D477,#D4AF37)!important;color:#0B1D3A!important;border-color:#D4AF37!important}.button:hover,.btn-primary:hover,.button-primary:hover,button[type="submit"]:hover,input[type="submit"]:hover{background:linear-gradient(135deg,#D4AF37,#B8891F)!important;color:#0B1D3A!important;border-color:#B8891F!important}.button-secondary,.btn-secondary{background:transparent!important;border-color:#D4AF37!important;color:#0B1D3A!important}.hero .button-secondary{color:#fff!important}.button-light{background:#fff!important;color:#0B1D3A!important;border-color:#fff!important}
.technology-feature,.product-hero,.section-dark,.product-grid-light .product-card,.product-card,.cta-section{background:#0B1D3A!important;color:#fff!important}.technology-feature p,.product-hero p,.section-dark p,.product-card p,.cta-inner p{color:rgba(255,255,255,.76)!important}.check-list svg,.structure-grid svg,.product-card a,.cta-inner .eyebrow{color:#F0D477!important}.architecture-visual{background:radial-gradient(circle,rgba(212,175,55,.26),transparent 55%)!important}.visual-grid aside{background:#0B1D3A!important}.visual-grid aside .active{background:#D4AF37!important;color:#0B1D3A!important}.visual-heading>span{background:#0B1D3A!important;color:#F0D477!important}.chart-bars span{background:linear-gradient(180deg,#F0D477,#D4AF37)!important}.product-monogram,.product-identity>div{background:#D4AF37!important;color:#0B1D3A!important}.status-badge{background:rgba(212,175,55,.14)!important;color:#F0D477!important;border-color:rgba(212,175,55,.34)!important}
.eyebrow,.text-link,.service-card a,.collection-card a,.area-card strong,.mission-grid article>span,.differential-grid span,.market-cards svg,.values-grid svg,.feature-list svg,.principles-row svg,.collection-placeholder,.collection-card span,.empty-state svg,.empty-state h1,.contact-details svg{color:#B8891F!important}.principle>span,.service-icon{background:#F8F2DF!important;color:#B8891F!important}
.admin-sidebar,.site-footer,footer{background:#0B1D3A!important;color:#fff!important;border-color:rgba(212,175,55,.42)!important}.admin-sidebar nav button,.admin-preview,.site-footer a,footer a{color:rgba(255,255,255,.84)!important}.admin-sidebar nav button:hover,.admin-sidebar nav button.active,.admin-preview:hover,.site-footer a:hover,footer a:hover{color:#D4AF37!important}
html[data-theme="dark"] .site-header{background:rgba(7,19,39,.98)!important}html[data-theme="dark"] .mega-menu{background:#132B50!important}html[data-theme="dark"] .mega-menu strong{color:#fff!important}html[data-theme="dark"] .mega-menu a{color:#CBD5E1!important}
'''


def finalize_branding() -> int:
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = original
        for old, new in REPLACEMENTS:
            updated = updated.replace(old, new)
        updated = re.sub(r"(?<![\w-])LANDER(?![\w-])", "VALTREN", updated)
        updated = re.sub(r"(?<![\w-])Lander(?![\w-])", "Valtren", updated)
        updated = re.sub(r"(?<![\w-])lander(?![\w-])", "valtren", updated)
        if path.suffix.lower() in {".html", ".htm"}:
            updated = re.sub(r"valtren-brand\.css\?v=[^\"']+", "valtren-brand.css?v=20260824-3", updated)
            updated = re.sub(r"valtren-mark\.svg(?:\?v=[^\"']+)?", "valtren-mark.svg?v=20260824-3", updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    if BRAND_CSS.exists():
        css = BRAND_CSS.read_text(encoding="utf-8")
        css = re.sub(r"\n?/\* VALTREN FINAL IDENTITY \*/.*\Z", "", css, flags=re.S)
        BRAND_CSS.write_text(css.rstrip() + "\n" + PATCH.strip() + "\n", encoding="utf-8")

    removed = 0
    for name in LEGACY_ASSETS:
        path = ASSETS / name
        if path.exists():
            path.unlink()
            removed += 1

    print(f"Finalização Valtren: {changed} arquivo(s) revisado(s), {removed} asset(s) legado(s) removido(s).")
    return changed


if __name__ == "__main__":
    finalize_branding()
