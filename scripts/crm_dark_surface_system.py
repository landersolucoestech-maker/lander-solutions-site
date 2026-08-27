from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "valtren-brand.css"
MARKER = "/* VALTREN CRM DARK-SHELL LIGHT-WORKSPACE */"
PRODUCT_REVIEW_MARKER = "/* VALTREN PRODUCT SYSTEM REVIEW */"

SEMANTIC_CSS = r'''
/* VALTREN CRM DARK-SHELL LIGHT-WORKSPACE */
:root{
  --crm-surface-app:#F4F6F8;
  --crm-surface-page:#F4F6F8;
  --crm-surface-card:#FFFFFF;
  --crm-surface-subtle:#F8FAFC;
  --crm-surface-muted:#EEF2F6;
  --crm-surface-modal:#FFFFFF;
  --crm-surface-dark:#0B1D3A;
}
.crm-app-shell{
  --crm-bg:var(--crm-surface-app);
  --crm-surface:var(--crm-surface-card);
  --crm-surface-soft:var(--crm-surface-subtle);
}

/* A moldura global é a única surface navy estrutural do Sistema Interno. */
.crm-app-shell .crm-topbar,
.crm-app-shell .crm-sidebar,
.crm-app-shell .crm-sidebar-head{
  background:var(--crm-surface-dark)!important;
  background-color:var(--crm-surface-dark)!important;
  color:#FFFFFF!important;
}
.crm-app-shell .crm-main,
.crm-app-shell .crm-workspace,
.crm-app-shell .crm-ref-workspace,
.crm-app-shell .crm-agenda-workspace{
  background:var(--crm-surface-page)!important;
  background-color:var(--crm-surface-page)!important;
  color:#0B1D3A!important;
  color-scheme:light!important;
}

/* Corrige a regra histórica global de <header>: headers internos nunca herdam o shell navy. */
.crm-app-shell .crm-main header:not(.crm-topbar),
.crm-app-shell .crm-workspace header,
.crm-app-shell .crm-ref-workspace header,
.crm-app-shell .crm-agenda-workspace header{
  background:var(--crm-surface-card)!important;
  background-color:var(--crm-surface-card)!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
}
.crm-app-shell .crm-main header:not(.crm-topbar) h1,
.crm-app-shell .crm-main header:not(.crm-topbar) h2,
.crm-app-shell .crm-main header:not(.crm-topbar) h3,
.crm-app-shell .crm-main header:not(.crm-topbar) h4{
  color:#0B1D3A!important;
}
.crm-app-shell .crm-main header:not(.crm-topbar) p,
.crm-app-shell .crm-main header:not(.crm-topbar) small,
.crm-app-shell .crm-main header:not(.crm-topbar) span:not(.crm-ref-badge):not([class*="status"]){
  color:#5F6F82!important;
}

/* Cards, painéis, KPIs e containers analíticos permanecem claros. */
.crm-app-shell .crm-workspace .crm-dashboard-panel,
.crm-app-shell .crm-workspace .crm-dashboard-kpi,
.crm-app-shell .crm-workspace .crm-panel,
.crm-app-shell .crm-workspace .crm-kpi,
.crm-app-shell .crm-workspace .crm-ref-panel,
.crm-app-shell .crm-workspace .crm-ref-table-card,
.crm-app-shell .crm-workspace .crm-ref-kpi,
.crm-app-shell .crm-workspace .crm-rel-list-panel,
.crm-app-shell .crm-workspace .crm-rel-kpi,
.crm-app-shell .crm-workspace .crm-legal-table-card,
.crm-app-shell .crm-workspace [class$="-panel"]:not([class*="event"]),
.crm-app-shell .crm-workspace [class$="-card"]:not([class*="event"]):not([class*="status"]):not([class*="badge"]),
.crm-app-shell .crm-ref-workspace [class$="-panel"]:not([class*="event"]),
.crm-app-shell .crm-ref-workspace [class$="-card"]:not([class*="event"]):not([class*="status"]):not([class*="badge"]),
.crm-app-shell .crm-agenda-workspace [class$="-panel"]:not([class*="event"]),
.crm-app-shell .crm-agenda-workspace [class$="-card"]:not([class*="event"]):not([class*="status"]):not([class*="badge"]){
  background:var(--crm-surface-card)!important;
  background-color:var(--crm-surface-card)!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
}

/* Tabelas: surface secundária clara no cabeçalho e hover neutro. */
.crm-app-shell .crm-main table,
.crm-app-shell .crm-main thead,
.crm-app-shell .crm-main tbody,
.crm-app-shell .crm-main tr,
.crm-app-shell .crm-main td{
  background-color:transparent!important;
  color:#0B1D3A!important;
}
.crm-app-shell .crm-main th,
.crm-app-shell .crm-main thead th{
  background:var(--crm-surface-subtle)!important;
  background-color:var(--crm-surface-subtle)!important;
  color:#5F6F82!important;
  border-color:#E2E8F0!important;
}
.crm-app-shell .crm-main tbody tr:hover td{
  background:var(--crm-surface-subtle)!important;
  background-color:var(--crm-surface-subtle)!important;
}

/* Tabs e toggles internos usam tint/ênfase, nunca uma faixa navy. */
.crm-app-shell .crm-workspace [class$="-tabs"] button.active,
.crm-app-shell .crm-workspace [class$="-tabs"] a.active,
.crm-app-shell .crm-ref-workspace [class$="-tabs"] button.active,
.crm-app-shell .crm-ref-workspace [class$="-tabs"] a.active,
.crm-app-shell .crm-agenda-workspace [class$="-tabs"] button.active,
.crm-app-shell .crm-agenda-workspace [class$="-tabs"] a.active,
.crm-app-shell .crm-agenda-view-toggle button.active,
.crm-app-shell .crm-acct-entry-head button.active,
.crm-app-shell .crm-alloc-steps button.active,
.crm-app-shell .crm-ref-subtabs a.active,
.crm-app-shell .crm-ref-pnl-tabs button.active,
.crm-app-shell .crm-ref-ai-tabs button.active{
  background:#FFF7D6!important;
  background-color:#FFF7D6!important;
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  border-color:#D4AF37!important;
  box-shadow:inset 0 -2px 0 #D4AF37!important;
}

/* Ações primárias do conteúdo usam o accent canônico, não navy preenchido. */
.crm-app-shell .crm-workspace button.primary,
.crm-app-shell .crm-workspace a.primary,
.crm-app-shell .crm-workspace .crm-rel-primary,
.crm-app-shell .crm-workspace .crm-ref-primary-wide,
.crm-app-shell .crm-workspace .crm-fin-row-actions>button.primary,
.crm-app-shell .crm-workspace .crm-alloc-editor-footer button.primary,
.crm-app-shell .crm-workspace .crm-alloc-step-head button.primary,
.crm-app-shell .crm-workspace .crm-part-workflow .primary,
.crm-app-shell .crm-workspace .crm-payout-actions>button.primary{
  background:#D4AF37!important;
  background-color:#D4AF37!important;
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  border-color:#D4AF37!important;
}

/* Bulk bars, rankings, empty states e informações auxiliares são superfícies claras. */
.crm-app-shell .crm-workspace .crm-fin-bulk,
.crm-app-shell .crm-workspace .crm-full-toast,
.crm-app-shell .crm-workspace [class*="ranking"],
.crm-app-shell .crm-workspace [class*="empty"],
.crm-app-shell .crm-workspace [class*="summary"],
.crm-app-shell .crm-workspace [class*="breakdown"],
.crm-app-shell .crm-workspace [class*="cost-grid"] article{
  background:var(--crm-surface-subtle)!important;
  background-color:var(--crm-surface-subtle)!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
}

/* Controles e menus dentro do workspace ficam claros. */
.crm-app-shell .crm-main input:not([type="checkbox"]):not([type="radio"]):not([type="range"]),
.crm-app-shell .crm-main select,
.crm-app-shell .crm-main textarea,
.crm-app-shell .crm-main [class*="popover"],
.crm-app-shell .crm-main [class*="dropdown"]:not(.crm-nav-dropdown),
.crm-app-shell .crm-main [class$="-more"]>div,
.crm-app-shell .crm-main [class$="-menu"]:not(.crm-nav):not(.crm-sidebar){
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
  color-scheme:light!important;
}

/* Pequenos indicadores podem usar accent, mas não navy estrutural. */
.crm-app-shell .crm-agenda-day.today>header span,
.crm-app-shell .crm-agenda-week-col.today>header strong,
.crm-app-shell .crm-rel-pagination b,
.crm-app-shell .crm-ref-stepper button.active b,
.crm-app-shell .crm-ref-profile-head>div:first-child,
.crm-app-shell .crm-ref-logo-upload img{
  background:#FFF7D6!important;
  background-color:#FFF7D6!important;
  color:#0B1D3A!important;
  border-color:#D4AF37!important;
}

/* Modais e drawers de conteúdo: header, body e footer claros; overlay permanece legítimo. */
.crm-rel-modal,.crm-agenda-modal,.crm-ref-modal,.crm-fin-modal,.crm-alloc-modal,.crm-legal-modal,
.crm-part-modal,.crm-payout-modal,.crm-business-modal,.crm-legal-matter-modal,.crm-compliance-modal,
.crm-ip-modal,.crm-corporate-modal,
.crm-legal-drawer,.crm-part-drawer,.crm-payout-drawer,.crm-business-drawer,.crm-legal-matter-drawer,
.crm-compliance-drawer,.crm-ip-drawer,.crm-corporate-drawer{
  background:var(--crm-surface-modal)!important;
  background-color:var(--crm-surface-modal)!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
  color-scheme:light!important;
}
.crm-rel-modal header,.crm-rel-modal footer,.crm-agenda-modal header,.crm-agenda-modal footer,
.crm-ref-modal header,.crm-ref-modal footer,.crm-fin-modal header,.crm-fin-modal footer,
.crm-alloc-modal header,.crm-alloc-modal footer,.crm-legal-modal header,.crm-legal-modal footer,
.crm-part-modal header,.crm-part-modal footer,.crm-payout-modal header,.crm-payout-modal footer,
.crm-business-modal header,.crm-business-modal footer,.crm-legal-matter-modal header,.crm-legal-matter-modal footer,
.crm-compliance-modal header,.crm-compliance-modal footer,.crm-ip-modal header,.crm-ip-modal footer,
.crm-corporate-modal header,.crm-corporate-modal footer{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
}
.crm-rel-modal .primary,.crm-agenda-modal .primary,.crm-ref-modal .primary,.crm-fin-modal .primary,
.crm-alloc-modal .primary,.crm-legal-modal .primary,.crm-part-modal .primary,.crm-payout-modal .primary,
.crm-business-modal .primary,.crm-legal-matter-modal .primary,.crm-compliance-modal .primary,
.crm-ip-modal .primary,.crm-corporate-modal .primary{
  background:#D4AF37!important;
  background-color:#D4AF37!important;
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  border-color:#D4AF37!important;
}

/* Dashboard: proteção explícita para os blocos executivos requisitados. */
.crm-app-shell .crm-dashboard-panel,
.crm-app-shell .crm-dashboard-panel>header,
.crm-app-shell .crm-dashboard-panel-body,
.crm-app-shell .crm-dashboard-group-card,
.crm-app-shell .crm-dashboard-cost-grid article,
.crm-app-shell .crm-dashboard-ranking a{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  border-color:#D9E1E9!important;
}
.crm-app-shell .crm-dashboard-inline-empty,
.crm-app-shell .crm-dashboard-empty-state,
.crm-app-shell .crm-dashboard-allocation-ready,
.crm-app-shell .crm-dashboard-mini-kpis article{
  background:var(--crm-surface-subtle)!important;
  background-color:var(--crm-surface-subtle)!important;
  color:#0B1D3A!important;
}
'''

