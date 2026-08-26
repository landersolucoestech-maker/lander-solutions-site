from __future__ import annotations

import re
import subprocess
from pathlib import Path

import crm_accessibility_semantics as accessibility

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"


def _tag_for_id(source: str, control_id: str) -> str:
    pattern = re.compile(rf'<(?:input|select|textarea)\b(?=[^>]*\bid="{re.escape(control_id)}")[^>]*>', re.I)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"Browser readiness: {control_id} possui {len(matches)} ocorrência(s)")
    return matches[0].group(0)


def assert_browser_readiness() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    syntax = subprocess.run(["node", "--check", str(APP)], capture_output=True, text=True)
    if syntax.returncode != 0:
        raise RuntimeError(f"Browser readiness: bundle inválido: {(syntax.stderr or syntax.stdout).strip()}")

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
        expected = f'aria-label="{label}"'
        if expected not in tag and not re.search(r'\b(?:aria-labelledby|title)=', tag, re.I):
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
        f"{len(accessibility.ACTION_LABELS)} dynamic labels, Agenda internal scroller)"
    )
    return 1


if __name__ == "__main__":
    assert_browser_readiness()
