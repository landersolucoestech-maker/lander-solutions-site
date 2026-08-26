from pathlib import Path

path=Path('scripts/test_crm_sidebar_architecture.js')
text=path.read_text(encoding='utf-8')
anchor="const review=read('crm_product_system_review.py');\n"
helper="const ownsSidebar=(source)=>/^[ \\t]*function[ \\t]+crmRelSidebar[ \\t]*[(]/m.test(source);\nconst ownerPayloadMatch=owner.match(/JS_BLOCK = r'''([^]*?)'''\\n\\nCSS_PATCH/);\nmust(ownerPayloadMatch,'sidebar owner payload must be statically identifiable');\nconst ownerPayload=ownerPayloadMatch[1];\n"
if anchor not in text:
    raise RuntimeError('sidebar test helper anchor not found')
text=text.replace(anchor,anchor+helper,1)
for old,new in [
    ("must(!relationships.includes('function crmRelSidebar'),'relationships still owns sidebar');","must(!ownsSidebar(relationships),'relationships still owns sidebar');"),
    ("must(!fidelity.includes('function crmRelSidebar'),'fidelity still owns sidebar');","must(!ownsSidebar(fidelity),'fidelity still owns sidebar');"),
    ("must(!definitive.includes('function crmRelSidebar'),'definitive architecture still owns sidebar');","must(!ownsSidebar(definitive),'definitive architecture still owns sidebar');"),
    ("must(owner.includes(\"nav('#/crm/marketing','Marketing'\"),'Marketing must remain first-level');","must(ownerPayload.includes(\"nav('#/crm/marketing','Marketing'\"),'Marketing must remain first-level');"),
    ("must(owner.includes(\"nav('#/crm/relatorios','Relatórios'\"),'Reports must remain');","must(ownerPayload.includes(\"nav('#/crm/relatorios','Relatórios'\"),'Reports must remain');"),
    ("['ValtrenChat','MusicChat',\"nav('#/crm/rh'\",'Administração'].forEach((token)=>must(!owner.includes(token),`sidebar owner still contains removed module: ${token}`));","['ValtrenChat','MusicChat',\"nav('#/crm/rh'\",'Administração'].forEach((token)=>must(!ownerPayload.includes(token),`sidebar payload still contains removed module: ${token}`));"),
]:
    if text.count(old)!=1:
        raise RuntimeError(f'ownership assertion anchor missing: {old}')
    text=text.replace(old,new,1)
path.write_text(text,encoding='utf-8')
print('Sidebar ownership source gate refined to emitted declarations and JS_BLOCK payload.')
