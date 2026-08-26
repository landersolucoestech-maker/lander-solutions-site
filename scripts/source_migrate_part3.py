from pathlib import Path
import re

ROOT=Path('.')

def read(path): return (ROOT/path).read_text(encoding='utf-8')
def write(path,text): (ROOT/path).write_text(text,encoding='utf-8')
def sub_once(text,pattern,repl,label,flags=0):
    updated,count=re.subn(pattern,repl,text,count=1,flags=flags)
    if count!=1: raise RuntimeError(f'{label}: esperado 1 replacement, encontrado {count}')
    return updated

path='scripts/crm_sidebar_architecture.py'
text=read(path)
text=text.replace('.crm-sidebar-overlay{display:none}\n.crm-mobile-nav-toggle{display:none}\n','.crm-sidebar-overlay{display:none}\n')
text=text.replace('  .crm-mobile-nav-toggle{display:inline-flex}\n','')
if '.crm-mobile-nav-toggle' in text: raise RuntimeError('sidebar owner ainda estiliza o botão do Header')
write(path,text)

path='scripts/crm_reference_modules.py'
text=read(path)
anchor="    css_block=_parts('crm_reference_modules.css.part*')\n"
if anchor not in text: raise RuntimeError('reference modules normalization anchor not found')
normalization=r'''    # Keep only shared primitives/runtime. Page/navigation ownership belongs to
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
'''
text=text.replace(anchor,anchor+normalization,1)
write(path,text)

path='scripts/crm_reference_fidelity_fix.js.part01'
text=read(path)
text=sub_once(text,r"\n  function crmRefMarketingOverview\(\).*?\}\s*\Z","\n",'fidelity marketing overview',re.S)
write(path,text)
write('scripts/crm_reference_fidelity_fix.js.part02','\n')
path='scripts/crm_reference_fidelity_fix.js.part03'
text=read(path)
reports=text.find('  function crmRefReportsPage()')
settings=text.find('  function crmRefSettingsPage()',reports)
if reports<0 or settings<0: raise RuntimeError('fidelity reports/settings boundaries not found')
text='\n'+text[reports:settings].rstrip()+'\n'
write(path,text)
write('scripts/crm_reference_fidelity_fix.js.part04','\n  // VALTREN CRM REFERENCE FIDELITY FIX END\n')

path='scripts/crm_global_header.py'
text=read(path)
header_css="""CSS_PATCH = r'''
/* VALTREN CRM GLOBAL HEADER */
.crm-app-shell .crm-topbar{position:relative;z-index:80;overflow:visible}
.crm-header-actions{margin-left:auto;display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:0;flex:0 0 auto}
.crm-header-create,.crm-mobile-nav-toggle{min-height:38px;border-radius:8px;padding:0 12px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font:inherit;font-weight:700;cursor:pointer;white-space:nowrap}
.crm-header-create{border:0;background:#0B1D3A;color:#fff}
.crm-mobile-nav-toggle{display:none;border:1px solid rgba(11,29,58,.14);background:#fff;color:#0B1D3A}
.crm-account-menu{position:relative;min-width:0}
.crm-account-menu>summary{list-style:none;min-height:44px;display:flex;align-items:center;gap:10px;padding:5px 10px;border:1px solid rgba(11,29,58,.12);border-radius:12px;background:#fff;cursor:pointer;box-sizing:border-box}
.crm-account-menu>summary::-webkit-details-marker{display:none}
.crm-account-icon{width:30px;height:30px;flex:0 0 30px;border-radius:50%;display:grid;place-items:center;background:#f8fafc;border:1px solid rgba(11,29,58,.12)}
.crm-account-copy{display:flex;min-width:0;flex-direction:column;align-items:flex-start;line-height:1.15}.crm-account-copy strong{font-size:13px}.crm-account-copy small{font-size:10px;color:#687386;margin-top:3px;white-space:nowrap}
.crm-account-chevron{color:#687386;flex:0 0 auto}
.crm-account-popover{position:absolute;right:0;top:calc(100% + 8px);width:min(320px,calc(100vw - 28px));box-sizing:border-box;padding:16px;border:1px solid rgba(11,29,58,.12);border-radius:12px;background:#fff;box-shadow:0 16px 40px rgba(11,29,58,.16);z-index:800}.crm-account-popover p{font-size:12px;line-height:1.5;color:#687386;margin:7px 0 12px}.crm-account-popover a{color:#0B1D3A;font-weight:700;text-decoration:none}
@media(max-width:980px){.crm-account-copy{display:none}.crm-account-menu>summary{gap:6px;padding:5px 8px}.crm-account-popover{max-width:calc(100vw - 24px)}}
@media(max-width:760px){.crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:wrap;margin-left:0}.crm-mobile-nav-toggle{display:inline-flex}.crm-account-menu{margin-left:auto}.crm-account-popover{position:fixed;right:12px;top:auto;max-width:calc(100vw - 24px)}}
'''
"""
text=sub_once(text,r"CSS_PATCH = r'''\n/\* VALTREN CRM GLOBAL HEADER \*/.*?\n'''\n",lambda m:header_css,'header CSS ownership',re.S)
write(path,text)

