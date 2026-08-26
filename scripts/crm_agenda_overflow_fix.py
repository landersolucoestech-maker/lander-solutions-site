from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_START = "/* VALTREN AGENDA OVERFLOW FIX START */"
CSS_END = "/* VALTREN AGENDA OVERFLOW FIX END */"

MAIN_OLD = '''      <main class="crm-main">
        <header class="crm-topbar crm-agenda-topbar">'''
MAIN_NEW = '''      <main class="crm-main crm-agenda-main">
        <header class="crm-topbar crm-agenda-topbar">'''

CALENDAR_OLD = '''          ${crmAgendaCalendar(events)}
        </section>'''
CALENDAR_NEW = '''          <div class="crm-agenda-scroll">${crmAgendaCalendar(events)}</div>
        </section>'''

SEARCH_OLD = '''<label class="crm-agenda-search"><input id="crm-agenda-search" value="${esc(state.crmAgendaSearch)}" placeholder="Buscar evento..." autocomplete="off"></label>'''
SEARCH_NEW = '''<label class="crm-agenda-search"><input id="crm-agenda-search" aria-label="Pesquisar eventos" value="${esc(state.crmAgendaSearch)}" placeholder="Buscar evento..." autocomplete="off"></label>'''

CSS_PATCH = f'''
{CSS_START}
.crm-agenda-main{{
  min-width:0!important;
  max-width:100%!important;
  overflow-x:hidden!important;
}}
.crm-agenda-workspace{{
  min-width:0!important;
  max-width:100%!important;
  overflow-x:hidden!important;
}}
.crm-agenda-scroll{{
  width:100%;
  max-width:100%;
  min-width:0;
  overflow-x:auto;
  overflow-y:hidden;
  -webkit-overflow-scrolling:touch;
  box-sizing:border-box;
}}
.crm-agenda-scroll>.crm-agenda-calendar{{
  max-width:none!important;
}}
@media(max-width:760px){{
  .crm-agenda-scroll>.crm-agenda-calendar{{overflow:visible!important}}
  .crm-agenda-view-toggle{{height:auto!important;min-height:36px!important}}
  .crm-agenda-view-toggle button{{height:32px!important;min-height:32px!important}}
}}
{CSS_END}
'''.strip()


def _replace_once_or_confirm(source: str, old: str, new: str, label: str) -> str:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        return source.replace(old, new, 1)
    if old_count == 0 and new_count == 1:
        return source
    raise RuntimeError(f"{label} divergente: old={old_count} new={new_count}")


def _replace_css_block(css: str) -> str:
    start_count = css.count(CSS_START)
    end_count = css.count(CSS_END)
    if start_count == 0 and end_count == 0:
        return css.rstrip() + "\n\n" + CSS_PATCH + "\n"
    if start_count != 1 or end_count != 1:
        raise RuntimeError(f"Markers da Agenda divergentes: start={start_count} end={end_count}")
    start = css.index(CSS_START)
    end = css.index(CSS_END, start) + len(CSS_END)
    current = css[start:end].strip()
    if current == CSS_PATCH:
        return css
    return css[:start] + CSS_PATCH + css[end:]


def apply_crm_agenda_overflow_fix() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    app = _replace_once_or_confirm(app, MAIN_OLD, MAIN_NEW, "main da Agenda")
    app = _replace_once_or_confirm(app, CALENDAR_OLD, CALENDAR_NEW, "container de scroll da Agenda")
    app = _replace_once_or_confirm(app, SEARCH_OLD, SEARCH_NEW, "busca acessível da Agenda")
    APP.write_text(app, encoding="utf-8")
    syntax = subprocess.run(["node", "--check", str(APP)], capture_output=True, text=True)
    if syntax.returncode != 0:
        raise RuntimeError(f"Bundle inválido após correção responsiva da Agenda: {(syntax.stderr or syntax.stdout).strip()}")

    css = CSS.read_text(encoding="utf-8")
    updated = _replace_css_block(css)
    if updated != css:
        CSS.write_text(updated, encoding="utf-8")

    print("Agenda: overflow horizontal isolado no calendário e targets de visualização normalizados.")
    return 1


if __name__ == "__main__":
    apply_crm_agenda_overflow_fix()
