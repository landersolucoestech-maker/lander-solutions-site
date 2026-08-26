from pathlib import Path

for name in [
    'scripts/crm_reference_fidelity_fix.js.part01',
    'scripts/crm_reference_fidelity_fix.js.part03',
    'scripts/crm_reference_fidelity_fix.js.part04',
]:
    path=Path(name)
    text=path.read_text(encoding='utf-8')
    path.write_text(text.rstrip()+'\n',encoding='utf-8')

Path('scripts/crm_reference_fidelity_fix.js.part02').write_text('',encoding='utf-8')
print('Migrated fidelity part endings normalized for diff hygiene.')
