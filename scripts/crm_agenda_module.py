from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = ROOT / "src" / "modules" / "agenda" / "source"
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260829-agenda-module-v1"


def _parts(prefix: str) -> str:
    files = sorted(PARTS_DIR.glob(prefix))
    if not files:
        raise RuntimeError(f"Partes ausentes em src/modules/agenda/source: {prefix}")
    return "".join(path.read_text(encoding="utf-8") for path in files)


def _write_cache_version() -> None:
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")


def apply_crm_agenda_module() -> int:
    app = APP.read_text(encoding="utf-8")
    js_block = _parts("crm_agenda_module.js.part*")
    css_patch = _parts("crm_agenda_module.css.part*")

    app = re.sub(
        r"  // VALTREN CRM AGENDA EVENTS START\n.*?  // VALTREN CRM AGENDA EVENTS END\n",
        "",
        app,
        flags=re.S,
    )
    app = re.sub(
        r"\n?  // VALTREN CRM AGENDA FIDELITY START\n.*?  // VALTREN CRM AGENDA FIDELITY END\n",
        "\n",
        app,
        flags=re.S,
    )

    # Agenda is a top-level functional module. Remove both historical and canonical
    # route emissions before registering one deterministic route block.
    for route in (
        "\n    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query);",
        "\n    else if (path === '/agenda') app.innerHTML = crmAgendaPage(query);",
    ):
        app = app.replace(route, "")

    if app.count("  function crmHeaderActions(context=''){") != 1:
        raise RuntimeError("Header compartilhado contextual não encontrado para Agenda")
    if not re.search(r"context\s*===\s*['\"]agenda['\"]", app):
        raise RuntimeError("Header compartilhado não oferece o contexto Agenda")

    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora de funções para Agenda divergente: {app.count(anchor)}")
    app = app.replace(anchor, js_block + "\n" + anchor, 1)

    route_anchor = "    else if (path === '/crm/relationships') app.innerHTML = crmRelationshipsPage(query);"
    canonical_route = "    else if (path === '/agenda') app.innerHTML = crmAgendaPage(query);"
    compatibility_route = "    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query); // legacy compatibility"
    count = app.count(route_anchor)
    if count < 1:
        raise RuntimeError("Âncora de roteamento não encontrada para registrar Agenda global")
    app = app.replace(route_anchor, route_anchor + "\n" + canonical_route + "\n" + compatibility_route, 1)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM AGENDA EVENTS \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + css_patch.strip() + "\n", encoding="utf-8")
    _write_cache_version()
    print("Agenda materializada como módulo global em /agenda; /crm/agenda preservada apenas como compatibilidade temporária.")
    return 1


if __name__ == "__main__":
    apply_crm_agenda_module()
