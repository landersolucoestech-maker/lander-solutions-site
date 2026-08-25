from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app.js'
CSS = ROOT / 'assets' / 'valtren-brand.css'
CSS_VERSION = '20260824-crm-global-header-v1'
JS_START = '  // VALTREN CRM GLOBAL HEADER START\n'
JS_END = '  // VALTREN CRM GLOBAL HEADER END\n'
CSS_MARKER = '/* VALTREN CRM GLOBAL HEADER */'

HELPERS = r'''  // VALTREN CRM GLOBAL HEADER START
  function crmHeaderActions(){
    const userName = state.crmUserName || 'Administrador';
    const initials = state.crmUserInitials || 'AD';
    const bell = `<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>`;
    return `<div class="crm-header-actions">
      <button class="crm-header-create crm-header-create-contact" type="button" data-action="crm-rel-create" data-kind="contacts">${icon('plus',15)}<span>Novo Contato</span></button>
      <button class="crm-header-create crm-header-create-lead" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>
      <div class="crm-header-menu crm-header-notifications">
        <button class="crm-header-icon-button" type="button" data-action="crm-header-notifications" aria-label="Notificações" aria-haspopup="true" aria-expanded="false">${bell}<span class="crm-header-notification-dot" aria-label="3 notificações não lidas">3</span></button>
        <div class="crm-header-dropdown crm-header-notification-dropdown" data-crm-header-dropdown="notifications" hidden>
          <div class="crm-header-dropdown-title"><strong>Notificações</strong><span>3 não lidas</span></div>
          <div class="crm-header-notification-list">
            <button type="button" class="unread" data-action="crm-header-menu-item"><i></i><span><strong>Novo lead cadastrado</strong><small>Há 5 min</small></span></button>
            <button type="button" class="unread" data-action="crm-header-menu-item"><i></i><span><strong>Contato atualizado</strong><small>Há 18 min</small></span></button>
            <button type="button" class="unread" data-action="crm-header-menu-item"><i></i><span><strong>Nova atividade registrada</strong><small>Há 1 h</small></span></button>
            <button type="button" data-crm-notification-extra hidden data-action="crm-header-menu-item"><i></i><span><strong>Importação concluída</strong><small>Hoje</small></span></button>
            <button type="button" data-crm-notification-extra hidden data-action="crm-header-menu-item"><i></i><span><strong>Registro revisado</strong><small>Ontem</small></span></button>
          </div>
          <button class="crm-header-view-all" type="button" data-action="crm-header-show-all-notifications">Ver todas as notificações</button>
        </div>
      </div>
      <div class="crm-header-menu crm-header-user">
        <button class="crm-header-user-button" type="button" data-action="crm-header-user-menu" aria-haspopup="true" aria-expanded="false">
          <span class="crm-header-avatar">${esc(initials)}</span>
          <span class="crm-header-user-copy"><strong>${esc(userName)}</strong><small>Usuário logado</small></span>
          <span class="crm-header-caret" aria-hidden="true">⌄</span>
        </button>
        <div class="crm-header-dropdown crm-header-user-dropdown" data-crm-header-dropdown="user" hidden>
          <button type="button" data-action="crm-header-account-item" data-account-item="profile">Perfil</button>
          <button type="button" data-action="crm-header-account-item" data-account-item="settings">Configurações</button>
          <div class="crm-header-dropdown-separator"></div>
          <button type="button" class="danger" data-action="crm-header-account-item" data-account-item="logout">Logout</button>
        </div>
      </div>
    </div>`;
  }

  function crmHeaderCloseMenus(except=''){
    document.querySelectorAll('[data-crm-header-dropdown]').forEach((menu) => {
      if (menu.dataset.crmHeaderDropdown !== except) menu.hidden = true;
    });
    document.querySelectorAll('[data-action="crm-header-notifications"],[data-action="crm-header-user-menu"]').forEach((button) => {
      const type = button.dataset.action === 'crm-header-notifications' ? 'notifications' : 'user';
      if (type !== except) button.setAttribute('aria-expanded','false');
    });
  }

  if (!window.__valtrenCrmHeaderBound) {
    window.__valtrenCrmHeaderBound = true;
    document.addEventListener('click', (event) => {
      const actionTarget = event.target.closest('[data-action]');
      const insideHeaderMenu = event.target.closest('.crm-header-menu');
      if (!actionTarget) {
        if (!insideHeaderMenu) crmHeaderCloseMenus();
        return;
      }
      const action = actionTarget.dataset.action;
      if (action === 'crm-header-notifications' || action === 'crm-header-user-menu') {
        event.stopPropagation();
        const type = action === 'crm-header-notifications' ? 'notifications' : 'user';
        const dropdown = document.querySelector(`[data-crm-header-dropdown="${type}"]`);
        const willOpen = !!dropdown?.hidden;
        crmHeaderCloseMenus(type);
        if (dropdown) dropdown.hidden = !willOpen;
        actionTarget.setAttribute('aria-expanded', String(willOpen));
        return;
      }
      if (action === 'crm-header-show-all-notifications') {
        event.stopPropagation();
        document.querySelectorAll('[data-crm-notification-extra]').forEach((item) => { item.hidden = false; });
        actionTarget.hidden = true;
        return;
      }
      if (action === 'crm-header-menu-item' || action === 'crm-header-account-item') {
        crmHeaderCloseMenus();
      }
    });
  }
  // VALTREN CRM GLOBAL HEADER END
'''

