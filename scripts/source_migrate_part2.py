from pathlib import Path
import re

ROOT=Path('.')

def read(path): return (ROOT/path).read_text(encoding='utf-8')
def write(path,text): (ROOT/path).write_text(text,encoding='utf-8')
def sub_once(text,pattern,repl,label,flags=0):
    updated,count=re.subn(pattern,repl,text,count=1,flags=flags)
    if count!=1: raise RuntimeError(f'{label}: esperado 1 replacement, encontrado {count}')
    return updated

# 7) Definitive architecture owns routes/settings, but no longer owns Sidebar.
path = 'scripts/crm_definitive_architecture.py'
text = read(path)
text = sub_once(
    text,
    r"\n  function crmAdminPlaceholderPage\(.*?\n  \}\n\n  function crmSettingsCompanyBody",
    "\n  function crmSettingsCompanyBody",
    'admin placeholder helper',
    re.S,
)
sidebar_start = text.find("  function crmRelSidebar(active='relationships',sub=''){")
sidebar_end = text.find('  function crmReferenceRoute(path){', sidebar_start)
if sidebar_start < 0 or sidebar_end < 0:
    raise RuntimeError('definitive architecture sidebar block not found')
text = text[:sidebar_start] + text[sidebar_end:]
marketing_helper = r'''  function crmMarketingUnavailablePage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Marketing',href:'#/crm/marketing'}]);
    const body=crmFidelityPanel('Operação de Marketing','',crmRefEmpty('Marketing ainda não está conectado','Campanhas, calendário, métricas, publicações e anúncios dependem de persistência e integrações reais. Nenhuma campanha, atividade ou métrica externa é simulada.'),'<a class="crm-empty-action" href="#/crm/configuracoes?tab=integracoes">Ver integrações</a>');
    return crmFidelityPage('marketing','overview','Marketing','Planejamento preparado sem simular execução externa','',`${breadcrumb}${body}`);
  }

'''
anchor = '  function crmSettingsCompanyBody(){'
if anchor not in text:
    raise RuntimeError('settings anchor for marketing helper not found')
text = text.replace(anchor, marketing_helper + anchor, 1)
text = text.replace("    if(path==='/crm/rh')return crmArchitecturePlaceholderPage('hr','hr','RH');", "    if(path==='/crm/rh')return crmArchitecturePlaceholderPage('','hr','RH','Domínio de RH ainda não implementado. Pessoas e Organizações permanecem identidades canônicas e não são tratadas como RH.');")
marketing_block = """    if(path==='/crm/marketing')return crmRefMarketingOverview();\n    if(path==='/crm/marketing/campaigns')return crmRefCampaignsPage();\n    if(path==='/crm/marketing/calendar')return crmRefCalendarPage();\n    if(path==='/crm/marketing/metrics')return crmRefMetricsPage();\n    if(path==='/crm/marketing/tasks')return crmRefTasksPage();\n    if(path==='/crm/marketing/briefings')return crmRefBriefingsPage();\n    if(path==='/crm/marketing/ai')return crmRefMarketingOverview();"""
if marketing_block not in text:
    raise RuntimeError('marketing route block not found')
text = text.replace(marketing_block, "    if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();", 1)
text = text.replace("    if(path==='/crm/valtrenchat'||path==='/crm/musicchat')return crmRefValtrenChatPage();", "    if(path==='/crm/valtrenchat'||path==='/crm/musicchat')return crmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);")
text = text.replace("    if(path==='/crm/administracao')return crmAdminPlaceholderPage('structure','Estrutura Organizacional');\n    if(path==='/crm/administracao/patrimonio-licencas')return crmAdminPlaceholderPage('assets','Patrimônio e Licenças');", "    if(path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas')return crmArchitecturePlaceholderPage('','admin','Administração','Área administrativa ainda não implementada como domínio operacional. Configurações de acesso, auditoria e integrações permanecem em Configurações.');")
validate_start = text.find('    sidebar_source = JS_BLOCK.split')
validate_end = text.find('    settings_source =', validate_start)
if validate_start < 0 or validate_end < 0:
    raise RuntimeError('definitive sidebar validation block not found')
text = text[:validate_start] + "    if \"function crmRelSidebar\" in JS_BLOCK:\n        raise RuntimeError(\"Arquitetura definitiva não pode emitir crmRelSidebar; o owner é crm_sidebar_architecture.py\")\n\n" + text[validate_end:]
# Move sidebar-specific CSS to the dedicated owner and make architecture CSS bounded.
css_start = text.find("CSS_PATCH = r'''\n/* VALTREN CRM DEFINITIVE ARCHITECTURE */")
breadcrumb = text.find('.crm-architecture-breadcrumb{', css_start)
if css_start < 0 or breadcrumb < 0:
    raise RuntimeError('definitive CSS block not found')
prefix_end = text.find('\n', css_start) + 1
marker_line_end = text.find('\n', prefix_end) + 1
text = text[:marker_line_end] + text[breadcrumb:]
old_css_write = "    css = CSS.read_text(encoding=\"utf-8\")\n    css = re.sub(r\"\\n?/\\* VALTREN CRM DEFINITIVE ARCHITECTURE \\*/.*\\Z\", \"\", css, flags=re.S)\n    CSS.write_text(css.rstrip() + \"\\n\\n\" + CSS_PATCH.strip() + \"\\n\", encoding=\"utf-8\")"
new_css_write = "    css = CSS.read_text(encoding=\"utf-8\")\n    desired_css = CSS_PATCH.strip()\n    marker_at = css.find(\"/* VALTREN CRM DEFINITIVE ARCHITECTURE */\")\n    if marker_at < 0:\n        css = css.rstrip() + \"\\n\\n\" + desired_css + \"\\n\"\n    else:\n        next_marker = css.find(\"\\n/* \" , marker_at + len(\"/* VALTREN CRM DEFINITIVE ARCHITECTURE */\"))\n        end = len(css) if next_marker < 0 else next_marker + 1\n        prefix = css[:marker_at].rstrip()\n        suffix = css[end:].lstrip(\"\\n\")\n        css = prefix + \"\\n\\n\" + desired_css + \"\\n\" + ((\"\\n\" + suffix) if suffix else \"\")\n    CSS.write_text(css, encoding=\"utf-8\")"
if old_css_write not in text:
    raise RuntimeError('definitive CSS write block not found')
text = text.replace(old_css_write, new_css_write, 1)
text = text.replace('print("Configurações materializado com seis abas internas; Administração restrita a dois submódulos; Meu Perfil preservado no menu do usuário.")', 'print("Arquitetura de rotas e Configurações materializada sem ownership de Sidebar; Meu Perfil preservado no menu da conta.")')
write(path, text)
