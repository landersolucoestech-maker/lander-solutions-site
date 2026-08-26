from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

import crm_dashboard_module as dashboard
import crm_product_system_review as review
import crm_sidebar_architecture as sidebar


def _assert_js_syntax(source: str, stage: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode == 0:
            return
        detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
        raise RuntimeError(f"Bundle inválido após {stage}: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_dashboard_idempotence() -> None:
    tracked = [dashboard.APP, dashboard.CSS, dashboard.ROOT / "index.html"]
    before = {path: _digest(path) for path in tracked if path.exists()}
    dashboard.apply_crm_dashboard()
    after = {path: _digest(path) for path in tracked if path.exists()}
    if before != after:
        changed = [str(path.relative_to(dashboard.ROOT)) for path in before if before.get(path) != after.get(path)]
        raise RuntimeError(f"Dashboard materializer não é idempotente após a cadeia: {changed}")
    _assert_js_syntax(dashboard.APP.read_text(encoding="utf-8"), "rerun idempotente do Dashboard")
    print("Dashboard materializer idempotence: PASS")


def _sidebar_declaration_lines(source: str) -> list[int]:
    pattern = re.compile(r"^[ \t]*function[ \t]+crmRelSidebar[ \t]*\(", re.MULTILINE)
    return [source.count("\n", 0, match.start()) + 1 for match in pattern.finditer(source)]


def _verify_sidebar_idempotence() -> None:
    tracked = [sidebar.APP, sidebar.CSS, sidebar.ROOT / "index.html"]
    before = {path: _digest(path) for path in tracked if path.exists()}
    source_before = sidebar.APP.read_text(encoding="utf-8")
    if source_before.count(sidebar.JS_START) != 1 or source_before.count(sidebar.JS_END) != 1:
        raise RuntimeError("Sidebar Architecture não chegou ao rerun com exatamente um par de markers")
    position_before = source_before.index(sidebar.JS_START)
    sidebar.apply_crm_sidebar_architecture()
    after = {path: _digest(path) for path in tracked if path.exists()}
    source_after = sidebar.APP.read_text(encoding="utf-8")
    position_after = source_after.index(sidebar.JS_START)
    if before != after or position_before != position_after:
        changed = [str(path.relative_to(sidebar.ROOT)) for path in before if before.get(path) != after.get(path)]
        raise RuntimeError(f"Sidebar Architecture não é idempotente após a cadeia: {changed}")
    if source_after.count(sidebar.JS_START) != 1 or source_after.count(sidebar.JS_END) != 1:
        raise RuntimeError("Sidebar Architecture duplicou markers após rerun")
    declaration_lines = _sidebar_declaration_lines(source_after)
    canonical_declaration = "  function crmRelSidebar(active='relationships',sub=''){"
    if len(declaration_lines) != 1 or source_after.count(canonical_declaration) != 1:
        raise RuntimeError(
            "crmRelSidebar não possui exatamente uma declaração canônica após rerun: "
            f"declarations={len(declaration_lines)} lines={declaration_lines} canonical={source_after.count(canonical_declaration)}"
        )
    _assert_js_syntax(source_after, "rerun idempotente da Sidebar Architecture")
    print("Sidebar Architecture materializer idempotence: PASS")


def apply_crm_product_system_review() -> int:
    if not review.APP.exists() or not review.CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")

    app = review.APP.read_text(encoding="utf-8")
    _assert_js_syntax(app, "entrada da revisão global")
    if app.count(dashboard.DASHBOARD_START) != 1 or app.count(dashboard.DASHBOARD_END) != 1:
        raise RuntimeError("Dashboard não chegou à revisão global sob ownership canônico")
    _verify_dashboard_idempotence()

    _verify_sidebar_idempotence()
    app = review.APP.read_text(encoding="utf-8")
    if app.count("  function crmHeaderActions(context=''){") != 1:
        raise RuntimeError("Header compartilhado não possui owner único")
    if 'Autenticação desativada' not in app or 'Nenhuma identidade é simulada' not in app:
        raise RuntimeError("Header perdeu transparência de autenticação")
    _assert_js_syntax(app, "Header e Sidebar canônicos")

    for start_anchor, end_anchor, replacement, label in review.REPLACEMENTS:
        app = review._replace_between(app, start_anchor, end_anchor, replacement, label)
        _assert_js_syntax(app, label)

    for old, new in [
        ("Protótipo · dados ilustrativos", ""),
        ("CRM Integrado", "Sistema Interno"),
        ("Módulos do CRM", "Módulos do Sistema Interno"),
        ("Não conectado", "Não configurado"),
        ("state.crmUserName || 'Administrador'", "state.crmUserName || ''"),
        ("state.crmUserName||'Administrador'", "state.crmUserName||''"),
        ("state.crmUserInitials || 'AD'", "state.crmUserInitials || ''"),
        ("state.crmUserInitials||'AD'", "state.crmUserInitials||''"),
    ]:
        app = app.replace(old, new)
    _assert_js_syntax(app, "normalização textual final")
    review.APP.write_text(app, encoding="utf-8")

    css = review.CSS.read_text(encoding="utf-8")
    updated_css = review._replace_css(css)
    if updated_css != css:
        review.CSS.write_text(updated_css, encoding="utf-8")

    for path in review.ROOT.rglob("*.html"):
        rel = path.relative_to(review.ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={review.CACHE_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Revisão global materializada com validação sintática incremental e Dashboard sob owner canônico.")
    return 1


if __name__ == "__main__":
    apply_crm_product_system_review()