CSS_PATCH = r'''
/* VALTREN CRM GLOBAL HEADER */
.crm-app-shell .crm-topbar{
  min-height:92px!important;
  padding:14px 26px 14px 30px!important;
  gap:24px!important;
  overflow:visible!important;
  position:relative!important;
  z-index:80!important;
}
.crm-app-shell .crm-topbar>div:first-child{min-width:0!important;}
.crm-app-shell .crm-topbar>div:first-child>span{display:none!important;}
.crm-app-shell .crm-topbar h1{margin:0!important;color:#FFFFFF!important;}
.crm-app-shell .crm-topbar p{margin:6px 0 0!important;color:rgba(255,255,255,.76)!important;}
.crm-header-actions{margin-left:auto;display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:0;}
.crm-header-create{height:38px;border-radius:8px;padding:0 12px;border:1px solid rgba(212,175,55,.52);display:inline-flex;align-items:center;justify-content:center;gap:7px;font:700 10px/1 Raleway,Arial,sans-serif;letter-spacing:.01em;cursor:pointer;white-space:nowrap;transition:background .16s ease,border-color .16s ease,color .16s ease;}
.crm-header-create-contact{background:#D4AF37;color:#0B1D3A;border-color:#D4AF37;}
.crm-header-create-contact:hover{background:#E0BE4B;border-color:#E0BE4B;}
.crm-header-create-lead{background:rgba(255,255,255,.06);color:#FFFFFF;}
.crm-header-create-lead:hover{background:rgba(212,175,55,.12);border-color:#D4AF37;}
.crm-header-menu{position:relative;flex:0 0 auto;}
.crm-header-icon-button{width:38px;height:38px;border-radius:9px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:#FFFFFF;display:grid;place-items:center;cursor:pointer;position:relative;}
.crm-header-icon-button:hover{background:rgba(255,255,255,.11);}
.crm-header-notification-dot{position:absolute;top:-5px;right:-5px;min-width:17px;height:17px;border-radius:999px;background:#D4AF37;color:#0B1D3A;border:2px solid #0B1D3A;display:grid;place-items:center;padding:0 3px;font:800 8px/1 Montserrat,Arial,sans-serif;}
.crm-header-user-button{height:42px;max-width:220px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);border-radius:10px;padding:4px 9px 4px 5px;color:#FFFFFF;display:flex;align-items:center;gap:9px;cursor:pointer;text-align:left;}
.crm-header-user-button:hover{background:rgba(255,255,255,.11);}
.crm-header-avatar{width:32px;height:32px;border-radius:8px;background:#D4AF37;color:#0B1D3A;display:grid;place-items:center;font:800 10px/1 Raleway,Arial,sans-serif;letter-spacing:.03em;flex:0 0 auto;}
.crm-header-user-copy{display:flex;flex-direction:column;min-width:0;line-height:1.1;}
.crm-header-user-copy strong{font-size:10px;color:#FFFFFF;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:110px;}
.crm-header-user-copy small{font:8px/1.2 Montserrat,Arial,sans-serif;color:rgba(255,255,255,.58);margin-top:3px;}
.crm-header-caret{color:rgba(255,255,255,.68);font-size:13px;margin-left:2px;}
.crm-header-dropdown{position:absolute;right:0;top:calc(100% + 9px);z-index:500;min-width:230px;background:#FFFFFF;color:#0B1D3A;border:1px solid rgba(11,29,58,.12);border-radius:11px;box-shadow:0 18px 46px rgba(6,19,38,.22);overflow:hidden;}
.crm-header-dropdown[hidden]{display:none!important;}
.crm-header-dropdown-title{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 13px;border-bottom:1px solid rgba(11,29,58,.08);}
.crm-header-dropdown-title strong{font-size:11px;color:#0B1D3A;}
.crm-header-dropdown-title span{font:700 8px/1 Montserrat,Arial,sans-serif;color:#9A7319;background:#FFF7DF;border-radius:999px;padding:5px 7px;}
.crm-header-notification-dropdown{width:320px;}
.crm-header-notification-list{display:grid;max-height:330px;overflow:auto;}
.crm-header-notification-list button{width:100%;border:0;background:#FFFFFF;display:grid;grid-template-columns:8px 1fr;gap:9px;text-align:left;padding:11px 13px;cursor:pointer;border-bottom:1px solid rgba(11,29,58,.06);}
.crm-header-notification-list button:hover{background:#F8FAFC;}
.crm-header-notification-list button>i{width:6px;height:6px;border-radius:999px;background:#CBD5E1;margin-top:5px;}
.crm-header-notification-list button.unread>i{background:#D4AF37;}
.crm-header-notification-list button>span{display:flex;flex-direction:column;min-width:0;}
.crm-header-notification-list strong{font-size:10px;color:#0B1D3A;font-weight:700;}
.crm-header-notification-list small{font:8px/1.3 Montserrat,Arial,sans-serif;color:#8390A0;margin-top:4px;}
.crm-header-view-all{width:100%;height:36px;border:0;background:#FAFBFC;color:#8A6917;font-size:9px;font-weight:800;cursor:pointer;}
.crm-header-view-all:hover{background:#F4F6F8;}
.crm-header-user-dropdown{min-width:190px;padding:5px;}
.crm-header-user-dropdown button{width:100%;height:34px;border:0;background:transparent;border-radius:7px;text-align:left;padding:0 10px;color:#334155;font-size:10px;font-weight:700;cursor:pointer;}
.crm-header-user-dropdown button:hover{background:#F4F6F8;}
.crm-header-user-dropdown button.danger{color:#A43E3E;}
.crm-header-dropdown-separator{height:1px;background:rgba(11,29,58,.08);margin:4px 5px;}
.crm-rel-module-header>.crm-rel-primary[data-action="crm-rel-create"]{display:none!important;}
@media(max-width:1180px){
  .crm-header-user-copy{display:none;}
  .crm-header-user-button{padding-right:6px;gap:5px;}
  .crm-header-caret{margin-left:0;}
}
@media(max-width:980px){
  .crm-app-shell .crm-topbar{padding:13px 20px!important;gap:16px!important;}
  .crm-header-create{padding:0 9px;}
}
@media(max-width:760px){
  .crm-app-shell .crm-topbar{align-items:flex-start!important;flex-direction:column!important;padding:14px 16px!important;}
  .crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:wrap;margin-left:0;}
  .crm-header-create{flex:1 1 140px;}
  .crm-header-notification-dropdown{right:auto;left:0;width:min(320px,calc(100vw - 32px));}
  .crm-header-user-dropdown{right:0;}
}
'''

