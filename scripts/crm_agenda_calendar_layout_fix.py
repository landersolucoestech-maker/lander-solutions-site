from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-agenda-calendar-layout-v1"

WEEK_FUNCTION = r'''  function crmAgendaWeekCalendar(events){
    const start=crmAgendaStartOfWeek(state.crmAgendaCurrentDate);
    const days=Array.from({length:7},(_,i)=>crmAgendaAddDays(start,i));
    const todayIso=crmAgendaISO(new Date());
    const headers=days.map((d)=>{
      const weekday=new Intl.DateTimeFormat('pt-BR',{weekday:'short'}).format(d).replace(/\.$/,'');
      const iso=crmAgendaISO(d);
      return `<div class="crm-agenda-week-head ${iso===todayIso?'today':''}"><span>${esc(`${weekday}., ${crmAgendaPad(d.getDate())}`)}</span></div>`;
    }).join('');
    const rows=[];
    for(let hour=8;hour<=18;hour++){
      rows.push(`<div class="crm-agenda-time-label">${crmAgendaPad(hour)}:00</div>`);
      days.forEach((d)=>{
        const iso=crmAgendaISO(d);
        const slot=events.filter((item)=>{
          if(item.startDate!==iso) return false;
          const parsed=parseInt(String(item.startTime||'08:00').split(':')[0],10);
          return (Number.isFinite(parsed)?parsed:8)===hour;
        });
        rows.push(`<div class="crm-agenda-time-cell ${iso===todayIso?'today':''}" data-date="${iso}" data-hour="${hour}">${slot.map((item)=>`<button type="button" class="crm-agenda-week-event ${crmAgendaStatusClass(item.status)}" data-action="crm-agenda-view" data-id="${esc(item.id)}" title="${esc(item.title)}"><strong>${esc(item.title)}</strong><small>${esc(crmAgendaTypeLabel(item.type))}</small></button>`).join('')}</div>`);
      });
    }
    return `<section class="crm-agenda-calendar crm-agenda-week"><div class="crm-agenda-week-corner"></div>${headers}${rows.join('')}</section>`;
  }
'''

DAY_FUNCTION = r'''  function crmAgendaDayCalendar(events){
    const iso=crmAgendaISO(state.crmAgendaCurrentDate);
    const label=new Intl.DateTimeFormat('pt-BR',{weekday:'long',day:'2-digit',month:'long'}).format(state.crmAgendaCurrentDate);
    const rows=[];
    for(let hour=8;hour<=18;hour++){
      const slot=events.filter((item)=>{
        if(item.startDate!==iso) return false;
        const parsed=parseInt(String(item.startTime||'08:00').split(':')[0],10);
        return (Number.isFinite(parsed)?parsed:8)===hour;
      });
      rows.push(`<div class="crm-agenda-time-label">${crmAgendaPad(hour)}:00</div><div class="crm-agenda-day-time-cell">${slot.map((item)=>`<button type="button" class="crm-agenda-week-event ${crmAgendaStatusClass(item.status)}" data-action="crm-agenda-view" data-id="${esc(item.id)}"><strong>${esc(item.title)}</strong><small>${esc(crmAgendaTypeLabel(item.type))}</small></button>`).join('')}</div>`);
    }
    return `<section class="crm-agenda-calendar crm-agenda-day-view"><header>${esc(label)}</header><div class="crm-agenda-day-time-grid">${rows.join('')}</div></section>`;
  }
'''

PAGE_FUNCTION = r'''  function crmAgendaPage(){
    crmAgendaEnsureState();
    const events=crmAgendaVisibleEvents();
    const hasFilters=!!state.crmAgendaSearch || state.crmAgendaTypeFilter!=='all-type' || state.crmAgendaStatusFilter!=='all-status';
    return `<div class="crm-app-shell">
      ${crmRelSidebar('agenda')}
      <main class="crm-main">
        <header class="crm-topbar crm-agenda-topbar">
          <div><h1>Agenda</h1><p>Gerencie shows, turnês e compromissos com foco operacional</p></div>
          ${crmHeaderActions('agenda')}
        </header>
        <section class="crm-workspace crm-agenda-workspace" aria-label="Agenda e Eventos">
          <div class="crm-agenda-toolbar">
            <button type="button" class="crm-agenda-today" data-action="crm-agenda-today">Hoje</button>
            <button type="button" class="icon-only" data-action="crm-agenda-prev" aria-label="Período anterior">‹</button>
            <button type="button" class="icon-only" data-action="crm-agenda-next" aria-label="Próximo período">›</button>
            <strong class="crm-agenda-period">${esc(crmAgendaPeriodLabel())}</strong>
            <label class="crm-agenda-search"><input id="crm-agenda-search" value="${esc(state.crmAgendaSearch)}" placeholder="Buscar evento..." autocomplete="off"></label>
            <select id="crm-agenda-type" aria-label="Tipo de evento"><option value="all-type">Todos</option>${CRM_AGENDA_TYPES.map(([v,l])=>`<option value="${v}" ${state.crmAgendaTypeFilter===v?'selected':''}>${l}</option>`).join('')}</select>
            <select id="crm-agenda-status" aria-label="Status"><option value="all-status">Todos</option>${CRM_AGENDA_FILTER_STATUSES.filter(([v])=>v!=='all-status').map(([v,l])=>`<option value="${v}" ${state.crmAgendaStatusFilter===v?'selected':''}>${l}</option>`).join('')}</select>
            <div class="crm-agenda-view-toggle" role="group" aria-label="Visualização">
              ${[['dia','Dia'],['semana','Semana'],['mes','Mês'],['ano','Ano']].map(([v,l])=>`<button type="button" class="${state.crmAgendaViewMode===v?'active':''}" data-action="crm-agenda-view-mode" data-view="${v}">${l}</button>`).join('')}
            </div>
            ${hasFilters?'<button type="button" class="crm-agenda-clear" data-action="crm-agenda-clear">Limpar</button>':''}
          </div>
          ${crmAgendaCalendar(events)}
        </section>
      </main>
    </div>`;
  }
'''

