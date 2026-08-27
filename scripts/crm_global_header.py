from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260827-crm-global-header-v9"
JS_START = "  // VALTREN CRM GLOBAL HEADER START\n"
JS_END = "  // VALTREN CRM GLOBAL HEADER END\n"
DASHBOARD_START = "  // VALTREN CRM DASHBOARD START\n"
CSS_MARKER = "/* VALTREN CRM GLOBAL HEADER */"

HELPERS = r'''  // VALTREN CRM GLOBAL HEADER START
  function crmHeaderNotificationItems(){
    return Array.isArray(state.crmNotifications) ? state.crmNotifications : [];
  }

  function crmHeaderBellIcon(){
    return `<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg>`;
  }

  function crmHeaderNotificationHref(item){
    const href=String(item?.href||'').trim();
    return href.startsWith('#/crm/') ? href : '';
  }

  function crmHeaderNotificationItem(item){
    const read=!!item?.read;
    const href=crmHeaderNotificationHref(item);
    const action=href?`<a href="${esc(href)}" data-action="crm-notification-open" data-id="${esc(item.id||'')}">Abrir</a>`:'';
    return `<article class="crm-notification-item ${read?'read':'unread'}" data-notification-id="${esc(item.id||'')}">
      <div class="crm-notification-copy"><strong>${esc(item.title||'Notificação')}</strong>${item.description?`<p>${esc(item.description)}</p>`:''}${item.timestamp?`<small>${esc(item.timestamp)}</small>`:''}</div>
      <div class="crm-notification-item-actions">${action}<button type="button" data-action="crm-notification-toggle-read" data-id="${esc(item.id||'')}">${read?'Marcar como não lida':'Marcar como lida'}</button></div>
    </article>`;
  }

  function crmHeaderNotifications(){
    const items=crmHeaderNotificationItems();
    const unread=items.filter((item)=>!item?.read).length;
    const body=items.length
      ? `<div class="crm-notification-list">${items.map(crmHeaderNotificationItem).join('')}</div>`
      : `<div class="crm-notification-empty"><strong>Nenhuma notificação</strong><p>Novos avisos locais aparecerão aqui quando houver uma fonte configurada.</p></div>`;
    return `<details class="crm-notification-menu">
      <summary aria-label="Notificações" aria-haspopup="menu" aria-expanded="false"><span class="crm-notification-icon" aria-hidden="true">${crmHeaderBellIcon()}</span>${unread?`<span class="crm-notification-badge" aria-label="${unread} notificação${unread===1?'':'ões'} não lida${unread===1?'':'s'}">${unread>99?'99+':unread}</span>`:''}</summary>
      <div class="crm-notification-popover" role="menu" aria-label="Notificações recentes"><header><strong>Notificações</strong>${unread?`<button type="button" data-action="crm-notification-mark-all-read">Marcar todas como lidas</button>`:''}</header>${body}</div>
    </details>`;
  }

  function crmHeaderCreateAction(context=''){
    if(context==='contacts')return `<button class="crm-header-create crm-header-create-contact" type="button" aria-label="Novo Contato" data-action="crm-full-create" data-kind="contact">${icon('plus',15)}<span>Novo Contato</span></button>`;
    if(context==='leads')return `<button class="crm-header-create crm-header-create-lead" type="button" aria-label="Novo Lead" data-action="crm-full-create" data-kind="lead">${icon('plus',15)}<span>Novo Lead</span></button>`;
    if(context === 'agenda')return `<button class="crm-header-create crm-header-create-agenda" type="button" aria-label="Novo Evento" data-action="crm-agenda-create">${icon('plus',15)}<span>Novo Evento</span></button>`;
    return '';
  }

  function crmHeaderActions(context=''){
    const create=crmHeaderCreateAction(context);
    const navToggle=`<button class="crm-mobile-nav-toggle" type="button" data-action="crm-sidebar-toggle" aria-controls="crm-system-sidebar" aria-expanded="false" aria-label="Abrir navegação">${icon('menu',18)}<span>Menu</span></button>`;
    return `<div class="crm-header-actions">${navToggle}${create}${crmHeaderNotifications()}<details class="crm-account-menu"><summary aria-label="Menu da conta" aria-haspopup="menu" aria-expanded="false"><span class="crm-account-icon" aria-hidden="true">${icon('user',16)}</span><span class="crm-account-copy"><strong>Conta</strong><small>Autenticação desativada</small></span><span class="crm-account-chevron" aria-hidden="true">⌄</span></summary><div class="crm-account-popover"><strong>Sem sessão ativa</strong><p>Este ambiente não possui autenticação ou usuário conectado. Nenhuma identidade é simulada.</p><a href="#/crm/configuracoes">Configurações</a></div></details></div>`;
  }

  function crmHeaderSetExpanded(menu,expanded){
    const summary=menu?.querySelector(':scope>summary');
    if(summary)summary.setAttribute('aria-expanded',expanded?'true':'false');
  }

  function crmHeaderCloseMenus(except=null){
    document.querySelectorAll('.crm-account-menu[open],.crm-notification-menu[open]').forEach((menu)=>{
      if(menu===except)return;
      menu.removeAttribute('open');
      crmHeaderSetExpanded(menu,false);
    });
  }

  function crmHeaderRefreshNotifications(){
    if(typeof renderCurrentWithoutReset==='function')renderCurrentWithoutReset();
  }

  if (!window.__valtrenCrmHeaderMenusBound) {
    window.__valtrenCrmHeaderMenusBound = true;
    document.addEventListener('keydown',(event)=>{
      if(event.key==='Escape')crmHeaderCloseMenus();
    });
    document.addEventListener('click',(event)=>{
      const notificationAction=event.target.closest?.('[data-action^="crm-notification-"]');
      if(notificationAction){
        const action=notificationAction.dataset.action;
        const items=crmHeaderNotificationItems();
        if(action==='crm-notification-toggle-read'){
          const item=items.find((row)=>String(row.id)===String(notificationAction.dataset.id));
          if(item)item.read=!item.read;
          crmHeaderRefreshNotifications();
          return;
        }
        if(action==='crm-notification-mark-all-read'){
          items.forEach((item)=>{item.read=true;});
          crmHeaderRefreshNotifications();
          return;
        }
        if(action==='crm-notification-open'){
          const item=items.find((row)=>String(row.id)===String(notificationAction.dataset.id));
          if(item)item.read=true;
          crmHeaderCloseMenus();
          return;
        }
      }
      const summary=event.target.closest?.('.crm-account-menu>summary,.crm-notification-menu>summary');
      if(summary){
        const menu=summary.parentElement;
        setTimeout(()=>{
          const expanded=!!menu?.open;
          crmHeaderSetExpanded(menu,expanded);
          if(expanded)crmHeaderCloseMenus(menu);
        },0);
        return;
      }
      if(!event.target.closest?.('.crm-account-menu,.crm-notification-menu'))crmHeaderCloseMenus();
    });
  }
  // VALTREN CRM GLOBAL HEADER END
'''