_SCOPING_REPLACEMENTS = (
    (
        'header, .site-header, .app-header, .main-header, .navbar, .topbar,\n[class~="site-nav"], [class~="main-nav"] {',
        '.site-header, .app-header, .main-header, .navbar, .topbar,\n[class~="site-nav"], [class~="main-nav"] {'
    ),
    ('header a, .site-header a, .app-header a, .main-header a, .navbar a, .topbar a {', '.site-header a, .app-header a, .main-header a, .navbar a, .topbar a {'),
    ('header a:hover, .site-header a:hover, .app-header a:hover, .main-header a:hover,', '.site-header a:hover, .app-header a:hover, .main-header a:hover,'),
    ('header a[aria-current="page"], .navbar a[aria-current="page"] {', '.site-header a[aria-current="page"], .navbar a[aria-current="page"] {'),
    ('header img[src*="valtren-logo"], .site-header img[src*="valtren-logo"],', '.site-header img[src*="valtren-logo"],'),
    ('footer, .site-footer, .main-footer {', '.site-footer, .main-footer {'),
    ('footer a, .site-footer a, .main-footer a {', '.site-footer a, .main-footer a {'),
    ('footer a:hover, .site-footer a:hover, .main-footer a:hover {', '.site-footer a:hover, .main-footer a:hover {'),
    ('.admin-sidebar,.site-footer,footer{', '.admin-sidebar,.site-footer{'),
    ('.admin-sidebar nav button,.admin-preview,.site-footer a,footer a{', '.admin-sidebar nav button,.admin-preview,.site-footer a{'),
    ('.admin-sidebar nav button:hover,.admin-sidebar nav button.active,.admin-preview:hover,.site-footer a:hover,footer a:hover{', '.admin-sidebar nav button:hover,.admin-sidebar nav button.active,.admin-preview:hover,.site-footer a:hover{'),
)