CSS_PATCH = r'''
/* VALTREN CRM AGENDA CALENDAR LAYOUT FIX */
.crm-agenda-workspace{width:100%!important;max-width:none!important;margin:0!important;padding:16px 16px 24px!important;background:#f3f6fa!important;box-sizing:border-box!important;}
.crm-agenda-kpis{display:none!important;}
.crm-agenda-toolbar{display:grid!important;grid-template-columns:auto 34px 34px auto minmax(240px,1fr) 138px 108px auto auto;align-items:center!important;gap:8px!important;background:#fff!important;border:1px solid #dce4ee!important;border-radius:11px!important;padding:10px!important;margin:0 0 10px!important;box-shadow:none!important;}
.crm-agenda-toolbar>button,.crm-agenda-toolbar>select{height:34px!important;border:1px solid #d9e2ec!important;background:#fff!important;color:#0B1D3A!important;border-radius:7px!important;padding:0 10px!important;font:700 10px Raleway,Arial,sans-serif!important;box-shadow:none!important;}
.crm-agenda-toolbar>button.icon-only{width:34px!important;padding:0!important;font-size:17px!important;}
.crm-agenda-period{min-width:145px!important;color:#0B1D3A!important;font-size:10px!important;font-weight:800!important;white-space:nowrap!important;text-transform:none!important;}
.crm-agenda-search{height:34px!important;min-width:0!important;display:flex!important;align-items:center!important;background:#fff!important;border:1px solid #d9e2ec!important;border-radius:7px!important;padding:0 10px!important;}
.crm-agenda-search input{width:100%!important;height:100%!important;border:0!important;outline:0!important;background:#fff!important;color:#0B1D3A!important;padding:0!important;font:10px Montserrat,Arial,sans-serif!important;box-shadow:none!important;}
.crm-agenda-toolbar select{min-width:0!important;width:100%!important;}
.crm-agenda-view-toggle{height:34px;display:flex;align-items:center;border:1px solid #d9e2ec;border-radius:7px;background:#f8fafc;padding:2px;white-space:nowrap;}
.crm-agenda-view-toggle button{height:28px;border:0;background:transparent;color:#0B1D3A;border-radius:5px;padding:0 9px;font:800 9px Raleway,Arial,sans-serif;cursor:pointer;}
.crm-agenda-view-toggle button.active{background:#0B1D3A;color:#fff;box-shadow:0 1px 2px rgba(11,29,58,.15);}
.crm-agenda-clear{padding-inline:9px!important;}
.crm-agenda-calendar{background:#fff!important;border:1px solid #dce4ee!important;border-radius:11px!important;overflow:hidden!important;box-shadow:none!important;}
.crm-agenda-week{display:grid!important;grid-template-columns:54px repeat(7,minmax(0,1fr))!important;grid-template-rows:36px repeat(11,50px)!important;min-height:586px!important;height:auto!important;}
.crm-agenda-week-corner{background:#fff;border-right:1px solid #e5ebf2;border-bottom:1px solid #e5ebf2;}
.crm-agenda-week-head{display:flex;align-items:center;justify-content:center;background:#fff;border-right:1px solid #e5ebf2;border-bottom:1px solid #e5ebf2;color:#5f6d7c;font-size:8px;font-weight:800;}
.crm-agenda-week-head:last-of-type{border-right:0;}
.crm-agenda-week-head.today span{color:#0B1D3A;font-weight:900;}
.crm-agenda-time-label{display:flex;align-items:flex-start;justify-content:flex-start;padding:7px 0 0 8px;border-right:1px solid #e5ebf2;border-bottom:1px solid #e5ebf2;color:#6f7e8e;background:#fff;font:8px/1 Montserrat,Arial,sans-serif;box-sizing:border-box;}
.crm-agenda-time-cell{position:relative;min-width:0;border-right:1px solid #e5ebf2;border-bottom:1px solid #e5ebf2;background:#fff;padding:3px;box-sizing:border-box;overflow:visible;}
.crm-agenda-time-cell:nth-child(8n){border-right:0;}
.crm-agenda-time-cell.today{background:#fcfdff;}
.crm-agenda-week-event{width:100%;min-height:30px;border:1px solid #c9d9ef;border-radius:6px;background:#edf4fd;color:#17335a;text-align:left;padding:4px 6px;display:grid;gap:1px;cursor:pointer;overflow:hidden;box-sizing:border-box;}
.crm-agenda-week-event strong{font:700 8px/1.2 Raleway,Arial,sans-serif;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.crm-agenda-week-event small{font:7px/1.2 Montserrat,Arial,sans-serif;color:#667b98;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.crm-agenda-week-event.confirmed{background:#edf7f2;border-color:#cfe7da;color:#225e43}.crm-agenda-week-event.pending{background:#fff8e8;border-color:#eddcac;color:#7d5916}.crm-agenda-week-event.done{background:#edf4fd;border-color:#c9d9ef}.crm-agenda-week-event.cancelled{background:#fff0f1;border-color:#efcdd1;color:#87333b}
.crm-agenda-day-view>header{height:36px!important;padding:0 12px!important;display:flex!important;align-items:center!important;border-bottom:1px solid #e5ebf2!important;background:#fff!important;color:#5f6d7c!important;font-size:9px!important;font-weight:800!important;text-transform:capitalize!important;}
.crm-agenda-day-time-grid{display:grid;grid-template-columns:54px minmax(0,1fr);grid-template-rows:repeat(11,50px);}
.crm-agenda-day-time-cell{border-bottom:1px solid #e5ebf2;background:#fff;padding:3px;}
.crm-agenda-month .crm-agenda-weekdays{background:#fff!important}.crm-agenda-month-grid{min-height:550px}.crm-agenda-day{min-height:110px!important;background:#fff!important;}
.crm-agenda-year{gap:10px!important}.crm-agenda-year-card{box-shadow:none!important;border-color:#dce4ee!important;}
@media(max-width:1180px){.crm-agenda-toolbar{grid-template-columns:auto 34px 34px auto minmax(180px,1fr) 120px 100px!important}.crm-agenda-view-toggle{grid-column:1/-1;justify-self:end}.crm-agenda-clear{grid-column:1/-1;justify-self:end}}
@media(max-width:760px){.crm-agenda-workspace{padding:10px!important}.crm-agenda-toolbar{display:flex!important;flex-wrap:wrap!important}.crm-agenda-search{flex:1 1 100%!important}.crm-agenda-view-toggle{width:100%;justify-content:space-between}.crm-agenda-view-toggle button{flex:1}.crm-agenda-calendar{overflow:auto!important}.crm-agenda-week{min-width:980px!important}.crm-agenda-month{min-width:760px}.crm-agenda-period{min-width:120px!important}.crm-agenda-toolbar>select{width:auto!important;flex:1 1 130px}}
'''


