from __future__ import annotations

import re
import subprocess
from pathlib import Path

import crm_accessibility_semantics as accessibility

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
TEXT_SUFFIXES = {".py", ".js", ".css", ".md", ".yml", ".yaml", ".html", ".json", ".txt"}


def _tag_for_id(source: str, control_id: str) -> str:
    pattern = re.compile(rf'<(?:input|select|textarea)\b(?=[^>]*\bid="{re.escape(control_id)}")[^>]*>', re.I)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"Browser readiness: {control_id} possui {len(matches)} ocorrência(s)")
    return matches[0].group(0)


def _repository_integrity_assertions() -> dict[str, int]:
    forbidden_integration = "Sound" + "charts"
    offenders: list[str] = []
    files_scanned = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "_site"} for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files_scanned += 1
        if forbidden_integration.casefold() in text.casefold():
            offenders.append(str(rel))
    if offenders:
        raise RuntimeError(f"Repository integrity: integração proibida ainda referenciada em {sorted(offenders)}")

    product_source = (ROOT / "scripts" / "crm_product_system_review.py").read_text(encoding="utf-8")
    conflicting_product_fragments = (
        "width:min(100%,1440px)",
        "gap:20px;background:var(--crm-surface);border-bottom",
        "background:var(--crm-text)!important;color:#FFFFFF!important;border-color:var(--crm-text)!important",
    )
    conflicts = [frag for frag in conflicting_product_fragments if frag in product_source]
    if conflicts:
        raise RuntimeError(f"Repository integrity: Product Review ainda emite ownership visual conflitante: {conflicts}")

    surface_source = (ROOT / "scripts" / "crm_dark_surface_system.py").read_text(encoding="utf-8")
    required_surface_scope = '.crm-app-shell .crm-main [class*="popover"]:not(.crm-account-popover)'
    if required_surface_scope not in surface_source:
        raise RuntimeError("Repository integrity: Account Popover ainda está sujeito ao seletor transversal de popovers do workspace")

    header_source = (ROOT / "scripts" / "crm_global_header.py").read_text(encoding="utf-8")
    if ".crm-account-popover" not in header_source or "background:#fff" not in header_source.lower():
        raise RuntimeError("Repository integrity: owner do Header não declara Account Popover light")

    return {"text_files_scanned": files_scanned, "forbidden_integration_occurrences": 0, "ownership_conflicts": 0}


def _runtime_security_assertions(app: str) -> dict[str, int]:
    unsafe_patterns = {
        "eval": re.compile(r"\beval\s*\("),
        "new Function": re.compile(r"\bnew\s+Function\s*\("),
        "javascript-url": re.compile(r"javascript\s*:", re.I),
        "direct-local-storage-parse": re.compile(r"JSON\.parse\s*\(\s*(?:window\.)?(?:localStorage|sessionStorage)\.getItem\s*\(", re.I),
        "debug-console-log": re.compile(r"\bconsole\.log\s*\("),
    }
    unsafe_hits = [label for label, pattern in unsafe_patterns.items() if pattern.search(app)]
    if unsafe_hits:
        raise RuntimeError(f"Browser readiness: padrões runtime inseguros/legados encontrados: {unsafe_hits}")

    blank_links = re.findall(r"<a\b[^>]*\btarget\s*=\s*(['\"])_blank\1[^>]*>", app, flags=re.I)
    # The previous expression only confirms presence. Inspect complete tags for rel safeguards.
    unsafe_blank_tags = []
    for match in re.finditer(r"<a\b[^>]*\btarget\s*=\s*(['\"])_blank\1[^>]*>", app, flags=re.I):
        tag = match.group(0)
        rel = re.search(r"\brel\s*=\s*(['\"])(.*?)\1", tag, flags=re.I)
        tokens = set((rel.group(2) if rel else "").lower().split())
        if not {"noopener", "noreferrer"}.intersection(tokens):
            unsafe_blank_tags.append(tag[:180])
    if unsafe_blank_tags:
        raise RuntimeError(f"Browser readiness: target=_blank sem rel seguro: {unsafe_blank_tags[:5]}")

    fabricated_auth = [token for token in ("crmUserName || 'Administrador'", "crmUserInitials || 'AD'") if token in app]
    if fabricated_auth:
        raise RuntimeError(f"Browser readiness: identidade de autenticação fictícia detectada: {fabricated_auth}")

    return {"unsafe_runtime_patterns": 0, "unsafe_blank_links": 0, "fabricated_auth_fallbacks": 0}


def assert_browser_readiness() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    syntax = subprocess.run(["node", "--check", str(APP)], capture_output=True, text=True)
    if syntax.returncode != 0:
        raise RuntimeError(f"Browser readiness: bundle inválido: {(syntax.stderr or syntax.stdout).strip()}")

    repo_integrity = _repository_integrity_assertions()
    runtime_security = _runtime_security_assertions(app)

    for token in (
        'class="crm-main crm-agenda-main"',
        'class="crm-agenda-scroll">${crmAgendaCalendar(events)}</div>',
        'aria-label="Pesquisar eventos"',
    ):
        if token not in app:
            raise RuntimeError(f"Browser readiness: contrato da Agenda ausente: {token}")

    for token in (
        "/* VALTREN AGENDA OVERFLOW FIX START */",
        "/* VALTREN AGENDA OVERFLOW FIX END */",
        ".crm-agenda-scroll",
        "overflow-x:auto",
        ".crm-agenda-week{min-width:980px!important}",
        ".crm-agenda-month{min-width:760px}",
    ):
        if token not in css:
            raise RuntimeError(f"Browser readiness: CSS da Agenda ausente: {token}")

    for control_id, label in accessibility.STATIC_LABELS.items():
        tag = _tag_for_id(app, control_id)
        if not accessibility.has_accessible_name_for_id(app, control_id, label):
            raise RuntimeError(f"Browser readiness: accessible name ausente em {control_id}: {tag}")

    for action, label in accessibility.ACTION_LABELS.items():
        pattern = re.compile(rf'<(?:input|select|textarea)\b(?=[^>]*\bdata-action="{re.escape(action)}")[^>]*>', re.I)
        matches = list(pattern.finditer(app))
        if len(matches) != 1:
            raise RuntimeError(f"Browser readiness: data-action {action} possui {len(matches)} ocorrência(s)")
        tag = matches[0].group(0)
        if f'aria-label="{label}"' not in tag:
            raise RuntimeError(f"Browser readiness: accessible name dinâmico ausente em {action}: {tag}")

    if accessibility.RULE_FILTER_ACCESSIBLE not in app:
        raise RuntimeError("Browser readiness: filtros de Regras de Categorização sem nomes acessíveis")
    for replacement in accessibility.PAGINATION_REPLACEMENTS.values():
        if replacement not in app:
            raise RuntimeError("Browser readiness: paginação icon-only sem accessible name")

    if css.count(accessibility.CSS_START) != 1 or css.count(accessibility.CSS_END) != 1:
        raise RuntimeError("Browser readiness: markers de acessibilidade divergentes")

    print(
        f"Browser readiness materialized assertions: PASS "
        f"({len(accessibility.STATIC_LABELS)} static labels, "
        f"{len(accessibility.ACTION_LABELS)} dynamic labels, Agenda internal scroller, "
        f"repo_files={repo_integrity['text_files_scanned']}, forbidden_integration=0, "
        f"ownership_conflicts=0, runtime_security={runtime_security})"
    )
    return 1


if __name__ == "__main__":
    assert_browser_readiness()
