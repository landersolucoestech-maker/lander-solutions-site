from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
APP=ROOT/'app.js'
CSS=ROOT/'assets'/'valtren-brand.css'
CACHE_VERSION='20260825-crm-reference-modules-v2'

def _parts(prefix:str)->str:
    files=sorted(HERE.glob(prefix))
    if not files: raise RuntimeError(f'Partes ausentes: {prefix}')
    return ''.join(p.read_text(encoding='utf-8') for p in files)

def apply_crm_reference_modules()->int:
    app=APP.read_text(encoding='utf-8')
    js_block=_parts('crm_reference_modules.js.part*')
    css_block=_parts('crm_reference_modules.css.part*')
    sidebar=(HERE/'crm_reference_sidebar.txt').read_text(encoding='utf-8')
    app=re.sub(r"\n?  // VALTREN CRM REFERENCE MODULES START\n.*?  // VALTREN CRM REFERENCE MODULES END\n",'\n',app,flags=re.S)
    pat=r"  function crmRelSidebar\(active='relationships'(?:,sub='')?\)\{.*?\n  \}\n\n  function crmRelActions"
    if not re.search(pat,app,flags=re.S): raise RuntimeError('crmRelSidebar não encontrado')
    app=re.sub(pat,sidebar+'\n  function crmRelActions',app,count=1,flags=re.S)
    start=app.find('  function crmDashboardPage(query)'); end=app.find('  function crmRelEnsureState()',start)
    if start<0 or end<0: raise RuntimeError('Dashboard CRM não encontrado')
    seg=app[start:end]
    seg2=re.sub(r'\n      <aside class="crm-sidebar">.*?</aside>\n      <main class="crm-main">',"\n      ${crmRelSidebar('dashboard')}\n      <main class=\"crm-main\">",seg,count=1,flags=re.S)
    if seg2==seg: raise RuntimeError('Sidebar inline do Dashboard não encontrado')
    app=app[:start]+seg2+app[end:]
    anchor='  function contactPage(query)'
    if anchor not in app: raise RuntimeError('âncora contactPage ausente')
    app=app.replace(anchor,js_block+'\n'+anchor,1)
    route_anchor="    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query);"
    route_line="    else if (path.startsWith('/crm/financeiro') || path.startsWith('/crm/marketing') || path === '/crm/musicchat' || path === '/crm/relatorios' || path.startsWith('/crm/configuracoes')) app.innerHTML = crmReferenceRoute(path);"
    if app.count(route_anchor)<2: raise RuntimeError('rotas base do CRM incompletas')
    app=app.replace(route_anchor,route_anchor+'\n'+route_line)
    APP.write_text(app,encoding='utf-8')
    css=CSS.read_text(encoding='utf-8')
    css=re.sub(r"\n?/\* VALTREN CRM REFERENCE MODULES \*/.*\Z",'',css,flags=re.S)
    CSS.write_text(css.rstrip()+'\n\n'+css_block.strip()+'\n',encoding='utf-8')
    for p in ROOT.rglob('*.html'):
        rel=p.relative_to(ROOT)
        if any(x in {'.git','.bootstrap','node_modules','scripts'} for x in rel.parts): continue
        t=p.read_text(encoding='utf-8')
        t=re.sub(r'app\.js(?:\?v=[A-Za-z0-9._-]+)?',f'app.js?v={CACHE_VERSION}',t)
        t=re.sub(r'valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?',f'valtren-brand.css?v={CACHE_VERSION}',t)
        p.write_text(t,encoding='utf-8')
    print('Módulos Financeiro, Marketing, MusicChat, Relatórios e Configurações aplicados a partir das referências anexadas.')
    return 1

if __name__=='__main__': apply_crm_reference_modules()
