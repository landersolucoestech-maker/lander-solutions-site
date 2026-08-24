from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BRAND_CSS = ASSETS / "valtren-brand.css"
TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".txt", ".xml", ".webmanifest"}
SKIP_DIRS = {".git", ".bootstrap", "node_modules", "scripts"}

REPLACEMENTS = (
    ("assets/valtren-logo-light.svg", "assets/valtren-logo.svg"),
    ("valtren-logo-light.svg", "valtren-logo.svg"),
    ("<span aria-hidden=\"true\">${state.theme === 'dark' ? '☀' : '☾'}</span>", "<span class=\"theme-toggle-track\" aria-hidden=\"true\"><span class=\"theme-toggle-thumb\"></span></span>"),
    ("font-family: Inter", "font-family: 'Montserrat'"),
    ("font-family: Poppins", "font-family: 'Raleway'"),
    ("#0B6A4F", "#D4AF37"), ("#0b6a4f", "#D4AF37"),
    ("#07513D", "#B8891F"), ("#07513d", "#B8891F"),
    ("#E7F3EF", "#FFFFFF"), ("#e7f3ef", "#FFFFFF"),
    ("#138565", "#D4AF37"),
    ("#27A37F", "#D4AF37"), ("#27a37f", "#D4AF37"),
    ("#1D8B6C", "#B8891F"), ("#1d8b6c", "#B8891F"),
    ("#12382F", "#0B1D3A"), ("#12382f", "#0B1D3A"),
    ("#102a24", "#0B1D3A"), ("#0A2420", "#071327"), ("#0a2420", "#071327"),
    ("#10241F", "#0B1D3A"), ("#10241f", "#0B1D3A"),
    ("#59c5a2", "#D4AF37"), ("#6ee7b7", "#D4AF37"),
    ("#77d7b8", "#D4AF37"), ("#a7f3d0", "#D4AF37"),
    ("rgba(11,106,79", "rgba(212,175,55"), ("rgba(11, 106, 79", "rgba(212, 175, 55"),
    ("rgba(39,163,127", "rgba(212,175,55"), ("rgba(39, 163, 127", "rgba(212, 175, 55"),
)