path='scripts/crm_product_system_review.py'
text=read(path)
text=sub_once(text,r"\n\.crm-header-actions\{.*?\.crm-account-popover a\{[^\n]*\}\n","\n",'global header CSS ownership',re.S)
text=text.replace('.crm-header-actions{width:100%;justify-content:space-between}.crm-account-menu{margin-left:auto}','')
text=text.replace('.crm-header-create{flex:1;justify-content:center}.crm-account-copy{display:none}','')
if '.crm-account-menu>' in text or '.crm-header-actions{' in text or '.crm-mobile-nav-toggle' in text: raise RuntimeError('global review ainda possui CSS do Header/Account Menu')
write(path,text)

path='scripts/crm_financial_transactions.css'
text=read(path).rstrip()
mobile=r'''
@media(max-width:760px){
  .crm-fin-account-strip{display:grid;grid-template-columns:1fr;overflow:visible;padding-bottom:0}
  .crm-fin-account-card,.crm-fin-account-add{width:100%;max-width:100%;flex:0 0 auto;box-sizing:border-box}
  .crm-fin-status-tabs{width:100%;overflow-x:auto;box-sizing:border-box}
  .crm-fin-status-tabs button{flex:0 0 auto}
  .crm-fin-toolbar{display:grid;grid-template-columns:1fr;align-items:stretch}
  .crm-fin-search{width:100%;min-width:0;max-width:none;box-sizing:border-box;flex:none}
  .crm-fin-toolbar>select,.crm-fin-toolbar>input,.crm-fin-more,.crm-fin-more>summary{width:100%;max-width:none;box-sizing:border-box}
  .crm-fin-more>div{left:0;right:auto;width:100%;min-width:0;box-sizing:border-box}
  .crm-fin-bulk{align-items:stretch;flex-direction:column}
  .crm-fin-bulk select,.crm-fin-bulk button{width:100%;max-width:none;box-sizing:border-box}
  .crm-fin-form-grid{grid-template-columns:1fr}
  .crm-fin-allocation-row{grid-template-columns:minmax(0,1fr) 88px 32px}
  .crm-fin-pagination{min-height:48px;flex-wrap:wrap;gap:8px;padding-block:8px}
  .crm-fin-modal footer{flex-wrap:wrap}.crm-fin-modal footer button{flex:1 1 120px}
}
'''
if mobile.strip() not in text: text += '\n'+mobile.strip()+'\n'
write(path,text)

