from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260826-sidebar-architecture-v1"
JS_START = "  // VALTREN SIDEBAR ARCHITECTURE START\n"
JS_END = "  // VALTREN SIDEBAR ARCHITECTURE END\n"
CSS_MARKER = "/* VALTREN SIDEBAR ARCHITECTURE */"

JS_BLOCK = r'''  // VALTREN SIDEBAR ARCHITECTURE START
  function crmRelSidebar(active='relationships',sub=''){
    const nav=(href,label,ic,key)=>`<a class="${active===key?'active':''}" href="${href}">${icon(ic,18)}<span>${label}</span></a>`;
    const subgroup=(key,label,ic,items)=>`<details class="crm-nav-group" ${active===key?'open':''}><summary>${icon(ic,18)}<span>${label}</span><b>⌄</b></summary><div>${items.map(([id,text,href])=>`<a class="${active===key&&sub===id?'active':''}" href="${href}">${text}</a>`).join('')}</div></details>`;
    const finance=[
      ['finance','Transações','#/crm/financeiro'],
      ['accounting','Contabilidade','#/crm/financeiro/accounting'],
      ['invoices','Notas Fiscais','#/crm/financeiro/invoices'],
      ['rateios','Rateios','#/crm/financeiro/rateios'],
      ['participacoes','Participações','#/crm/financeiro/participacoes'],
      ['repasses','Repasses','#/crm/financeiro/repasses']
    ];
    const business=[
      ['products','Produtos','#/crm/negocios'],
      ['services','Serviços','#/crm/negocios/servicos'],
      ['units','Unidades de Negócio','#/crm/negocios/unidades']
    ];
    const legal=`<details class="crm-nav-group crm-nav-legal" ${active==='legal'?'open':''}><summary>${icon('file',18)}<span>Jurídico</span><b>⌄</b></summary><div>
      <a class="${active==='legal'&&sub==='matters'?'active':''}" href="#/crm/juridico">Assuntos Jurídicos</a>
      <details class="crm-nav-subgroup" ${active==='legal'&&String(sub).startsWith('contracts')?'open':''}><summary><span>Contratos</span><b>⌄</b></summary><div>
        <a class="${active==='legal'&&sub==='contracts'?'active':''}" href="#/crm/juridico/contratos">Contratos</a>
        <a class="${active==='legal'&&sub==='contracts-templates'?'active':''}" href="#/crm/juridico/contratos/templates">Templates</a>
        <a class="${active==='legal'&&sub==='contracts-variables'?'active':''}" href="#/crm/juridico/contratos/variaveis">Variáveis</a>
      </div></details>
      <a class="${active==='legal'&&sub==='compliance'?'active':''}" href="#/crm/juridico/compliance">Compliance e Políticas</a>
      <a class="${active==='legal'&&sub==='ip'?'active':''}" href="#/crm/juridico/propriedade-intelectual">Propriedade Intelectual</a>
      <a class="${active==='legal'&&sub==='corporate'?'active':''}" href="#/crm/juridico/societario">Societário</a>
    </div></details>`;
    return `<div class="crm-sidebar-overlay" data-action="crm-sidebar-close" aria-hidden="true"></div><aside id="crm-system-sidebar" class="crm-sidebar" aria-label="Navegação do Sistema Interno">
      <div class="crm-sidebar-head"><a class="crm-brand" href="#/crm/dashboard" aria-label="Valtren Sistema Interno"><img src="assets/valtren-mark.svg" alt="Valtren Solutions"><span><strong>VALTREN</strong><small>Sistema Interno</small></span></a><button class="crm-sidebar-close" type="button" data-action="crm-sidebar-close" aria-label="Fechar navegação">${icon('close',18)}</button></div>
      <nav class="crm-nav" aria-label="Módulos do Sistema Interno">
        ${nav('#/crm/dashboard','Dashboard','layers','dashboard')}
        ${nav('#/crm/relationships','CRM','users','relationships')}
        ${nav('#/crm/agenda','Agenda','calendar','agenda')}
        ${subgroup('accounting','Financeiro','database',finance)}
        ${legal}
        ${nav('#/crm/marketing','Marketing','globe','marketing')}
        ${subgroup('business','Negócios','layers',business)}
        ${nav('#/crm/relatorios','Relatórios','file','reports')}
        ${nav('#/crm/configuracoes','Configurações','settings','settings')}
      </nav>
    </aside>`;
  }

  function crmSidebarIsMobile(){
    return window.matchMedia('(max-width: 760px)').matches;
  }

  function crmSidebarSetOpen(open,restoreFocus=false){
    const sidebar=document.getElementById('crm-system-sidebar');
    const overlay=document.querySelector('.crm-sidebar-overlay');
    const shouldOpen=Boolean(open)&&crmSidebarIsMobile();
    sidebar?.classList.toggle('is-open',shouldOpen);
    overlay?.classList.toggle('is-open',shouldOpen);
    if(sidebar) sidebar.setAttribute('aria-hidden',crmSidebarIsMobile()&&!shouldOpen?'true':'false');
    document.querySelectorAll('[data-action="crm-sidebar-toggle"]').forEach((button)=>button.setAttribute('aria-expanded',String(shouldOpen)));
    document.documentElement.classList.toggle('crm-sidebar-lock',shouldOpen);
    document.body?.classList.toggle('crm-sidebar-lock',shouldOpen);
    if(shouldOpen){
      window.requestAnimationFrame(()=>sidebar?.querySelector('[data-action="crm-sidebar-close"]')?.focus());
    }else if(restoreFocus){
      document.querySelector('[data-action="crm-sidebar-toggle"]')?.focus();
    }
  }

  if(!window.__valtrenSidebarArchitectureBound){
    window.__valtrenSidebarArchitectureBound=true;
    document.addEventListener('click',(event)=>{
      const actionTarget=event.target.closest('[data-action]');
      if(actionTarget?.dataset.action==='crm-sidebar-toggle'){
        event.preventDefault();
        const sidebar=document.getElementById('crm-system-sidebar');
        crmSidebarSetOpen(!sidebar?.classList.contains('is-open'));
        return;
      }
      if(actionTarget?.dataset.action==='crm-sidebar-close'){
        event.preventDefault();
        crmSidebarSetOpen(false,true);
        return;
      }
      const sidebarLink=event.target.closest('#crm-system-sidebar a[href]');
      if(sidebarLink&&crmSidebarIsMobile()) crmSidebarSetOpen(false,false);
    });
    document.addEventListener('keydown',(event)=>{
      if(event.key==='Escape'&&document.getElementById('crm-system-sidebar')?.classList.contains('is-open')) crmSidebarSetOpen(false,true);
    });
    window.addEventListener('resize',()=>{
      if(!crmSidebarIsMobile()) crmSidebarSetOpen(false,false);
    });
  }
  // VALTREN SIDEBAR ARCHITECTURE END
'''