def _scope_legacy_global_selectors(css: str) -> str:
    for old, new in _SCOPING_REPLACEMENTS:
        css = css.replace(old, new)
    return css


def _insert_before_product_review(css: str) -> str:
    css = re.sub(
        r"\n?/\* VALTREN CRM DARK-SHELL LIGHT-WORKSPACE \*/.*?(?=\n/\* VALTREN PRODUCT SYSTEM REVIEW \*/)",
        "",
        css,
        flags=re.S,
    )
    at = css.find(PRODUCT_REVIEW_MARKER)
    if at < 0:
        raise RuntimeError("Product System Review marker ausente; surface owner deve rodar depois da revisão global")
    prefix = css[:at].rstrip()
    suffix = css[at:]
    return prefix + "\n\n" + SEMANTIC_CSS.strip() + "\n\n" + suffix


def _dark_background(value: str) -> bool:
    v = re.sub(r"\s+", "", value.lower())
    dark_tokens = (
        "#0b1d3a", "#071327", "#12294c", "#132b50", "#1e1e1e",
        "var(--valtren-navy)", "var(--valtren-charcoal)", "var(--crm-text)", "var(--crm-surface-dark)",
    )
    return any(token in v for token in dark_tokens)


def _rules(css: str):
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector = " ".join(match.group(1).split())
        body = match.group(2)
        backgrounds = []
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            key, value = decl.split(":", 1)
            if key.strip().lower() in {"background", "background-color"} and _dark_background(value):
                backgrounds.append(value.strip())
        if backgrounds:
            yield match.start(), selector, backgrounds