path='scripts/materialize.py'
text=read(path)
import_anchor='        from crm_definitive_architecture import apply_crm_definitive_architecture\n'
if import_anchor not in text: raise RuntimeError('materialize definitive import anchor missing')
text=text.replace(import_anchor,import_anchor+'        from crm_sidebar_architecture import apply_crm_sidebar_architecture\n',1)
call_anchor='        apply_crm_definitive_architecture()\n'
if call_anchor not in text: raise RuntimeError('materialize definitive call anchor missing')
text=text.replace(call_anchor,call_anchor+'        apply_crm_sidebar_architecture()\n',1)
write(path,text)

path='scripts/crm_product_system_review_runner.py'
text=read(path)
text=text.replace('import crm_product_system_review as review\n','import crm_product_system_review as review\nimport crm_sidebar_architecture as sidebar\n',1)
insert='''

def _verify_sidebar_idempotence() -> None:
    tracked = [sidebar.APP, sidebar.CSS, sidebar.ROOT / "index.html"]
    before = {path: _digest(path) for path in tracked if path.exists()}
    position_before = sidebar.APP.read_text(encoding="utf-8").index(sidebar.JS_START)
    sidebar.apply_crm_sidebar_architecture()
    after = {path: _digest(path) for path in tracked if path.exists()}
    position_after = sidebar.APP.read_text(encoding="utf-8").index(sidebar.JS_START)
    if before != after or position_before != position_after:
        changed = [str(path.relative_to(sidebar.ROOT)) for path in before if before.get(path) != after.get(path)]
        raise RuntimeError(f"Sidebar Architecture não é idempotente após a cadeia: {changed}")
    app = sidebar.APP.read_text(encoding="utf-8")
    if len(re.findall(r"\bfunction\s+crmRelSidebar\s*\(", app)) != 1:
        raise RuntimeError("crmRelSidebar não possui owner único após rerun")
    _assert_js_syntax(app, "rerun idempotente da Sidebar Architecture")
    print("Sidebar Architecture materializer idempotence: PASS")
'''
anchor='\ndef apply_crm_product_system_review() -> int:\n'
if anchor not in text: raise RuntimeError('review runner apply anchor missing')
text=text.replace(anchor,insert+anchor,1)
old='''    app = review.APP.read_text(encoding="utf-8")
    app = review._replace_marked_block(app, review.HEADER_START, review.HEADER_END, review.HEADER_HELPERS, "Account Menu")
    _assert_js_syntax(app, "Account Menu compartilhado")

'''
new='''    _verify_sidebar_idempotence()
    app = review.APP.read_text(encoding="utf-8")
    if app.count("  function crmHeaderActions(context=''){") != 1:
        raise RuntimeError("Header compartilhado não possui owner único")
    if 'Autenticação desativada' not in app or 'Nenhuma identidade é simulada' not in app:
        raise RuntimeError("Header perdeu transparência de autenticação")
    _assert_js_syntax(app, "Header e Sidebar canônicos")

'''
if old not in text: raise RuntimeError('review runner legacy header step missing')
text=text.replace(old,new,1)
write(path,text)

