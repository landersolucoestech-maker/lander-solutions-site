from pathlib import Path

old='''    sidebar_start = app.rfind("function crmRelSidebar")
    sidebar_end = app.find("function crmReferenceRoute", sidebar_start)
    sidebar = app[sidebar_start:sidebar_end]
'''
new='''    sidebar_start = app.find("// VALTREN SIDEBAR ARCHITECTURE START")
    sidebar_end = app.find("// VALTREN SIDEBAR ARCHITECTURE END", sidebar_start)
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Bloco canônico da Sidebar não localizado para validação")
    sidebar = app[sidebar_start:sidebar_end]
'''
changed=[]
for path in sorted(Path('scripts').glob('*.py')):
    if path.name in {'crm_sidebar_architecture.py','apply_sidebar_guard_fix.py'}:
        continue
    text=path.read_text(encoding='utf-8')
    if old in text:
        text=text.replace(old,new)
        path.write_text(text,encoding='utf-8')
        changed.append(path.as_posix())
if not changed:
    raise RuntimeError('Nenhum guard legado de Sidebar encontrado para corrigir')
print('Sidebar validation guards updated:', ', '.join(changed))
