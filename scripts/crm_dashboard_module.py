from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MODULE_DIR = ROOT / "web" / "src" / "modules" / "dashboard"
CORE = MODULE_DIR / "core.js"
PARTICIPATION_CORE = MODULE_DIR / "participation-core.js"
BROWSER = MODULE_DIR / "browser.js"
MODULE_CSS = MODULE_DIR / "styles.css"
DASHBOARD_START = "  // VALTREN CRM DASHBOARD START\n"
DASHBOARD_END = "  // VALTREN CRM DASHBOARD END\n"
CSS_MARKER = "/* VALTREN EXECUTIVE DASHBOARD */"
LEGACY_CSS_MARKER = "/* VALTREN CRM INTEGRATED */"
CACHE_VERSION = "20260829-dashboard-module-v1"

LEGACY_DASHBOARD_TOKENS = [
    "kpi('Contatos'",
    "kpi('Leads'",
    "kpi('Clientes'",
    "Indicadores essenciais de CRM e Financeiro",
    "O que precisa de atenção",
    "Revisar pipeline comercial",
    "Acessos principais",
]

DASHBOARD_HEADER_EYEBROW = "<span>Sistema Interno</span>"
DASHBOARD_INTRO_BLOCK = '<div class="crm-page-header"><div><h2>Visão Econômica Consolidada</h2><p>Empresa: Valtren Solutions · Produtos, SaaS, Serviços e Unidades de Negócio são dimensões gerenciais internas.</p></div></div>'
REMOVED_DASHBOARD_COPY = [
    "Sistema Interno",
    "Visão Econômica Consolidada",
    "Empresa: Valtren Solutions · Produtos, SaaS, Serviços e Unidades de Negócio são dimensões gerenciais internas.",
]

REQUIRED_BROWSER_COMPONENTS = [
    "crmDashboardKpis",
    "crmDashboardBridge",
    "crmDashboardUnitTable",
    "crmDashboardProductsVsServices",
    "crmDashboardBarList",
    "crmDashboardTrendSvg",
    "crmDashboardParticipationSummary",
    "crmDashboardBilledVsReceived",
    "crmDashboardReceivablesPayables",
    "crmDashboardDeductions",
    "crmDashboardCostStructure",
    "crmDashboardRankings",
    "crmDashboardEmptyState",
]

REQUIRED_CORE_FUNCTIONS = [
    "buildUnitPerformance",
    "consolidatedFromDre",
    "buildProductsVsServices",
    "buildTrend",
    "buildFiscalSummary",
    "buildParticipationSummary",
    "buildDeductionBreakdown",
    "buildCostStructure",
    "buildRankings",
    "buildDashboard",
]

REQUIRED_PARTICIPATION_CORE_FUNCTIONS = [
    "participationUnitKey",
    "buildParticipationSummary",
    "__participationIntegrityWrapped",
]