def assert_dark_surface_ownership(css: str | None = None) -> dict[str, int]:
    source = CSS.read_text(encoding="utf-8") if css is None else css
    marker_at = source.find(MARKER)
    product_at = source.find(PRODUCT_REVIEW_MARKER)
    if marker_at < 0 or product_at < 0 or marker_at >= product_at:
        raise RuntimeError("Dark-shell/light-workspace marker deve preceder a revisão global final")

    required_tokens = (
        "--crm-surface-app", "--crm-surface-page", "--crm-surface-card", "--crm-surface-subtle",
        "--crm-surface-modal", "--crm-surface-dark",
    )
    missing = [token for token in required_tokens if token not in source[marker_at:product_at]]
    if missing:
        raise RuntimeError(f"Tokens semânticos de surface ausentes: {missing}")

    pre_surface = source[:marker_at]
    if re.search(r"(^|[,\n])\s*header\s*(?:,|\{)", pre_surface) and "background: var(--valtren-navy) !important" in pre_surface:
        raise RuntimeError("Seletor genérico header ainda controla surface navy")
    if re.search(r"(^|[,\n])\s*footer\s*(?:,|\{)", pre_surface) and "background: var(--valtren-navy) !important" in pre_surface:
        raise RuntimeError("Seletor genérico footer ainda controla surface navy")

    counts = {"shell": 0, "overlay": 0, "accent": 0, "overridden": 0, "violations": 0}
    violations: list[str] = []
    for position, selector, backgrounds in _rules(source):
        if ".crm" not in selector:
            continue
        low = selector.lower()
        if "var(--crm-surface-dark)" in " ".join(backgrounds).lower():
            if any(token in low for token in (".crm-topbar", ".crm-sidebar", ".crm-sidebar-head")):
                counts["shell"] += 1
                continue
            violations.append(f"surface-dark fora do shell: {selector}")
            counts["violations"] += 1
            continue
        if any(token in low for token in ("overlay", "backdrop")):
            counts["overlay"] += 1
            continue
        if any(token in low for token in ("badge", "status", "icon", "avatar", "legend", "series", "indicator", "today>header span", "today>header strong")):
            counts["accent"] += 1
            continue
        structural = any(token in low for token in (
            "panel", "card", "modal", "drawer", "header", "footer", "table", "toolbar", "tabs",
            "primary", "pagination", "bulk", "toast", "stepper", "profile-head", "logo-upload", "view-toggle",
        ))
        if structural and position < product_at:
            counts["overridden"] += 1
            continue
        violations.append(f"dark background estrutural não classificado: {selector} => {backgrounds}")
        counts["violations"] += 1

    if violations:
        detail = " | ".join(violations[:20])
        raise RuntimeError(f"Dark surface ownership gate falhou ({len(violations)}): {detail}")

    for token in (
        ".crm-app-shell .crm-dashboard-panel>header",
        ".crm-app-shell .crm-dashboard-panel-body",
        ".crm-app-shell .crm-dashboard-group-card",
        ".crm-app-shell .crm-dashboard-cost-grid article",
        ".crm-app-shell .crm-dashboard-ranking a",
    ):
        if token not in source[marker_at:product_at]:
            raise RuntimeError(f"Proteção de surface do Dashboard ausente: {token}")
    print(
        "Dark surface ownership gate: PASS "
        f"shell={counts['shell']} overlay={counts['overlay']} accent={counts['accent']} "
        f"overridden={counts['overridden']} violations=0"
    )
    return counts


def apply_crm_dark_surface_system() -> int:
    if not CSS.exists():
        raise FileNotFoundError("assets/valtren-brand.css ausente")
    css = CSS.read_text(encoding="utf-8")
    css = _scope_legacy_global_selectors(css)
    css = _insert_before_product_review(css)
    assert_dark_surface_ownership(css)
    CSS.write_text(css, encoding="utf-8")
    print("Dark shell/light workspace aplicado: navy estrutural restrito ao Header global e Sidebar.")
    return 1


if __name__ == "__main__":
    apply_crm_dark_surface_system()
