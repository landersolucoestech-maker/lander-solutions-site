from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import crm_product_system_review as review


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


def apply_crm_product_system_review() -> int:
    if not review.APP.exists() or not review.CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")

    app = review.APP.read_text(encoding="utf-8")
    _assert_js_syntax(app, "entrada da revisão global")

    start = app.find(review.HEADER_START)
    end = app.find(review.HEADER_END, start) if start >= 0 else -1
    if start < 0 or end < 0:
        raise RuntimeError("Bloco compartilhado do Account Menu não encontrado")
    app = app[:start] + review.HEADER_HELPERS + app[end + len(review.HEADER_END):]
    _assert_js_syntax(app, "Account Menu compartilhado")

    replacements = {
        "crmRelEnsureState": review.EMPTY_RELATIONSHIP_STATE,
        "crmFullUsers": review.EMPTY_USERS,
        "crmDashboardPage": review.DASHBOARD,
        "crmSettingsCompanyBody": review.SETTINGS_COMPANY,
        "crmSettingsNotificationsBody": review.SETTINGS_NOTIFICATIONS,
        "crmSettingsSecurityBody": review.SETTINGS_SECURITY,
        "crmSettingsIntegrationsBody": review.SETTINGS_INTEGRATIONS,
        "crmSettingsAuditBody": review.SETTINGS_AUDIT,
        "crmSettingsUsersBody": review.SETTINGS_USERS,
        "crmCanonicalProfilePage": review.PROFILE,
    }
    for name, replacement in replacements.items():
        app = review._replace_function(app, name, replacement)
        _assert_js_syntax(app, name)

    for old, new in [
        ("Protótipo · dados ilustrativos", ""),
        ("CRM Integrado", "Sistema Interno"),
        ("Módulos do CRM", "Módulos do Sistema Interno"),
        ("Não conectado", "Não configurado"),
        ("state.crmUserName || 'Administrador'", "state.crmUserName || ''"),
        ("state.crmUserName||'Administrador'", "state.crmUserName||''"),
    ]:
        app = app.replace(old, new)
    _assert_js_syntax(app, "normalização textual final")
    review.APP.write_text(app, encoding="utf-8")

    css = review.CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN PRODUCT SYSTEM REVIEW \*/.*\Z", "", css, flags=re.S)
    review.CSS.write_text(css.rstrip() + "\n\n" + review.CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in review.ROOT.rglob("*.html"):
        rel = path.relative_to(review.ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={review.CACHE_VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Revisão global materializada com validação sintática por etapa.")
    return 1


if __name__ == "__main__":
    apply_crm_product_system_review()