def apply_crm_global_header() -> int:
    app = APP.read_text(encoding='utf-8')
    app = re.sub(r"  // VALTREN CRM GLOBAL HEADER START\n.*?  // VALTREN CRM GLOBAL HEADER END\n", "", app, flags=re.S)
    anchor = '  function crmDashboardPage(query){\n'
    if anchor not in app:
        raise RuntimeError('crmDashboardPage anchor not found')
    app = app.replace(anchor, HELPERS + '\n' + anchor, 1)

    old_dashboard = '''        <header class="crm-topbar">\n          <div><span>CRM Integrado</span><h1>Dashboard</h1><p>Visão executiva consolidada da Valtren Solutions</p></div>\n          <span class="crm-demo-badge">Protótipo · dados ilustrativos</span>\n        </header>'''
    new_dashboard = '''        <header class="crm-topbar">\n          <div><h1>Dashboard</h1><p>Visão executiva consolidada da Valtren Solutions</p></div>\n          ${crmHeaderActions()}\n        </header>'''
    if old_dashboard not in app:
        raise RuntimeError('Dashboard header block not found')
    app = app.replace(old_dashboard, new_dashboard, 1)

    old_crm = '''        <header class="crm-topbar">\n          <div><span>CRM Integrado</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n        </header>'''
    new_crm = '''        <header class="crm-topbar">\n          <div><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n          ${crmHeaderActions()}\n        </header>'''
    if old_crm not in app:
        raise RuntimeError('CRM header block not found')
    app = app.replace(old_crm, new_crm, 1)

    app, count = re.subn(r'\n\s*<button class="crm-rel-primary" type="button" data-action="crm-rel-create" data-kind="\$\{tab\}">\$\{icon\(\'plus\',16\)\} \$\{isContacts \? \'Novo Contato\' : \'Novo Lead\'\}</button>', '', app, count=1)
    if count != 1:
        raise RuntimeError(f'Old module create button not found: {count}')
    APP.write_text(app, encoding='utf-8')

    css = CSS.read_text(encoding='utf-8')
    css = re.sub(r'\n?/\* VALTREN CRM GLOBAL HEADER \*/.*\Z', '', css, flags=re.S)
    CSS.write_text(css.rstrip() + '\n\n' + CSS_PATCH.strip() + '\n', encoding='utf-8')

    for path in ROOT.rglob('*.html'):
        if any(part in {'.git','.bootstrap','node_modules','scripts'} for part in path.relative_to(ROOT).parts):
            continue
        original = path.read_text(encoding='utf-8')
        updated = re.sub(r'valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?', f'valtren-brand.css?v={CSS_VERSION}', original)
        if updated != original:
            path.write_text(updated, encoding='utf-8')

    print('Header global do CRM atualizado com ações, notificações e usuário.')
    return 1

if __name__ == '__main__':
    apply_crm_global_header()