CSS_PATCH = r'''
/* VALTREN SIDEBAR ARCHITECTURE */
.crm-app-shell{padding-left:250px}
.crm-sidebar{position:fixed;inset:0 auto 0 0;width:250px;height:100vh;box-sizing:border-box;overflow-y:auto;overscroll-behavior:contain;z-index:650}
.crm-sidebar-head{display:flex;align-items:center;gap:8px;min-width:0}
.crm-sidebar-head .crm-brand{flex:1;min-width:0}
.crm-sidebar-close{display:none;width:36px;height:36px;flex:0 0 auto;border:1px solid rgba(255,255,255,.16);border-radius:8px;background:rgba(255,255,255,.08);color:inherit;align-items:center;justify-content:center;cursor:pointer}
.crm-sidebar-overlay{display:none}
.crm-mobile-nav-toggle{display:none}
@media(max-width:980px) and (min-width:761px){.crm-app-shell{padding-left:210px}.crm-sidebar{width:210px}}
@media(max-width:760px){
  .crm-app-shell{padding-left:0}
  .crm-mobile-nav-toggle{display:inline-flex}
  .crm-sidebar{display:block;position:fixed;inset:0 auto 0 0;width:min(86vw,320px);height:100dvh;max-height:100dvh;overflow-y:auto;transform:translateX(-104%);transition:transform .2s ease;z-index:750;box-shadow:18px 0 48px rgba(4,15,31,.24)}
  .crm-sidebar.is-open{transform:translateX(0)}
  .crm-sidebar-head{position:sticky;top:0;z-index:2;background:inherit;padding-right:8px}
  .crm-sidebar-close{display:inline-flex}
  .crm-sidebar-overlay{display:block;position:fixed;inset:0;background:rgba(4,15,31,.48);opacity:0;pointer-events:none;transition:opacity .2s ease;z-index:740}
  .crm-sidebar-overlay.is-open{opacity:1;pointer-events:auto}
  html.crm-sidebar-lock,body.crm-sidebar-lock{overflow:hidden}
  .crm-nav-group[open]>div,.crm-nav-subgroup[open]>div{display:grid}
}
'''