test="""const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
const materialized=process.argv.includes('--materialized');
const fail=(m)=>{throw new Error(m)};
const must=(c,m)=>{if(!c)fail(m)};
const read=(name)=>fs.readFileSync(path.join(__dirname,name),'utf8');
const owner=read('crm_sidebar_architecture.py');
const relationships=read('crm_relationships_module.py');
const fidelity=read('crm_reference_fidelity_fix.js.part01')+read('crm_reference_fidelity_fix.js.part02')+read('crm_reference_fidelity_fix.js.part03')+read('crm_reference_fidelity_fix.js.part04');
const definitive=read('crm_definitive_architecture.py');
const reference=read('crm_reference_modules.py');
const materialize=read('materialize.py');
const header=read('crm_global_header.py');
const review=read('crm_product_system_review.py');
must(owner.includes('VALTREN SIDEBAR ARCHITECTURE START'),'sidebar owner start marker missing');
must(owner.includes('VALTREN SIDEBAR ARCHITECTURE END'),'sidebar owner end marker missing');
must(owner.includes("function crmRelSidebar(active='relationships',sub='')"),'sidebar owner declaration missing');
must(!relationships.includes('function crmRelSidebar'),'relationships still owns sidebar');
must(!fidelity.includes('function crmRelSidebar'),'fidelity still owns sidebar');
must(!definitive.includes('function crmRelSidebar'),'definitive architecture still owns sidebar');
must(!reference.includes('crm_reference_sidebar.txt'),'reference modules still rewrites sidebar');
must(materialize.includes('from crm_sidebar_architecture import apply_crm_sidebar_architecture'),'materialize missing sidebar owner import');
must(materialize.includes('apply_crm_sidebar_architecture()'),'materialize missing sidebar owner call');
must(owner.includes("nav('#/crm/marketing','Marketing'"),'Marketing must remain first-level');
must(owner.includes("nav('#/crm/relatorios','Relatórios'"),'Reports must remain');
['ValtrenChat','MusicChat',"nav('#/crm/rh'",'Administração'].forEach((token)=>must(!owner.includes(token),`sidebar owner still contains removed module: ${token}`));
must(header.includes('crm-sidebar-toggle'),'Header missing mobile navigation toggle');
must(header.includes('@media(max-width:980px){.crm-account-copy{display:none}'),'Header missing tablet Account Menu compaction');
must(!review.includes('.crm-sidebar{position:'),'global review still positions Sidebar');
must(!review.includes('.crm-account-menu>summary'),'global review still styles Account Menu');
if(materialized){
 const app=fs.readFileSync(path.join(root,'app.js'),'utf8');
 const css=fs.readFileSync(path.join(root,'assets','valtren-brand.css'),'utf8');
 const decl=(app.match(/\\bfunction\\s+crmRelSidebar\\s*\\(/g)||[]).length;
 must(decl===1,`crmRelSidebar declaration count must be 1, got ${decl}`);
 must((app.match(/VALTREN SIDEBAR ARCHITECTURE START/g)||[]).length===1,'sidebar start marker count mismatch');
 must((app.match(/VALTREN SIDEBAR ARCHITECTURE END/g)||[]).length===1,'sidebar end marker count mismatch');
 const s=app.indexOf('VALTREN SIDEBAR ARCHITECTURE START');
 const e=app.indexOf('VALTREN SIDEBAR ARCHITECTURE END',s);
 const block=app.slice(s,e);
 ['ValtrenChat','MusicChat','>RH<','Administração'].forEach((token)=>must(!block.includes(token),`removed module leaked into materialized sidebar: ${token}`));
 ['Marketing','Relatórios','Configurações','Negócios','Jurídico','Financeiro'].forEach((token)=>must(block.includes(token),`required sidebar module missing: ${token}`));
 must(app.includes("if(path==='/crm/valtrenchat'||path==='/crm/musicchat')return crmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);"),'ValtrenChat legacy route missing integration redirect');
 must(app.includes("if(path==='/crm/rh')return crmArchitecturePlaceholderPage('','hr','RH'"),'RH compatibility route missing honest placeholder');
 must(app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();"),'Marketing route must use unavailable/non-simulated workspace');
 must(app.includes("if(path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas')return crmArchitecturePlaceholderPage('','admin','Administração'"),'Administration compatibility route missing honest placeholder');
 must(css.includes('/* VALTREN SIDEBAR ARCHITECTURE */'),'sidebar CSS owner missing');
 must(css.includes('transform:translateX(-104%)'),'mobile drawer closed state missing');
 must(css.includes('.crm-sidebar.is-open{transform:translateX(0)}'),'mobile drawer open state missing');
 must(css.includes('html.crm-sidebar-lock,body.crm-sidebar-lock{overflow:hidden}'),'mobile body lock missing');
}
console.log(`sidebar-architecture: PASS${materialized?' (materialized)':''}`);
"""
write('scripts/test_crm_sidebar_architecture.js',test)