CSS_PATCH = r'''
/* VALTREN CRM GLOBAL HEADER */
.crm-app-shell .crm-topbar{position:relative;z-index:80;overflow:visible}
.crm-header-actions{margin-left:auto;display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:0;flex:0 0 auto}
.crm-header-create,.crm-mobile-nav-toggle{min-height:40px;border-radius:8px;padding:0 12px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font:inherit;font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap}
.crm-header-create{border:1px solid #D4AF37;background:#D4AF37;color:#0B1D3A}
.crm-mobile-nav-toggle{display:none;border:1px solid rgba(255,255,255,.24);background:transparent;color:#fff}
.crm-header-create:focus-visible,.crm-mobile-nav-toggle:focus-visible,.crm-notification-menu>summary:focus-visible,.crm-notification-popover button:focus-visible,.crm-notification-popover a:focus-visible,.crm-account-menu>summary:focus-visible,.crm-account-popover a:focus-visible{outline:2px solid #D4AF37;outline-offset:2px}
.crm-notification-menu,.crm-account-menu{position:relative;min-width:0}
.crm-app-shell .crm-main .crm-topbar .crm-header-actions .crm-notification-menu{background:transparent!important;background-color:transparent!important;color:#FFFFFF!important;color-scheme:dark!important;border-color:transparent!important;box-shadow:none!important}
.crm-notification-menu>summary,.crm-account-menu>summary{list-style:none;min-height:44px;display:flex;align-items:center;justify-content:center;gap:10px;border:1px solid rgba(212,175,55,.62);border-radius:12px;background:transparent;color:#FFFFFF;cursor:pointer;box-sizing:border-box;box-shadow:none;transition:background .16s ease,border-color .16s ease}
.crm-notification-menu>summary{position:relative;width:44px;padding:5px}
.crm-account-menu>summary{padding:5px 10px}
.crm-notification-menu>summary:hover,.crm-notification-menu[open]>summary,.crm-account-menu>summary:hover,.crm-account-menu[open]>summary{background:rgba(212,175,55,.10);border-color:#D4AF37}
.crm-notification-menu>summary::-webkit-details-marker,.crm-account-menu>summary::-webkit-details-marker{display:none}
.crm-notification-icon,.crm-account-icon{display:grid;place-items:center;color:#D4AF37}
.crm-notification-icon{width:30px;height:30px}
.crm-account-icon{width:30px;height:30px;flex:0 0 30px;border-radius:50%;background:rgba(212,175,55,.12);border:1px solid rgba(212,175,55,.72)}
.crm-notification-badge{position:absolute;top:2px;right:2px;min-width:17px;height:17px;padding:0 4px;border-radius:999px;background:#D4AF37;color:#0B1D3A;border:2px solid #07172F;display:inline-flex;align-items:center;justify-content:center;font:800 9px/1 Montserrat,Arial,sans-serif}
.crm-account-copy{display:flex;min-width:0;flex-direction:column;align-items:flex-start;line-height:1.15}.crm-account-copy strong{font-size:13px;color:#FFFFFF}.crm-account-copy small{font-size:11px;color:#E8CC73;margin-top:3px;white-space:nowrap}
.crm-account-chevron{color:#D4AF37;flex:0 0 auto;transition:transform .18s ease}.crm-account-menu[open] .crm-account-chevron{transform:rotate(180deg)}
.crm-notification-popover,.crm-account-popover{position:absolute;right:0;top:calc(100% + 8px);box-sizing:border-box;border:1px solid rgba(11,29,58,.12);border-radius:12px;background:#fff;color:#0B1D3A;color-scheme:light;box-shadow:0 16px 40px rgba(11,29,58,.16);z-index:800}
.crm-notification-popover{width:min(380px,calc(100vw - 28px));padding:0;overflow:hidden}
.crm-notification-popover>header{min-height:48px;padding:11px 13px;display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px solid rgba(11,29,58,.09);background:#fff}
.crm-notification-popover>header>strong{color:#0B1D3A;font-size:13px}.crm-notification-popover>header>button{min-height:32px;padding:6px 8px;border:0;background:transparent;color:#475569;font-size:11px;font-weight:700;cursor:pointer}
.crm-notification-list{max-height:min(440px,65vh);overflow:auto;background:#fff}
.crm-notification-item{display:grid;gap:9px;padding:12px 13px;border-bottom:1px solid rgba(11,29,58,.07);background:#fff}.crm-notification-item.unread{background:#FFFDF6}.crm-notification-item:last-child{border-bottom:0}
.crm-notification-copy{min-width:0}.crm-notification-copy strong{display:block;color:#0B1D3A;font-size:12px;line-height:1.35}.crm-notification-copy p{margin:4px 0 0;color:#526174;font-size:11px;font-weight:500;line-height:1.45}.crm-notification-copy small{display:block;margin-top:5px;color:#64748B;font-size:10px;font-weight:600;line-height:1.3}
.crm-notification-item-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.crm-notification-item-actions a,.crm-notification-item-actions button{min-height:30px;padding:5px 8px;border-radius:7px;font-size:10px;font-weight:700;text-decoration:none}.crm-notification-item-actions a{display:inline-flex;align-items:center;background:#D4AF37;color:#0B1D3A}.crm-notification-item-actions button{border:1px solid rgba(11,29,58,.14);background:#fff;color:#475569;cursor:pointer}
.crm-notification-empty{padding:24px 18px;text-align:center;background:#fff}.crm-notification-empty strong{display:block;color:#0B1D3A;font-size:13px}.crm-notification-empty p{margin:6px auto 0;max-width:290px;color:#526174;font-size:11px;font-weight:500;line-height:1.5}
.crm-account-popover{width:min(320px,calc(100vw - 28px));padding:16px}
.crm-account-popover>strong{display:block;color:#0B1D3A;font-size:13px;line-height:1.3}
.crm-app-shell .crm-topbar .crm-account-menu .crm-account-popover p{font-size:12px;line-height:1.5;color:#526174!important;font-weight:500;margin:7px 0 12px}.crm-account-popover a{display:inline-flex;min-height:36px;align-items:center;color:#0B1D3A;font-size:12px;font-weight:700;text-decoration:none}
@media(max-width:980px){.crm-account-copy{display:none}.crm-account-menu>summary{gap:6px;padding:5px 8px}.crm-account-popover{max-width:calc(100vw - 24px)}}
@media(max-width:760px){.crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:nowrap;margin-left:0}.crm-mobile-nav-toggle{display:inline-flex}.crm-account-menu{margin-left:auto}.crm-notification-popover{position:fixed;left:12px;right:12px;top:86px;width:auto;max-width:none;max-height:calc(100dvh - 98px)}.crm-notification-list{max-height:calc(100dvh - 160px)}.crm-account-popover{position:fixed;right:12px;top:auto;max-width:calc(100vw - 24px)}}
@media(max-width:480px){.crm-header-create span,.crm-mobile-nav-toggle span{display:none}.crm-header-create,.crm-mobile-nav-toggle{width:44px;padding:0}.crm-header-actions{gap:6px}}
'''


