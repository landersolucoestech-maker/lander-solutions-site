from pathlib import Path

path=Path('scripts/source_migrate_part1.py')
text=path.read_text(encoding='utf-8')
start=text.find('# 1) CRM Relacionamentos')
end=text.find('# 2) Reference Modules',start)
if start<0 or end<0:
    raise RuntimeError('part1 CRM migration section not found')
replacement='''# 1) CRM Relacionamentos becomes a sidebar consumer. Remove fake seeds and the legacy sidebar declaration at source.\npath = 'scripts/crm_relationships_module.py'\ntext = read(path)\ntext = sub_once(\n    text,\n    r"  function crmRelEnsureState\\(\\)\\{.*?\\n  \\}\\n\\n  function crmRelSidebar\\(active='relationships'\\)\\{.*?\\n  \\}\\n\\n  function crmRelActions",\n    "  function crmRelEnsureState(){\\n    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];\\n    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];\\n  }\\n\\n  function crmRelActions",\n    'relationship fake seeds and legacy sidebar',\n    re.S,\n)\nif 'function crmRelSidebar' in text:\n    raise RuntimeError('relationships still contains crmRelSidebar')\nfor forbidden in ['Marina Costa','Aurora Tecnologia Ltda.','Grupo Horizonte','Rafael Nunes','Paulo Mendes','Fernanda Lima','Daniel Souza']:\n    if forbidden in text:\n        raise RuntimeError(f'fake relationship seed survived: {forbidden}')\nwrite(path, text)\n\n'''
path.write_text(text[:start]+replacement+text[end:],encoding='utf-8')
print('source_migrate_part1 CRM section normalized')
