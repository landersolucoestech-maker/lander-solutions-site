from pathlib import Path
import re

ROOT=Path('.')

def read(path): return (ROOT/path).read_text(encoding='utf-8')
def write(path,text): (ROOT/path).write_text(text,encoding='utf-8')
def sub_once(text,pattern,repl,label,flags=0):
    updated,count=re.subn(pattern,repl,text,count=1,flags=flags)
    if count!=1: raise RuntimeError(f'{label}: esperado 1 replacement, encontrado {count}')
    return updated

# 1) CRM Relacionamentos becomes a sidebar consumer. Remove fake seeds and the legacy sidebar declaration at source.
path = 'scripts/crm_relationships_module.py'
text = read(path)
text = sub_once(
    text,
    r"\n  function crmRelSidebar\(active='relationships'\)\{.*?\n  \}\n\n  function crmRelActions",
    "\n\n  function crmRelActions",
    'legacy crmRelSidebar in relationships',
    re.S,
)
text = sub_once(
    text,
    r"  function crmRelEnsureState\(\)\{.*?\n  \}\n\n  function crmRelActions",
    "  function crmRelEnsureState(){\n    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];\n    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];\n  }\n\n  function crmRelActions",
    'relationship fake seeds',
    re.S,
)
if 'function crmRelSidebar' in text:
    raise RuntimeError('relationships still contains crmRelSidebar')
for forbidden in ['Marina Costa','Aurora Tecnologia Ltda.','Grupo Horizonte','Rafael Nunes','Paulo Mendes','Fernanda Lima','Daniel Souza']:
    if forbidden in text:
        raise RuntimeError(f'fake relationship seed survived: {forbidden}')
write(path, text)

# 2) Reference Modules no longer rewrites a sidebar owned elsewhere.
path = 'scripts/crm_reference_modules.py'
text = read(path)
text = text.replace("    sidebar=(HERE/'crm_reference_sidebar.txt').read_text(encoding='utf-8')\n", '')
start = text.find('    pat=r"  function crmRelSidebar')
end = text.find('    # Dashboard pertence', start)
if start < 0 or end < 0:
    raise RuntimeError('reference modules legacy sidebar replacement block not found')
text = text[:start] + text[end:]
if 'crm_reference_sidebar.txt' in text or 're.sub(pat,sidebar' in text:
    raise RuntimeError('reference modules still owns sidebar replacement')
text = text.replace(
    "print('Módulos de referência materializados sem reescrever Dashboard ou criar segundo owner de sidebar nele.')",
    "print('Módulos de referência materializados como consumers da navegação canônica; Dashboard e sidebar permanecem com seus owners.')",
)
write(path, text)
sidebar_legacy = ROOT / 'scripts/crm_reference_sidebar.txt'
if sidebar_legacy.exists():
    sidebar_legacy.unlink()

# 3) Fidelity layer keeps page primitives only; remove its second sidebar declaration.
path = 'scripts/crm_reference_fidelity_fix.js.part01'
text = read(path)
text = sub_once(
    text,
    r"\n  function crmRelSidebar\(active='relationships',sub=''\)\{.*?\n  \}\n\n  function crmRefFinancePage",
    "\n\n  function crmRefFinancePage",
    'fidelity crmRelSidebar',
    re.S,
)
if 'function crmRelSidebar' in text:
    raise RuntimeError('fidelity payload still contains crmRelSidebar')
write(path, text)

# 4) Canonical Parties uses a CRM-owned function boundary, not the sidebar.
path = 'scripts/crm_canonical_parties.py'
text = read(path)
count = text.count('function crmRelSidebar')
if count != 2:
    raise RuntimeError(f'canonical parties sidebar-boundary count unexpected: {count}')
text = text.replace('function crmRelSidebar', 'function crmRelActions')
write(path, text)

# 5) Global review stays transverse: no Header or Sidebar ownership.
path = 'scripts/crm_product_system_review.py'
text = read(path)
text = re.sub(r'^HEADER_START = .*\nHEADER_END = .*\n', '', text, count=1, flags=re.M)
start = text.find('def _replace_marked_block')
end = text.find('EMPTY_RELATIONSHIP_STATE =', start)
if start < 0 or end < 0:
    raise RuntimeError('global review header ownership block not found')
