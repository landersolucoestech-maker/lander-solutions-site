from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-agenda-events-v1"


def _parts(prefix: str) -> str:
    files = sorted(HERE.glob(prefix))
    if not files:
        raise RuntimeError(f"Partes ausentes: {prefix}")
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

    app = app.replace('\n          <a href="#/crm/agenda">${icon(\'calendar\',18)}<span>Agenda</span></a>', '')
    app = app.replace('\n        <a class="${active === \'agenda\' ? \'active\' : \'\'}" href="#/crm/agenda">${icon(\'calendar\',18)}<span>Agenda</span></a>', '')
    app = app.replace('\n      ${context === \'agenda\' ? `<button class="crm-header-create crm-header-create-agenda" type="button" data-action="crm-agenda-create">${icon(\'plus\',15)}<span>Novo Evento</span></button>` : \'\'}', '')
    app = app.replace("\n    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query);", '')

    dashboard_nav = '''          <a class="active" href="#/crm/dashboard">${icon('layers',18)}<span>Dashboard</span></a>\n          <a href="#/crm/relationships">${icon('users',18)}<span>CRM</span></a>'''
    dashboard_agenda = dashboard_nav + '''\n          <a href="#/crm/agenda">${icon('calendar',18)}<span>Agenda</span></a>'''
    if dashboard_nav in app and 'href="#/crm/agenda"' not in app:
        app = app.replace(dashboard_nav, dashboard_agenda, 1)

    rel_link = '''        <a class="${active === 'relationships' ? 'active' : ''}" href="#/crm/relationships">${icon('users',18)}<span>CRM</span></a>'''
    rel_agenda = rel_link + '''\n        <a class="${active === 'agenda' ? 'active' : ''}" href="#/crm/agenda">${icon('calendar',18)}<span>Agenda</span></a>'''
    if rel_link not in app:
        raise RuntimeError("Link compartilhado do CRM não encontrado para adicionar Agenda")
    app = app.replace(rel_link, rel_agenda, 1)

    lead_button = '''      ${context === 'leads' ? `<button class="crm-header-create crm-header-create-lead" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>` : ''}'''
    agenda_button = lead_button + '''\n      ${context === 'agenda' ? `<button class="crm-header-create crm-header-create-agenda" type="button" data-action="crm-agenda-create">${icon('plus',15)}<span>Novo Evento</span></button>` : ''}'''
    if lead_button not in app:
        raise RuntimeError("Ações contextuais do header CRM não encontradas")
    app = app.replace(lead_button, agenda_button, 1)

    anchor = "  function contactPage(query)"
    if anchor not in app:
        raise RuntimeError("Âncora de funções para Agenda não encontrada")
    app = app.replace(anchor, js_block + "\n" + anchor, 1)

    route_anchor = "    else if (path === '/crm/relationships') app.innerHTML = crmRelationshipsPage(query);"
    agenda_route = "    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query);"
    if agenda_route not in app:
        count = app.count(route_anchor)
        if count < 2:
            raise RuntimeError(f"Rotas do CRM não encontradas nas duas renderizações: {count}")
        app = app.replace(route_anchor, route_anchor + "\n" + agenda_route)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM AGENDA EVENTS \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + css_patch.strip() + "\n", encoding="utf-8")
    _write_cache_version()
    print("Módulo Agenda & Eventos aplicado fielmente à referência anexada.")
    return 1


if __name__ == "__main__":
    apply_crm_agenda_module()