def _assert_js_syntax(source: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
            raise RuntimeError(f"Header global produziu bundle inválido: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def _materialize_helpers(app: str) -> str:
    start_count = app.count(JS_START)
    end_count = app.count(JS_END)
    desired = HELPERS.rstrip() + "\n"
    if start_count == 1 and end_count == 1:
        start = app.index(JS_START)
        end = app.index(JS_END, start) + len(JS_END)
        current = app[start:end]
        return app if current == desired else app[:start] + desired + app[end:]
    if start_count or end_count:
        raise RuntimeError(f"Marcadores do header global divergentes: {start_count}/{end_count}")
    if app.count(DASHBOARD_START) != 1:
        raise RuntimeError(f"Âncora canônica do Dashboard divergente: {app.count(DASHBOARD_START)}")
    at = app.index(DASHBOARD_START)
    return app[:at] + desired + "\n" + app[at:]


def _materialize_crm_header(app: str) -> str:
    old_crm = '''        <header class="crm-topbar">\n          <div><span>CRM Integrado</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n        </header>'''
    new_crm = '''        <header class="crm-topbar">\n          <div><span>Sistema Interno</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n          ${crmHeaderActions(tab)}\n        </header>'''
    old_count = app.count(old_crm)
    new_count = app.count(new_crm)
    if old_count == 1 and new_count == 0:
        return app.replace(old_crm, new_crm, 1)
    if old_count == 0 and new_count == 1:
        return app
    raise RuntimeError(f"Header CRM divergente: legado={old_count}, canônico={new_count}")


def _remove_local_create_button(app: str) -> str:
    pattern = r'\n\s*<button class="crm-rel-primary" type="button" data-action="crm-rel-create" data-kind="\$\{tab\}">\$\{icon\(\'plus\',16\)\} \$\{isContacts \? \'Novo Contato\' : \'Novo Lead\'\}</button>'
    app, count = re.subn(pattern, "", app, count=1)
    if count == 1:
        return app
    if 'class="crm-rel-primary" type="button" data-action="crm-rel-create"' not in app:
        return app
    raise RuntimeError(f"Botão local de criação do CRM divergente: {count}")


def _replace_css_block(css: str) -> str:
    desired = CSS_PATCH.strip()
    marker_at = css.find(CSS_MARKER)
    if marker_at < 0:
        return css.rstrip() + "\n\n" + desired + "\n"
    next_marker = css.find("\n/* ", marker_at + len(CSS_MARKER))
    end = len(css) if next_marker < 0 else next_marker + 1
    current = css[marker_at:end].strip()
    if current == desired:
        return css
    prefix = css[:marker_at].rstrip()
    suffix = css[end:].lstrip("\n")
    return prefix + "\n\n" + desired + "\n" + ("\n" + suffix if suffix else "")


def apply_crm_global_header() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    app = _materialize_helpers(app)

    if app.count("${crmHeaderActions('dashboard')}") != 1:
        raise RuntimeError("Dashboard não chegou com header canônico do próprio owner")

    app = _materialize_crm_header(app)
    app = _remove_local_create_button(app)
    required = [
        'aria-label="Notificações"',
        'function crmHeaderNotifications()',
        'function crmHeaderBellIcon()',
        'data-action="crm-notification-toggle-read"',
        'data-action="crm-notification-mark-all-read"',
        'data-action="crm-full-create" data-kind="contact"',
        'data-action="crm-full-create" data-kind="lead"',
    ]
    missing = [token for token in required if token not in app]
    if missing:
        raise RuntimeError(f"Contrato do Header/Notificações incompleto: {missing}")
    _assert_js_syntax(app)
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css_block(css)
    if updated_css != css:
        CSS.write_text(updated_css, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CSS_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Header compartilhado materializado com ações contextuais, sino de Notificações independente e Account Menu preservado.")
    return 1


if __name__ == "__main__":
    apply_crm_global_header()
