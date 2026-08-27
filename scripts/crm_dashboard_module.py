from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_dashboard_core.js"
PARTICIPATION_CORE = ROOT / "scripts" / "crm_dashboard_participation_core.js"
BROWSER = ROOT / "scripts" / "crm_dashboard_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_dashboard.css"
DASHBOARD_START = "  // VALTREN CRM DASHBOARD START\n"
DASHBOARD_END = "  // VALTREN CRM DASHBOARD END\n"
CSS_MARKER = "/* VALTREN EXECUTIVE DASHBOARD */"
LEGACY_CSS_MARKER = "/* VALTREN CRM INTEGRATED */"
CACHE_VERSION = "20260827-executive-dashboard-v3"

LEGACY_DASHBOARD_TOKENS = [
    "kpi('Contatos'",
    "kpi('Leads'",
    "kpi('Clientes'",
    "Indicadores essenciais de CRM e Financeiro",
    "O que precisa de atenção",
    "Revisar pipeline comercial",
    "Acessos principais",
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


def _source_block() -> str:
    core = CORE.read_text(encoding="utf-8").strip()
    participation_core = PARTICIPATION_CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
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
    old_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage();"
    canonical_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query);"
    if old_route in app:
        app = app.replace(old_route, canonical_route)
    if canonical_route in app:
        return app
    # O bootstrap histórico possui mais de uma forma válida de rotear o Dashboard.
    # crmDashboardPage aceita query opcional, então qualquer rota já existente para
    # /crm/dashboard deve ser preservada em vez de depender de uma âncora fixa.
    if "path === '/crm/dashboard'" in app or "path==='/crm/dashboard'" in app:
        return app
    anchor = "    else if (path === '/contato') app.innerHTML = contactPage(query);"
    if app.count(anchor) < 1:
        raise RuntimeError("Rota do Dashboard ausente e âncora de compatibilidade não encontrada")
    return app.replace(anchor, canonical_route + "\n" + anchor, 1)


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
    _assert_js_syntax(core, "crm_dashboard_core.js")
    _assert_js_syntax(participation_core, "crm_dashboard_participation_core.js")
    _assert_js_syntax(browser, "crm_dashboard_browser.js")
    missing_core = [name for name in REQUIRED_CORE_FUNCTIONS if name not in core]
    missing_participation = [name for name in REQUIRED_PARTICIPATION_CORE_FUNCTIONS if name not in participation_core]
    missing_browser = [name for name in REQUIRED_BROWSER_COMPONENTS if name not in browser]
    if missing_core or missing_participation or missing_browser:
        raise RuntimeError(f"Arquitetura do Dashboard incompleta: core={missing_core}, participation={missing_participation}, browser={missing_browser}")
    for token in LEGACY_DASHBOARD_TOKENS:
        if token in browser:
            raise RuntimeError(f"Dashboard legado sobreviveu no browser owner: {token}")
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
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
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
    app = _materialize_dashboard(APP.read_text(encoding="utf-8"))
    app = _materialize_route(app)
    if app.count(DASHBOARD_START) != 1 or app.count(DASHBOARD_END) != 1 or app.count("function crmDashboardPage(") != 1:
        raise RuntimeError("Dashboard executivo não ficou materializado exatamente uma vez")
    if app.count("ValtrenDashboardParticipationCore") < 1 or app.count("__participationIntegrityWrapped") < 1:
        raise RuntimeError("Núcleo de integridade das Participações não foi materializado")
    for token in LEGACY_DASHBOARD_TOKENS:
        if token in app[app.index(DASHBOARD_START):app.index(DASHBOARD_END)]:
            raise RuntimeError(f"Dashboard materializado contém estrutura CRM descartada: {token}")
    _assert_js_syntax(app, "bundle materializado")
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css_block(css)
    if updated_css != css:
        CSS.write_text(updated_css, encoding="utf-8")
    _update_cache_busters()
    print("Dashboard executivo materializado: Valtren consolidada, performance por unidades internas, Participações/Repasses sem dupla contagem, faturado x recebido e arquitetura financeira sem dados fictícios.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard()