def apply_crm_agenda_calendar_layout_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    week_pattern = r"  function crmAgendaWeekCalendar\(events\)\{.*?\n  function crmAgendaDayCalendar\(events\)\{"
    if not re.search(week_pattern, app, flags=re.S):
        raise RuntimeError("crmAgendaWeekCalendar não encontrado")
    app = re.sub(week_pattern, WEEK_FUNCTION + "\n" + DAY_FUNCTION.rstrip() + "\n\n  function __crmAgendaYearAnchor__(){", app, count=1, flags=re.S)
    app = app.replace("\n\n  function __crmAgendaYearAnchor__(){\n    const year=state.crmAgendaCurrentDate.getFullYear();", "\n\n  function crmAgendaYearCalendar(events){\n    const year=state.crmAgendaCurrentDate.getFullYear();", 1)

    page_pattern = r"  function crmAgendaPage\(\)\{.*?\n  function crmAgendaPJContacts\(\)\{"
    if not re.search(page_pattern, app, flags=re.S):
        raise RuntimeError("crmAgendaPage não encontrado")
    app = re.sub(page_pattern, PAGE_FUNCTION + "\n\n  function crmAgendaPJContacts(){", app, count=1, flags=re.S)

    click_anchor = "      if(action==='crm-agenda-next'){ crmAgendaShift(1); return; }"
    view_line = "      if(action==='crm-agenda-view-mode'){ state.crmAgendaViewMode=target.dataset.view||'semana'; crmAgendaRerender(); return; }"
    if view_line not in app:
        if click_anchor not in app:
            raise RuntimeError("âncora de navegação da Agenda não encontrada")
        app = app.replace(click_anchor, click_anchor + "\n" + view_line, 1)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM AGENDA CALENDAR LAYOUT FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Layout do calendário da Agenda ajustado à referência semanal fornecida.")
    return 1


if __name__ == "__main__":
    apply_crm_agenda_calendar_layout_fix()
