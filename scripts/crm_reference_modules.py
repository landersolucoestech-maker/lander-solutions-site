from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
APP=ROOT/'app.js'
CSS=ROOT/'assets'/'valtren-brand.css'
CACHE_VERSION='20260826-crm-reference-modules-v4'
CSS_MARKER='/* VALTREN CRM REFERENCE MODULES */'


def _parts(prefix:str)->str:
    files=sorted(HERE.glob(prefix))
    if not files: raise RuntimeError(f'Partes ausentes: {prefix}')
    return ''.join(p.read_text(encoding='utf-8') for p in files)


def _strip_legacy_sidebar_css(css_block:str)->str:
    # Reference Modules is a navigation consumer. Any selector exclusively
    # styling the canonical sidebar belongs to crm_sidebar_architecture.py.
    lines=[]
    removed=0
    for line in css_block.splitlines():
        if '.crm-nav-group' in line or '.crm-nav-subgroup' in line:
            removed+=1
            continue
        lines.append(line)
    cleaned='\n'.join(lines).strip()+'\n'
    if removed<1:
        raise RuntimeError('CSS legado da Sidebar esperado em Reference Modules não foi localizado')
    if '.crm-nav-group' in cleaned or '.crm-nav-subgroup' in cleaned:
        raise RuntimeError('Reference Modules ainda contém CSS de ownership da Sidebar')
    return cleaned


def _replace_css_block(css:str, block:str)->str:
    desired=block.strip()
    marker_at=css.find(CSS_MARKER)
    if marker_at<0:
        return css.rstrip()+'\n\n'+desired+'\n'
    next_marker=css.find('\n/* ',marker_at+len(CSS_MARKER))
    end=len(css) if next_marker<0 else next_marker+1
    current=css[marker_at:end].strip()
    if current==desired:
        return css
    prefix=css[:marker_at].rstrip()
    suffix=css[end:].lstrip('\n')
    return prefix+'\n\n'+desired+'\n'+(('\n'+suffix) if suffix else '')


def apply_crm_reference_modules()->int:
    app=APP.read_text(encoding='utf-8')
    js_block=_parts('crm_reference_modules.js.part*')
    css_block=_strip_legacy_sidebar_css(_parts('crm_reference_modules.css.part*'))
    # Keep only shared primitives/runtime. Page/navigation ownership belongs to
    # definitive/domain materializers and the dedicated Sidebar owner.
    js_block = re.sub(r"\n  const CRM_REF_MARKETING_SUB=.*?;\n", "\n", js_block, count=1)
    js_block = re.sub(r"\n    if\(!state\.crmRefMusicChat\)\{.*?\}\n", "\n", js_block, count=1)
    for start_anchor,end_anchor,label in [
        ("\n  function crmRefFinancePage", "\n  function crmRefTransactionModal", "legacy finance pages"),
        ("\n  function crmRefMarketingOverview", "\n  function crmRefReportsPage", "legacy marketing pages"),
        ("\n  function crmRefReportsPage", "\n  function crmRefSettingsPage", "legacy reports pages"),
        ("\n  function crmRefSettingsPage", "\n  function crmRefUserModal", "legacy settings pages"),
        ("\n  function crmReferenceRoute(path){", "\n  // VALTREN CRM REFERENCE MODULES END", "legacy reference router"),
    ]:
        start=js_block.find(start_anchor)
        end=js_block.find(end_anchor,start+1) if start>=0 else -1
        if start<0 or end<0:
            raise RuntimeError(f"Reference Modules boundary ausente: {label}")
        js_block=js_block[:start]+js_block[end:]

    app=re.sub(r"\n?  // VALTREN CRM REFERENCE MODULES START\n.*?  // VALTREN CRM REFERENCE MODULES END\n",'\n',app,flags=re.S)

    # Dashboard pertence ao seu próprio materializador e já consome o sidebar
    # compartilhado. Reference Modules não deve procurar/regravar markup inline.
    if app.count("${crmRelSidebar('dashboard','dashboard')}") != 1 and app.count("${crmRelSidebar('dashboard')}") != 1:
        raise RuntimeError('Dashboard não consome crmRelSidebar compartilhado')

    anchor='  function contactPage(query)'
    if anchor not in app:
        raise RuntimeError('âncora contactPage ausente')
    app=app.replace(anchor,js_block+'\n'+anchor,1)

    route_anchor="    else if (path === '/crm/agenda') app.innerHTML = crmAgendaPage(query);"
    route_line="    else if (path.startsWith('/crm/financeiro') || path.startsWith('/crm/marketing') || path === '/crm/musicchat' || path === '/crm/relatorios' || path.startsWith('/crm/configuracoes')) app.innerHTML = crmReferenceRoute(path);"
    if app.count(route_anchor)<2:
        raise RuntimeError('rotas base do CRM incompletas')
    app=app.replace(route_anchor,route_anchor+'\n'+route_line)
    APP.write_text(app,encoding='utf-8')

    css=CSS.read_text(encoding='utf-8')
    updated_css=_replace_css_block(css,css_block)
    if updated_css!=css:
        CSS.write_text(updated_css,encoding='utf-8')

    for p in ROOT.rglob('*.html'):
        rel=p.relative_to(ROOT)
        if any(x in {'.git','.bootstrap','node_modules','scripts'} for x in rel.parts):
            continue
        t=p.read_text(encoding='utf-8')
        t=re.sub(r'app\.js(?:\?v=[A-Za-z0-9._-]+)?',f'app.js?v={CACHE_VERSION}',t)
        t=re.sub(r'valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?',f'valtren-brand.css?v={CACHE_VERSION}',t)
        p.write_text(t,encoding='utf-8')

    print('Módulos de referência materializados como consumers da navegação canônica; CSS estrutural da sidebar removido deste owner.')
    return 1


if __name__=='__main__':
    apply_crm_reference_modules()
