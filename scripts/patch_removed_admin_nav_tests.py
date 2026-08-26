from pathlib import Path

replacements = {
    Path('scripts/test_crm_financial_transactions.js'): (
        "  test('88 Administração continua com dois itens',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),admin=app.slice(start,end);assert(admin.includes('Estrutura Organizacional'));assert(admin.includes('Patrimônio e Licenças'));assert(!admin.includes('Auditoria'));assert(!admin.includes('Integrações'));});",
        "  test('88 Administração permanece fora da sidebar canônica',()=>{const start=app.indexOf('VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));});",
    ),
    Path('scripts/test_crm_business_ui.js'): (
        "  test('Administração continua com dois submódulos',()=>{const start=app.lastIndexOf('const administration=['),end=app.indexOf('];',start),s=app.slice(start,end);assert(s.includes('Estrutura Organizacional'));assert(s.includes('Patrimônio e Licenças'));});",
        "  test('Administração permanece fora da sidebar canônica',()=>{const start=app.indexOf('VALTREN SIDEBAR ARCHITECTURE START'),end=app.indexOf('VALTREN SIDEBAR ARCHITECTURE END',start);assert(start>=0&&end>start);const sidebar=app.slice(start,end);for(const label of ['Administração','Estrutura Organizacional','Patrimônio e Licenças'])assert(!sidebar.includes(label));});",
    ),
}

for path, (old, new) in replacements.items():
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one obsolete Administration assertion, got {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f'{path}: Administration sidebar expectation aligned with canonical removal.')