def _assert_js_syntax(source: str) -> None:
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(['node','--check',str(temp_path)],capture_output=True,text=True)
        if result.returncode != 0:
            detail=(result.stderr or result.stdout or 'erro sintático desconhecido').strip()
            raise RuntimeError(f'Sidebar Architecture produziu bundle inválido: {detail}')
    finally:
        temp_path.unlink(missing_ok=True)


def _materialize_js(app: str) -> str:
    start_count=app.count(JS_START)
    end_count=app.count(JS_END)
    desired=JS_BLOCK.rstrip()+"\n"
    if start_count==1 and end_count==1:
        start=app.index(JS_START)
        end=app.index(JS_END,start)+len(JS_END)
        current=app[start:end]
        updated=app if current==desired else app[:start]+desired+app[end:]
    elif start_count==0 and end_count==0:
        declarations=len(re.findall(r'\bfunction\s+crmRelSidebar\s*\(',app))
        if declarations:
            raise RuntimeError(f'Owner legado de crmRelSidebar ainda presente antes da primeira materialização: {declarations}')
        anchor='  function contactPage(query)'
        if app.count(anchor)!=1:
            raise RuntimeError(f'Âncora inicial da Sidebar divergente: {app.count(anchor)}')
        at=app.index(anchor)
        updated=app[:at]+desired+"\n"+app[at:]
    else:
        raise RuntimeError(f'Markers da Sidebar divergentes: {start_count}/{end_count}')
    declarations=len(re.findall(r'\bfunction\s+crmRelSidebar\s*\(',updated))
    if declarations!=1:
        raise RuntimeError(f'crmRelSidebar deve possuir exatamente 1 declaração, encontrado {declarations}')
    block=updated[updated.index(JS_START):updated.index(JS_END)]
    if any(token in block for token in ['ValtrenChat','MusicChat','>RH<','Administração']):
        raise RuntimeError('Sidebar canônica contém módulo residual removido')
    for required in ['Marketing','Relatórios','Configurações','Negócios','Jurídico','Financeiro']:
        if required not in block:
            raise RuntimeError(f'Sidebar canônica sem módulo obrigatório: {required}')
    _assert_js_syntax(updated)
    return updated


def _materialize_css(css: str) -> str:
    desired=CSS_PATCH.strip()
    marker_at=css.find(CSS_MARKER)
    if marker_at<0:
        return css.rstrip()+"\n\n"+desired+"\n"
    next_marker=css.find('\n/* ',marker_at+len(CSS_MARKER))
    end=len(css) if next_marker<0 else next_marker+1
    current=css[marker_at:end].strip()
    if current==desired:
        return css
    prefix=css[:marker_at].rstrip()
    suffix=css[end:].lstrip('\n')
    return prefix+"\n\n"+desired+"\n"+(("\n"+suffix) if suffix else '')


def apply_crm_sidebar_architecture() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError('app.js ou assets/valtren-brand.css ausente')
    app=APP.read_text(encoding='utf-8')
    updated_app=_materialize_js(app)
    if updated_app!=app:
        APP.write_text(updated_app,encoding='utf-8')
    css=CSS.read_text(encoding='utf-8')
    updated_css=_materialize_css(css)
    if updated_css!=css:
        CSS.write_text(updated_css,encoding='utf-8')
    for path in ROOT.rglob('*.html'):
        rel=path.relative_to(ROOT)
        if any(part in {'.git','.bootstrap','node_modules','scripts'} for part in rel.parts):
            continue
        text=path.read_text(encoding='utf-8')
        updated=re.sub(r'app\.js(?:\?v=[A-Za-z0-9._-]+)?',f'app.js?v={CACHE_VERSION}',text)
        updated=re.sub(r'valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?',f'valtren-brand.css?v={CACHE_VERSION}',updated)
        if updated!=text:
            path.write_text(updated,encoding='utf-8')
    print('Sidebar Architecture materializada com owner único, drawer mobile e saída byte-stable.')
    return 1


if __name__=='__main__':
    apply_crm_sidebar_architecture()