text = text[:start] + text[end:]
text = sub_once(
    text,
    r"EMPTY_RELATIONSHIP_STATE = r'''  function crmRelEnsureState\(\)\{.*?'''\n\nEMPTY_USERS",
    "EMPTY_RELATIONSHIP_STATE = r'''  function crmRelEnsureState(){\n    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];\n    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];\n    crmCanonicalEnsureFromLegacy();\n  }\n'''\n\nEMPTY_USERS",
    'global relationship empty state',
    re.S,
)
text = text.replace(
    '("  function crmRelEnsureState(){", "  function crmRelSidebar(", EMPTY_RELATIONSHIP_STATE, "crmRelEnsureState"),',
    '("  function crmRelEnsureState(){", "  function crmRelActions(", EMPTY_RELATIONSHIP_STATE, "crmRelEnsureState"),',
)
text = text.replace(
    '    app = _replace_marked_block(app, HEADER_START, HEADER_END, HEADER_HELPERS, "Account Menu")\n',
    "    if app.count(\"  function crmHeaderActions(context=''){\") != 1:\n        raise RuntimeError('Header owner divergente antes da revisão global')\n    if 'Autenticação desativada' not in app or 'Nenhuma identidade é simulada' not in app:\n        raise RuntimeError('Header owner perdeu transparência de autenticação')\n",
)
# Remove layout ownership of sidebar from the global design-system patch.
text = re.sub(
    r"\.crm-app-shell\{display:block;grid-template-columns:none;min-height:100vh;background:var\(--crm-bg\);color:var\(--crm-text\);padding-left:250px\}\.crm-sidebar\{position:fixed;inset:0 auto 0 0;width:250px;height:100vh;box-sizing:border-box;overflow-y:auto;overscroll-behavior:contain;z-index:100\}\.crm-main",
    '.crm-app-shell{display:block;grid-template-columns:none;min-height:100vh;background:var(--crm-bg);color:var(--crm-text)}.crm-main',
    text,
    count=1,
)
text = re.sub(
    r"@media\(max-width:980px\) and \(min-width:761px\)\{\.crm-app-shell\{padding-left:210px\}\.crm-sidebar\{width:210px\}",
    '@media(max-width:980px) and (min-width:761px){',
    text,
    count=1,
)
text = re.sub(
    r"@media\(max-width:760px\)\{\.crm-app-shell\{padding-left:0\}\.crm-sidebar\{position:static;width:auto;height:auto;max-height:none;overflow:visible\}",
    '@media(max-width:760px){',
    text,
    count=1,
)
if '_replace_marked_block' in text or 'HEADER_HELPERS' in text:
    raise RuntimeError('global review still owns Header implementation')
if '.crm-sidebar{position:' in text:
    raise RuntimeError('global review still owns Sidebar positioning')
write(path, text)

# 6) Header owner: mobile navigation toggle + tablet-safe Account Menu.
path = 'scripts/crm_global_header.py'
text = read(path)
old = '    return `<div class="crm-header-actions">${create}<details class="crm-account-menu">'
new = '    const navToggle=`<button class="crm-mobile-nav-toggle" type="button" data-action="crm-sidebar-toggle" aria-controls="crm-system-sidebar" aria-expanded="false" aria-label="Abrir navegação">${icon(\'menu\',18)}<span>Menu</span></button>`;\n    return `<div class="crm-header-actions">${navToggle}${create}<details class="crm-account-menu">'
if old not in text:
    raise RuntimeError('header return anchor not found')
text = text.replace(old, new, 1)
old_media = '@media(max-width:760px){.crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:wrap;margin-left:0}}'
new_media = '@media(max-width:980px){.crm-account-copy{display:none}.crm-account-menu>summary{gap:6px;padding:5px 8px}.crm-account-popover{max-width:calc(100vw - 24px)}}\n@media(max-width:760px){.crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:wrap;margin-left:0}.crm-account-menu{margin-left:auto}}'
if old_media not in text:
    raise RuntimeError('header mobile CSS anchor not found')
text = text.replace(old_media, new_media, 1)
write(path, text)
