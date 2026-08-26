from pathlib import Path

path=Path('scripts/crm_sidebar_architecture.py')
text=path.read_text(encoding='utf-8')
old='''.crm-nav-subgroup>div{
  width:100%;
  min-width:0;
  display:grid;'''
new='''.crm-nav-subgroup>div{
  width:auto;
  min-width:0;
  display:grid;'''
if text.count(old)!=1:
    raise SystemExit(f'expected one nested sidebar width rule, got {text.count(old)}')
path.write_text(text.replace(old,new,1),encoding='utf-8')
print('Nested Contracts submenu width now respects its indented containing block without horizontal overflow.')
