from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app.js'
CSS = ROOT / 'assets' / 'valtren-brand.css'

MARKER = '/* VALTREN CRM INTEGRATED */'

CRM_FUNCTION = r'''  function crmDashboardPage(){
    return `<div class="crm-app-shell">
      <aside class="crm-sidebar">
        <a class="crm-brand" href="#/crm/dashboard" aria-label="Valtren CRM Integrado">
          <img src="assets/valtren-mark.svg" alt="Valtren Solutions">
          <span><strong>VALTREN</strong><small>CRM Integrado</small></span>
        </a>
        <nav class="crm-nav" aria-label="Módulos do CRM">
          <a class="active" href="#/crm/dashboard">${icon('layers',18)}<span>Dashboard</span></a>
        </nav>
      </aside>
      <main class="crm-main">
        <header class="crm-topbar">
          <div><span>CRM Integrado</span><h1>Dashboard</h1></div>
        </header>
        <section class="crm-workspace" aria-label="Dashboard">
          <div class="crm-empty-module">
            <h2>Dashboard</h2>
            <p>Estrutura inicial criada. Os componentes deste módulo serão adicionados conforme sua definição.</p>
          </div>
        </section>
      </main>
    </div>`;
  }
'''

CSS_PATCH = r'''
/* VALTREN CRM INTEGRATED */
.crm-app-shell{min-height:100vh;background:#F7F8FA;color:#0B1D3A;display:grid;grid-template-columns:250px minmax(0,1fr);font-family:Raleway,Montserrat,Arial,sans-serif}.crm-sidebar{background:#0B1D3A;color:#fff;padding:22px 16px;display:flex;flex-direction:column;gap:28px;border-right:1px solid rgba(212,175,55,.22)}.crm-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#fff;padding:4px 8px}.crm-brand img{width:34px;height:34px;object-fit:contain}.crm-brand span{display:flex;flex-direction:column;line-height:1.05}.crm-brand strong{font-size:15px;letter-spacing:.12em}.crm-brand small{font-family:Montserrat,Arial,sans-serif;color:#D4AF37;font-size:10px;margin-top:5px;letter-spacing:.04em}.crm-nav{display:flex;flex-direction:column;gap:6px}.crm-nav a{display:flex;align-items:center;gap:11px;min-height:44px;padding:0 12px;border-radius:8px;color:rgba(255,255,255,.78);text-decoration:none;font-size:14px;font-weight:600}.crm-nav a.active{background:rgba(212,175,55,.13);color:#fff;border:1px solid rgba(212,175,55,.24)}.crm-nav a.active svg{color:#D4AF37}.crm-main{min-width:0;display:flex;flex-direction:column}.crm-topbar{min-height:82px;background:#fff;border-bottom:1px solid rgba(11,29,58,.1);display:flex;align-items:center;padding:16px 30px}.crm-topbar span{display:block;font-family:Montserrat,Arial,sans-serif;color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:.12em;margin-bottom:5px}.crm-topbar h1{font-size:25px;line-height:1.1;margin:0;color:#0B1D3A}.crm-workspace{padding:30px;min-width:0}.crm-empty-module{min-height:430px;background:#fff;border:1px solid rgba(11,29,58,.1);border-radius:12px;padding:28px}.crm-empty-module h2{margin:0 0 9px;font-size:22px;color:#0B1D3A}.crm-empty-module p{margin:0;max-width:650px;color:#64748B;font-family:Montserrat,Arial,sans-serif;font-size:14px;line-height:1.65}@media(max-width:760px){.crm-app-shell{grid-template-columns:1fr}.crm-sidebar{padding:14px;gap:14px}.crm-brand img{width:30px;height:30px}.crm-nav{flex-direction:row}.crm-nav a{flex:0 0 auto}.crm-topbar{padding:15px 18px}.crm-workspace{padding:18px}.crm-empty-module{min-height:300px;padding:20px}}
'''


def apply_crm_dashboard() -> int:
    app = APP.read_text(encoding='utf-8')
    if 'function crmDashboardPage()' not in app:
        anchor = '  function contactPage(query)'
        if anchor not in app:
            raise RuntimeError('CRM function anchor not found')
        app = app.replace(anchor, CRM_FUNCTION + '\n' + anchor, 1)

    route_line = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage();\n"
    if "path === '/crm/dashboard'" not in app:
        anchor = "    else if (path === '/contato') app.innerHTML = contactPage(query);"
        count = app.count(anchor)
        if count < 2:
            raise RuntimeError(f'Expected two route anchors, found {count}')
        app = app.replace(anchor, route_line + anchor)

    APP.write_text(app, encoding='utf-8')

    css = CSS.read_text(encoding='utf-8')
    css = re.sub(r"\n?/\* VALTREN CRM INTEGRATED \*/.*\Z", '', css, flags=re.S)
    CSS.write_text(css.rstrip() + '\n\n' + CSS_PATCH.strip() + '\n', encoding='utf-8')
    print('Módulo CRM Dashboard aplicado.')
    return 1


if __name__ == '__main__':
    apply_crm_dashboard()