path='.github/workflows/pages-dev.yml'
text=read(path)
source_anchor='''      - name: Test global product-system review
        run: |
          python -m py_compile scripts/crm_product_system_review.py
          node scripts/test_crm_product_system_review.js

'''
source_insert=source_anchor+'''      - name: Test sidebar architecture owner
        run: |
          python -m py_compile scripts/crm_sidebar_architecture.py
          node scripts/test_crm_sidebar_architecture.js

'''
if source_anchor not in text: raise RuntimeError('workflow source gate anchor missing')
text=text.replace(source_anchor,source_insert,1)
idemp_anchor='''      - name: Verify global product-system review idempotence
        run: |
          APP_BEFORE="$(sha256sum app.js | awk '{print $1}')"
          CSS_BEFORE="$(sha256sum assets/valtren-brand.css | awk '{print $1}')"
          INDEX_BEFORE="$(sha256sum index.html | awk '{print $1}')"
          python scripts/crm_product_system_review.py
          APP_AFTER="$(sha256sum app.js | awk '{print $1}')"
          CSS_AFTER="$(sha256sum assets/valtren-brand.css | awk '{print $1}')"
          INDEX_AFTER="$(sha256sum index.html | awk '{print $1}')"
          echo "Product review app.js SHA before: $APP_BEFORE"
          echo "Product review app.js SHA after:  $APP_AFTER"
          test "$APP_BEFORE" = "$APP_AFTER"
          test "$CSS_BEFORE" = "$CSS_AFTER"
          test "$INDEX_BEFORE" = "$INDEX_AFTER"

'''
sidebar_gate=idemp_anchor+'''      - name: Verify Sidebar Architecture idempotence and ownership
        run: |
          APP_BEFORE="$(sha256sum app.js | awk '{print $1}')"
          CSS_BEFORE="$(sha256sum assets/valtren-brand.css | awk '{print $1}')"
          INDEX_BEFORE="$(sha256sum index.html | awk '{print $1}')"
          POS_BEFORE="$(python - <<'PY'
from pathlib import Path
print(Path('app.js').read_text().index('  // VALTREN SIDEBAR ARCHITECTURE START'))
PY
)"
          python scripts/crm_sidebar_architecture.py
          node --check app.js
          APP_AFTER="$(sha256sum app.js | awk '{print $1}')"
          CSS_AFTER="$(sha256sum assets/valtren-brand.css | awk '{print $1}')"
          INDEX_AFTER="$(sha256sum index.html | awk '{print $1}')"
          POS_AFTER="$(python - <<'PY'
from pathlib import Path
print(Path('app.js').read_text().index('  // VALTREN SIDEBAR ARCHITECTURE START'))
PY
)"
          test "$APP_BEFORE" = "$APP_AFTER"
          test "$CSS_BEFORE" = "$CSS_AFTER"
          test "$INDEX_BEFORE" = "$INDEX_AFTER"
          test "$POS_BEFORE" = "$POS_AFTER"
          test "$(grep -Eo 'function[[:space:]]+crmRelSidebar[[:space:]]*\\(' app.js | wc -l)" -eq 1
          node scripts/test_crm_sidebar_architecture.js --materialized

'''
if idemp_anchor not in text: raise RuntimeError('workflow global idempotence anchor missing')
text=text.replace(idemp_anchor,sidebar_gate,1)
materialized_anchor='''          readonly_suite scripts/test_crm_product_system_review.js --materialized
          FINAL_SHA="$(sha256sum app.js | awk '{print $1}')"
'''
if materialized_anchor not in text: raise RuntimeError('workflow materialized matrix anchor missing')
text=text.replace(materialized_anchor,"          readonly_suite scripts/test_crm_product_system_review.js --materialized\n          readonly_suite scripts/test_crm_sidebar_architecture.js --materialized\n          FINAL_SHA=\"$(sha256sum app.js | awk '{print $1}')\"\n",1)
write(path,text)

print('Source migration part 3 prepared: sidebar owner, runtime cleanup, responsive owners and CI gates.')
