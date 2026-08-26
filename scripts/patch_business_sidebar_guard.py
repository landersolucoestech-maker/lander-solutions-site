from pathlib import Path

path = Path('scripts/crm_business.py')
text = path.read_text(encoding='utf-8')
old = '''    sidebar_start = app.rfind("function crmRelSidebar")
    sidebar_end = app.find("function crmReferenceRoute", sidebar_start)
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Sidebar canônico não localizado")
    sidebar = app[sidebar_start:sidebar_end]
'''
new = '''    sidebar_start_marker = "// VALTREN SIDEBAR ARCHITECTURE START"
    sidebar_end_marker = "// VALTREN SIDEBAR ARCHITECTURE END"
    sidebar_start = app.find(sidebar_start_marker)
    sidebar_end = app.find(sidebar_end_marker, sidebar_start + len(sidebar_start_marker)) if sidebar_start >= 0 else -1
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Markers canônicos da Sidebar não localizados")
    sidebar = app[sidebar_start:sidebar_end]
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'expected exactly one legacy Business sidebar guard, got {count}')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('Business sidebar validation now uses canonical Sidebar Architecture markers.')
