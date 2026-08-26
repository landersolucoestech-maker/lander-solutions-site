from pathlib import Path

path=Path('scripts/source_migrate_part1.py')
text=path.read_text(encoding='utf-8')

start=text.find('# 1) CRM Relacionamentos')
end=text.find('# 2) Reference Modules',start)
if start<0 or end<0:
    raise RuntimeError('part1 CRM migration section not found')
replacement='''# 1) CRM Relacionamentos becomes a sidebar consumer. Remove fake seeds and the legacy sidebar declaration at source.\npath = 'scripts/crm_relationships_module.py'\ntext = read(path)\ntext = sub_once(\n    text,\n    r"  function crmRelEnsureState\\(\\)\\{.*?\\n  \\}\\n\\n  function crmRelSidebar\\(active='relationships'\\)\\{.*?\\n  \\}\\n\\n  function crmRelActions",\n    "  function crmRelEnsureState(){\\n    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];\\n    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];\\n  }\\n\\n  function crmRelActions",\n    'relationship fake seeds and legacy sidebar',\n    re.S,\n)\nif 'function crmRelSidebar' in text:\n    raise RuntimeError('relationships still contains crmRelSidebar')\nfor forbidden in ['Marina Costa','Aurora Tecnologia Ltda.','Grupo Horizonte','Rafael Nunes','Paulo Mendes','Fernanda Lima','Daniel Souza']:\n    if forbidden in text:\n        raise RuntimeError(f'fake relationship seed survived: {forbidden}')\nwrite(path, text)\n\n'''
text=text[:start]+replacement+text[end:]

start=text.find('# 4) Canonical Parties')
end=text.find('# 5) Global review',start)
if start<0 or end<0:
    raise RuntimeError('part1 canonical parties migration section not found')
replacement='''# 4) Canonical Parties uses a CRM-owned function boundary, not the sidebar.\npath = 'scripts/crm_canonical_parties.py'\ntext = read(path)\nold_regex = r'r"  function crmRelEnsureState\\(\\)\\{.*?\\n  \\}\\n\\n  function crmRelSidebar"'\nnew_regex = r'r"  function crmRelEnsureState\\(\\)\\{.*?\\n  \\}\\n\\n  function crmRelActions"'\nif text.count(old_regex) != 1:\n    raise RuntimeError(f'canonical parties regex boundary unexpected: {text.count(old_regex)}')\ntext = text.replace(old_regex, new_regex, 1)\nold_replace = 'ensure_src.replace("\\n  }\\n\\n  function crmRelSidebar", "\\n    crmCanonicalEnsureFromLegacy();\\n  }\\n\\n  function crmRelSidebar", 1)'\nnew_replace = 'ensure_src.replace("\\n  }\\n\\n  function crmRelActions", "\\n    crmCanonicalEnsureFromLegacy();\\nn  }\\n\\n  function crmRelActions", 1)'\nif text.count(old_replace) != 1:\n    raise RuntimeError(f'canonical parties replace boundary unexpected: {text.count(old_replace)}')\ntext = text.replace(old_replace, new_replace, 1)\nwrite(path, text)\n\n'''
# Correct the escaped newline token before writing the migration script.
replacement=replacement.replace('\\n    crmCanonicalEnsureFromLegacy();\\n\\n  }','\\n    crmCanonicalEnsureFromLegacy();\\n  }')
text=text[:start]+replacement+text[end:]
path.write_text(text,encoding='utf-8')
print('source_migrate_part1 CRM and Canonical Parties sections normalized')