def _assert_js_syntax(source: str, stage: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
            raise RuntimeError(f"Dashboard produziu JavaScript inválido em {stage}: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def _dashboard_browser_source() -> str:
    browser = BROWSER.read_text(encoding="utf-8").strip()
    eyebrow_count = browser.count(DASHBOARD_HEADER_EYEBROW)
    intro_count = browser.count(DASHBOARD_INTRO_BLOCK)
    if eyebrow_count != 1 or intro_count != 1:
        raise RuntimeError(
            f"Hierarquia canônica do Dashboard divergente: eyebrow={eyebrow_count}, intro={intro_count}"
        )
    browser = browser.replace(DASHBOARD_HEADER_EYEBROW, "", 1)
    browser = browser.replace(DASHBOARD_INTRO_BLOCK, "", 1)
    return browser


def _source_block() -> str:
    core = CORE.read_text(encoding="utf-8").strip()
    participation_core = PARTICIPATION_CORE.read_text(encoding="utf-8").strip()
    browser = _dashboard_browser_source()
    return DASHBOARD_START + core + "\n\n" + participation_core + "\n\n" + browser + "\n" + DASHBOARD_END


def _materialize_dashboard(app: str) -> str:
    block = _source_block()
    start_count = app.count(DASHBOARD_START)
    end_count = app.count(DASHBOARD_END)
    if start_count == 1 and end_count == 1:
        start = app.index(DASHBOARD_START)
        end = app.index(DASHBOARD_END, start) + len(DASHBOARD_END)
        return app if app[start:end] == block else app[:start] + block + app[end:]
    if start_count or end_count:
        raise RuntimeError(f"Marcadores do Dashboard divergentes: {start_count}/{end_count}")

    function_anchor = "  function crmDashboardPage("
    contact_anchor = "  function contactPage(query)"
    function_count = app.count(function_anchor)
    if app.count(contact_anchor) != 1 or function_count not in {0, 1}:
        raise RuntimeError(f"Âncoras do Dashboard inválidas: dashboard={function_count}, contactPage={app.count(contact_anchor)}")
    contact_at = app.index(contact_anchor)
    if function_count == 1:
        start = app.index(function_anchor)
        if start >= contact_at:
            raise RuntimeError("crmDashboardPage apareceu depois da âncora contactPage")
        return app[:start] + block + "\n" + app[contact_at:]
    return app[:contact_at] + block + "\n" + app[contact_at:]


def _materialize_route(app: str) -> str:
    canonical_route = "    else if (path === '/dashboard') app.innerHTML = crmDashboardPage(query);"
    compatibility_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query); // legacy compatibility"

    if app.count(canonical_route) == 1 and app.count(compatibility_route) == 1:
        return app

    legacy_patterns = (
        "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage();",
        "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query);",
        compatibility_route,
        canonical_route,
    )
    for route in legacy_patterns:
        app = app.replace(route + "\n", "").replace(route, "")

    anchor = "    else if (path === '/contato') app.innerHTML = contactPage(query);"
    if app.count(anchor) < 1:
        raise RuntimeError("Âncora de compatibilidade não encontrada para registrar Dashboard global")
    return app.replace(anchor, canonical_route + "\n" + compatibility_route + "\n" + anchor, 1)


def _replace_css_block(css: str) -> str:
    desired = MODULE_CSS.read_text(encoding="utf-8").strip()
    marker_at = css.find(CSS_MARKER)
    if marker_at < 0:
        marker_at = css.find(LEGACY_CSS_MARKER)
    if marker_at < 0:
        return css.rstrip() + "\n\n" + desired + "\n"
    next_marker = css.find("\n/* ", marker_at + 3)
    end = len(css) if next_marker < 0 else next_marker + 1
    current = css[marker_at:end].strip()
    if current == desired:
        return css
    prefix = css[:marker_at].rstrip()
    suffix = css[end:].lstrip("\n")
    return prefix + "\n\n" + desired + "\n" + (("\n" + suffix) if suffix else "")


def _validate_sources() -> None:
    for path in (CORE, PARTICIPATION_CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)
    core = CORE.read_text(encoding="utf-8")
    participation_core = PARTICIPATION_CORE.read_text(encoding="utf-8")
    browser = BROWSER.read_text(encoding="utf-8")
    rendered_browser = _dashboard_browser_source()
    _assert_js_syntax(core, "web/src/modules/dashboard/core.js")
    _assert_js_syntax(participation_core, "web/src/modules/dashboard/participation-core.js")
    _assert_js_syntax(rendered_browser, "web/src/modules/dashboard/browser.js normalizado")
    missing_core = [name for name in REQUIRED_CORE_FUNCTIONS if name not in core]
    missing_participation = [name for name in REQUIRED_PARTICIPATION_CORE_FUNCTIONS if name not in participation_core]
    missing_browser = [name for name in REQUIRED_BROWSER_COMPONENTS if name not in rendered_browser]
    if missing_core or missing_participation or missing_browser:
        raise RuntimeError(f"Arquitetura do Dashboard incompleta: core={missing_core}, participation={missing_participation}, browser={missing_browser}")
    for token in LEGACY_DASHBOARD_TOKENS:
        if token in rendered_browser:
            raise RuntimeError(f"Dashboard legado sobreviveu no browser owner: {token}")
    for token in REMOVED_DASHBOARD_COPY:
        if token in rendered_browser:
            raise RuntimeError(f"Dashboard voltou a emitir copy estrutural removida: {token}")
    forbidden_company_models = ["Empresa: Visa Fácil", "Empresa: Music OS 360", "Empresa: Vivendo da Música", "Empresa: Dica de Cria"]
    for token in forbidden_company_models:
        if token in browser or token in core or token in participation_core:
            raise RuntimeError(f"Unidade de negócio foi tratada como empresa independente: {token}")
    if "single_legal_entity_with_internal_business_dimensions" not in core:
        raise RuntimeError("Core do Dashboard perdeu o modelo de entidade jurídica única")
    if "operatingResult-thirdPartyParticipation" not in core:
        raise RuntimeError("Fórmula central de Resultado Valtren ausente")
    if "participatingKeys" not in participation_core or "participatingUnits" not in participation_core:
        raise RuntimeError("Integridade de Participações não protege o resultado das unidades contra dupla contagem")


def _update_cache_busters() -> None:
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts", "api", "web"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", original)
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def apply_crm_dashboard() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    _validate_sources()

    original_app = APP.read_text(encoding="utf-8")
    app = _materialize_dashboard(original_app)
    app = _materialize_route(app)
    if app.count(DASHBOARD_START) != 1 or app.count(DASHBOARD_END) != 1 or app.count("function crmDashboardPage(") != 1:
        raise RuntimeError("Dashboard executivo não ficou materializado exatamente uma vez")
    if app.count("ValtrenDashboardParticipationCore") < 1 or app.count("__participationIntegrityWrapped") < 1:
        raise RuntimeError("Núcleo de integridade das Participações não foi materializado")
    if app.count("path === '/dashboard'") != 1:
        raise RuntimeError("Rota canônica /dashboard não ficou materializada exatamente uma vez")
    dashboard_block = app[app.index(DASHBOARD_START):app.index(DASHBOARD_END)]
    for token in LEGACY_DASHBOARD_TOKENS:
        if token in dashboard_block:
            raise RuntimeError(f"Dashboard materializado contém estrutura CRM descartada: {token}")
    for token in REMOVED_DASHBOARD_COPY:
        if token in dashboard_block:
            raise RuntimeError(f"Dashboard materializado voltou a emitir copy estrutural removida: {token}")
    _assert_js_syntax(app, "bundle materializado")
    app_changed = app != original_app
    if app_changed:
        APP.write_text(app, encoding="utf-8")

    original_css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css_block(original_css)
    css_changed = updated_css != original_css
    if css_changed:
        CSS.write_text(updated_css, encoding="utf-8")

    if app_changed or css_changed:
        _update_cache_busters()

    print("Dashboard materializado como módulo global em /dashboard; rotas /crm e /crm/dashboard preservadas apenas como compatibilidade temporária.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard()