PATCH = r'''
/* VALTREN IDENTITY LOCK */
:root{--valtren-navy:#0B1D3A;--valtren-gold:#D4AF37;--valtren-white:#FFFFFF;--valtren-charcoal:#1E1E1E;--valtren-slate:#475569;--valtren-accent:#D4AF37;--valtren-accent-dark:#B8891F;--valtren-accent-soft:rgba(212,175,55,.10);--ink:#0B1D3A;--slate:#475569;--line:rgba(11,29,58,.15);--muted:#FFFFFF;--white:#FFFFFF;--radius:12px;--shadow:0 18px 48px rgba(11,29,58,.10)}
body{font-family:'Montserrat',Arial,sans-serif!important;color:#0B1D3A!important;background:#FFFFFF!important}h1,h2,h3,h4,h5,h6,.visual-heading strong{font-family:'Raleway',Arial,sans-serif!important}p{color:#475569}.section-muted{background:linear-gradient(180deg,#FFFFFF 0%,rgba(11,29,58,.035) 100%)!important}
.site-header{background:rgba(11,29,58,.985)!important;border-bottom:1px solid rgba(212,175,55,.38)!important;box-shadow:0 8px 30px rgba(11,29,58,.12)!important}.header-inner{min-height:82px;height:auto!important}.brand{display:inline-flex!important;align-items:center!important;background:#FFFFFF!important;border:1px solid rgba(212,175,55,.38)!important;border-radius:10px!important;padding:7px 11px!important}.brand img{width:232px!important;height:48px!important;object-fit:contain!important;object-position:left center!important;filter:none!important}.desktop-nav>a,.nav-dropdown>button,.menu-button{color:#FFFFFF!important}.desktop-nav>a:hover,.desktop-nav>a.active,.nav-dropdown>button:hover{color:#D4AF37!important}.mega-menu{background:#FFFFFF!important;border-color:rgba(11,29,58,.16)!important}.mega-menu strong{color:#0B1D3A!important}.mega-menu a{color:#475569!important}.mega-menu a:hover,.mega-menu .mega-all{color:#B8891F!important}.mobile-nav{background:#0B1D3A!important}.mobile-nav a{color:#FFFFFF!important;border-color:rgba(255,255,255,.12)!important}.mobile-nav a.active{color:#D4AF37!important}
.preference-controls{gap:9px!important}.language-switcher{height:36px!important;padding:3px!important;border:1px solid rgba(212,175,55,.35)!important;border-radius:999px!important;background:rgba(255,255,255,.07)!important}.language-switcher button{height:28px!important;min-width:31px!important;border-radius:999px!important;color:rgba(255,255,255,.78)!important}.language-switcher button:hover{color:#D4AF37!important}.language-switcher button.active{background:#D4AF37!important;color:#0B1D3A!important;box-shadow:none!important}.theme-toggle{position:relative!important;width:54px!important;height:32px!important;padding:3px!important;border:1px solid rgba(212,175,55,.55)!important;border-radius:999px!important;background:#FFFFFF!important;display:block!important;overflow:hidden!important}.theme-toggle:hover{border-color:#D4AF37!important;box-shadow:0 0 0 3px rgba(212,175,55,.12)!important}.theme-toggle-track{position:relative!important;display:block!important;width:100%!important;height:100%!important;border-radius:999px!important;background:#0B1D3A!important}.theme-toggle-thumb{position:absolute!important;top:3px!important;left:3px!important;width:20px!important;height:20px!important;border-radius:50%!important;background:#D4AF37!important;box-shadow:0 2px 8px rgba(0,0,0,.18)!important;transform:translateX(0)!important;transition:transform .2s ease!important}html[data-theme="dark"] .theme-toggle-thumb{transform:translateX(22px)!important}.site-footer .language-switcher{background:rgba(255,255,255,.07)!important;border-color:rgba(212,175,55,.35)!important}.site-footer .language-switcher button{color:rgba(255,255,255,.78)!important}.site-footer .language-switcher button.active{background:#D4AF37!important;color:#0B1D3A!important}.site-footer .theme-toggle{background:#FFFFFF!important;border-color:rgba(212,175,55,.55)!important}
.footer-brand>img,.admin-sidebar>img,.admin-login>img,.brand-panel>img{background:#FFFFFF!important;border:1px solid rgba(212,175,55,.34)!important;border-radius:10px!important;padding:9px 11px!important;filter:none!important;opacity:1!important}.footer-brand>img{width:245px!important;max-width:100%!important}.admin-sidebar>img{width:205px!important;height:auto!important}.admin-login>img{width:270px!important;max-width:100%!important}.brand-panel>img{max-width:440px!important}img[src*="valtren-logo.svg"]{filter:none!important}
.hero,.page-hero,.product-hero,.technology-feature,.section-dark,.cta-section{background:linear-gradient(135deg,#0B1D3A 0%,#071327 72%,#0B1D3A 100%)!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.22)!important}.hero h1,.hero h2,.hero h3,.hero p,.page-hero h1,.page-hero p,.product-hero h1,.product-hero p,.technology-feature h2,.technology-feature p,.section-dark h2,.section-dark p,.cta-section h2,.cta-section p{color:#FFFFFF!important}.eyebrow,.text-link,.service-card a,.product-card a,.collection-card a,.check-list svg,.structure-grid svg,.values-grid svg,.market-cards svg,.principles-row svg,.contact-details svg{color:#D4AF37!important}.hero-visual{border:1px solid rgba(212,175,55,.30)!important;background:#FFFFFF!important}.visual-grid aside{background:#0B1D3A!important;color:#FFFFFF!important}.visual-grid aside .active{background:#D4AF37!important;color:#0B1D3A!important}.visual-heading>span{background:#0B1D3A!important;color:#D4AF37!important}.chart-bars span{background:#D4AF37!important}
.button,.btn-primary,.button-primary,button[type="submit"],input[type="submit"]{background:#D4AF37!important;color:#0B1D3A!important;border:1px solid #D4AF37!important;border-radius:8px!important;font-weight:700!important;box-shadow:none!important}.button:hover,.btn-primary:hover,.button-primary:hover,button[type="submit"]:hover,input[type="submit"]:hover{background:#B8891F!important;color:#FFFFFF!important;border-color:#B8891F!important}.button-secondary,.btn-secondary{background:transparent!important;color:#0B1D3A!important;border-color:#D4AF37!important}.hero .button-secondary,.product-hero .button-secondary,.section-dark .button-secondary{color:#FFFFFF!important}.button-light{background:#FFFFFF!important;color:#0B1D3A!important;border-color:#FFFFFF!important}
.principle,.area-card,.service-card,.market-cards article,.mission-grid article,.values-grid>div,.principles-row>div,.collection-card,.contact-form,.contact-card,.brand-panel,.admin-login,.admin-panel,.admin-nested,.admin-note,.backup-card,.metric-row div,.chart-panel{background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(11,29,58,.14)!important;border-radius:12px!important;box-shadow:none!important}.service-card:hover,.collection-card:hover,.area-card:hover{border-color:rgba(212,175,55,.58)!important;box-shadow:0 16px 36px rgba(11,29,58,.08)!important}.principle>span,.service-icon,.product-monogram,.product-identity>div{background:rgba(212,175,55,.12)!important;color:#B8891F!important}.tag-cloud span{background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(11,29,58,.14)!important}input,textarea,select,.contact-form input,.contact-form textarea,.admin-panel input,.admin-panel textarea,.admin-panel select,.admin-login input{background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(71,85,105,.32)!important;border-radius:8px!important}input:focus,textarea:focus,select:focus{border-color:#D4AF37!important;box-shadow:0 0 0 3px rgba(212,175,55,.13)!important}
.site-footer,footer,.admin-sidebar{background:#0B1D3A!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.30)!important}.site-footer h3{font-family:'Montserrat',Arial,sans-serif!important;color:#FFFFFF!important}.site-footer p,.site-footer small,.site-footer a,.admin-sidebar>span,.admin-sidebar nav button,.admin-preview{color:rgba(255,255,255,.78)!important}.site-footer a:hover,.admin-sidebar nav button:hover,.admin-sidebar nav button.active,.admin-preview:hover{color:#D4AF37!important}.admin-sidebar nav button.active{background:rgba(212,175,55,.12)!important}.admin-shell,.admin-login-page,.admin-main{background:#FFFFFF!important}.admin-warning{background:rgba(212,175,55,.10)!important;border-color:rgba(212,175,55,.45)!important;color:#0B1D3A!important}
html[data-theme="dark"]{color-scheme:dark;--ink:#FFFFFF;--slate:#FFFFFF;--line:rgba(212,175,55,.20);--muted:#1E1E1E;--white:#1E1E1E}html[data-theme="dark"] body{background:#1E1E1E!important;color:#FFFFFF!important}html[data-theme="dark"] p{color:rgba(255,255,255,.76)!important}html[data-theme="dark"] .section-muted{background:#1E1E1E!important}html[data-theme="dark"] .site-header{background:rgba(11,29,58,.985)!important}html[data-theme="dark"] .mega-menu{background:#1E1E1E!important;border-color:rgba(212,175,55,.25)!important}html[data-theme="dark"] .mega-menu strong{color:#FFFFFF!important}html[data-theme="dark"] .mega-menu a{color:rgba(255,255,255,.78)!important}html[data-theme="dark"] .principle,html[data-theme="dark"] .area-card,html[data-theme="dark"] .service-card,html[data-theme="dark"] .market-cards article,html[data-theme="dark"] .mission-grid article,html[data-theme="dark"] .values-grid>div,html[data-theme="dark"] .principles-row>div,html[data-theme="dark"] .collection-card,html[data-theme="dark"] .contact-form,html[data-theme="dark"] .contact-card,html[data-theme="dark"] .brand-panel,html[data-theme="dark"] .admin-login,html[data-theme="dark"] .admin-panel,html[data-theme="dark"] .admin-nested,html[data-theme="dark"] .admin-note,html[data-theme="dark"] .backup-card,html[data-theme="dark"] .metric-row div,html[data-theme="dark"] .chart-panel{background:#1E1E1E!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.20)!important}html[data-theme="dark"] input,html[data-theme="dark"] textarea,html[data-theme="dark"] select{background:#1E1E1E!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.28)!important}html[data-theme="dark"] .tag-cloud span{background:#1E1E1E!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.20)!important}html[data-theme="dark"] .button-secondary{color:#FFFFFF!important}html[data-theme="dark"] .admin-shell,html[data-theme="dark"] .admin-login-page,html[data-theme="dark"] .admin-main{background:#1E1E1E!important}
@media(max-width:900px){.brand img{width:205px!important}.mobile-nav .preference-controls{padding-top:16px!important}}
'''


def lock_identity() -> int:
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
        if path.name == "app.js":
            updated = re.sub(r"\$\{state\.theme\s*===\s*'dark'\s*\?\s*'assets/valtren-logo\.svg'\s*:\s*'assets/valtren-logo\.svg'\}", "assets/valtren-logo.svg", updated)
        if path.suffix.lower() in {".html", ".htm"}:
            updated = re.sub(r"valtren-brand\.css\?v=[^\"']+", "valtren-brand.css?v=20260824-identity-lock", updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    if BRAND_CSS.exists():
        css = BRAND_CSS.read_text(encoding="utf-8")
        css = re.sub(r"\n?/\* VALTREN IDENTITY LOCK \*/.*\Z", "", css, flags=re.S)
        BRAND_CSS.write_text(css.rstrip() + "\n\n" + PATCH.strip() + "\n", encoding="utf-8")
    for name in ("logo-horizontal-light.webp", "logo-horizontal.webp", "logo-mark.webp", "valtren-logo-light.svg"):
        target = ASSETS / name
        if target.exists():
            target.unlink()
    print(f"Valtren identity lock aplicado em {changed} arquivo(s).")
    return changed


if __name__ == "__main__":
    lock_identity()
