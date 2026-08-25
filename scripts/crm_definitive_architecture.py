from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-definitive-architecture-v1"
JS_START = "  // VALTREN CRM DEFINITIVE ARCHITECTURE START\n"
JS_END = "  // VALTREN CRM DEFINITIVE ARCHITECTURE END\n"
CSS_MARKER = "/* VALTREN CRM DEFINITIVE ARCHITECTURE */"

JS_BLOCK = r'''  // VALTREN CRM DEFINITIVE ARCHITECTURE START
  function crmArchitecturePlaceholderPage(active,sub,title,description='Estrutura do módulo preparada para a próxima etapa de implementação.'){
    const body=crmFidelityPanel(title,'',crmRefEmpty('Módulo preparado para implementação','A estrutura e a rota já fazem parte da arquitetura oficial do Sistema Interno.'));
    return crmFidelityPage(active,sub,title,description,'',body);
  }

  function crmArchitectureIntegrationsPage(){
    const body=`${crmFidelityPanel('Integrações','Conecte e configure as integrações do Sistema Interno.',`<div class="crm-ref-integration-grid">${['Soundcharts','Meta','Google Ads','TikTok Ads','YouTube Ads','Spotify Ads'].map(x=>`<article><strong>${x}</strong><span class="crm-ref-badge">Não conectado</span><button>Configurar</button></article>`).join('')}</div>`)}${crmFidelityPanel('Distribuidoras','Conecte contas de distribuidoras quando aplicável.',crmRefEmpty('Nenhuma distribuidora conectada'))}`;
    return crmFidelityPage('settings','integrations','Integrações','Gerencie as integrações do sistema','',body);
  }

  function crmRelSidebar(active='relationships',sub=''){
    const nav=(href,label,ic,key)=>`<a class="${active===key?'active':''}" href="${href}">${icon(ic,18)}<span>${label}</span></a>`;
    const subgroup=(key,label,ic,items)=>`<details class="crm-nav-group" ${active===key?'open':''}><summary>${icon(ic,18)}<span>${label}</span><b>⌄</b></summary><div>${items.map(([id,text,href])=>`<a class="${active===key&&sub===id?'active':''}" href="${href}">${text}</a>`).join('')}</div></details>`;
    const finance=[
      ['finance','Transações','#/crm/financeiro'],
      ['accounting','Contabilidade','#/crm/financeiro/accounting'],
      ['invoices','Notas Fiscais','#/crm/financeiro/invoices'],
      ['rateios','Rateios','#/crm/financeiro/rateios'],
      ['participacoes','Participações','#/crm/financeiro/participacoes'],
      ['repasses','Repasses','#/crm/financeiro/repasses']
    ];
    const marketing=[
      ['overview','Visão Geral','#/crm/marketing'],
      ['campaigns','Campanhas','#/crm/marketing/campaigns'],
      ['calendar','Calendário','#/crm/marketing/calendar'],
      ['metrics','Métricas','#/crm/marketing/metrics'],
      ['tasks','Tarefas','#/crm/marketing/tasks']
    ];
    const business=[
      ['products','Produtos','#/crm/negocios'],
      ['services','Serviços','#/crm/negocios/servicos'],
      ['units','Unidades de Negócio','#/crm/negocios/unidades']
    ];
    const settings=[
      ['settings','Configurações','#/crm/configuracoes'],
      ['profile','Meu Perfil','#/crm/configuracoes/profile'],
      ['integrations','Integrações','#/crm/configuracoes/integracoes'],
      ['audit','Audit Trail','#/crm/configuracoes/audit'],
      ['users','Usuários','#/crm/configuracoes/users'],
      ['billing','Billing','#/crm/configuracoes/billing']
    ];
    const administration=[
      ['structure','Estrutura Organizacional','#/crm/administracao'],
      ['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas']
    ];
    const legal=`<details class="crm-nav-group crm-nav-legal" ${active==='legal'?'open':''}><summary>${icon('file',18)}<span>Jurídico</span><b>⌄</b></summary><div>
      <a class="${active==='legal'&&sub==='matters'?'active':''}" href="#/crm/juridico">Assuntos Jurídicos</a>
      <details class="crm-nav-subgroup" ${active==='legal'&&String(sub).startsWith('contracts')?'open':''}><summary><span>Contratos</span><b>⌄</b></summary><div>
        <a class="${active==='legal'&&sub==='contracts'?'active':''}" href="#/crm/juridico/contratos">Contratos</a>
        <a class="${active==='legal'&&sub==='contracts-templates'?'active':''}" href="#/crm/juridico/contratos/templates">Templates</a>
        <a class="${active==='legal'&&sub==='contracts-variables'?'active':''}" href="#/crm/juridico/contratos/variaveis">Variáveis</a>
      </div></details>
      <a class="${active==='legal'&&sub==='compliance'?'active':''}" href="#/crm/juridico/compliance">Compliance e Políticas</a>
      <a class="${active==='legal'&&sub==='ip'?'active':''}" href="#/crm/juridico/propriedade-intelectual">Propriedade Intelectual</a>
      <a class="${active==='legal'&&sub==='corporate'?'active':''}" href="#/crm/juridico/societario">Societário</a>
    </div></details>`;
    return `<aside class="crm-sidebar"><a class="crm-brand" href="#/crm/dashboard" aria-label="Valtren Sistema Interno"><img src="assets/valtren-mark.svg" alt="Valtren Solutions"><span><strong>VALTREN</strong><small>Sistema Interno</small></span></a><nav class="crm-nav" aria-label="Módulos do Sistema Interno">
      ${nav('#/crm/dashboard','Dashboard','layers','dashboard')}
      ${nav('#/crm/relationships','CRM','users','relationships')}
      ${nav('#/crm/agenda','Agenda','calendar','agenda')}
      ${subgroup('accounting','Financeiro','database',finance)}
      ${legal}
      ${nav('#/crm/valtrenchat','ValtrenChat','message','valtrenchat')}
      ${nav('#/crm/rh','RH','users','hr')}
      ${subgroup('marketing','Marketing','globe',marketing)}
      ${subgroup('business','Negócios','layers',business)}
      ${nav('#/crm/relatorios','Relatórios','file','reports')}
      ${subgroup('settings','Configurações','settings',settings)}
      ${subgroup('admin','Administração','settings',administration)}
    </nav></aside>`;
  }

  function crmReferenceRoute(path){
    if(path==='/crm/financeiro')return crmRefFinancePage();
    if(path==='/crm/financeiro/accounting')return crmRefAccountingPage();
    if(path==='/crm/financeiro/invoices')return crmRefInvoicesPage();
    if(path==='/crm/financeiro/rules')return crmRefCategorizationRulesPage();
    if(path==='/crm/financeiro/categories')return crmRefCategoriesPage();
    if(path==='/crm/financeiro/rateios')return crmArchitecturePlaceholderPage('accounting','rateios','Rateios');
    if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage('accounting','participacoes','Participações');
    if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage('accounting','repasses','Repasses');

    if(path==='/crm/juridico')return crmArchitecturePlaceholderPage('legal','matters','Assuntos Jurídicos');
    if(path==='/crm/juridico/contratos')return crmArchitecturePlaceholderPage('legal','contracts','Contratos');
    if(path==='/crm/juridico/contratos/templates')return crmArchitecturePlaceholderPage('legal','contracts-templates','Templates');
    if(path==='/crm/juridico/contratos/variaveis')return crmArchitecturePlaceholderPage('legal','contracts-variables','Variáveis');
    if(path==='/crm/juridico/compliance')return crmArchitecturePlaceholderPage('legal','compliance','Compliance e Políticas');
    if(path==='/crm/juridico/propriedade-intelectual')return crmArchitecturePlaceholderPage('legal','ip','Propriedade Intelectual');
    if(path==='/crm/juridico/societario')return crmArchitecturePlaceholderPage('legal','corporate','Societário');

    if(path==='/crm/rh')return crmArchitecturePlaceholderPage('hr','hr','RH');

    if(path==='/crm/marketing')return crmRefMarketingOverview();
    if(path==='/crm/marketing/campaigns')return crmRefCampaignsPage();
    if(path==='/crm/marketing/calendar')return crmRefCalendarPage();
    if(path==='/crm/marketing/metrics')return crmRefMetricsPage();
    if(path==='/crm/marketing/tasks')return crmRefTasksPage();
    if(path==='/crm/marketing/briefings')return crmRefBriefingsPage();
    if(path==='/crm/marketing/ai')return crmRefMarketingOverview();

    if(path==='/crm/negocios')return crmArchitecturePlaceholderPage('business','products','Produtos');
    if(path==='/crm/negocios/servicos')return crmArchitecturePlaceholderPage('business','services','Serviços');
    if(path==='/crm/negocios/unidades')return crmArchitecturePlaceholderPage('business','units','Unidades de Negócio');

    if(path==='/crm/valtrenchat'||path==='/crm/musicchat')return crmRefValtrenChatPage();
    if(path==='/crm/relatorios')return crmRefReportsPage();

    if(path==='/crm/configuracoes')return crmRefSettingsPage();
    if(path==='/crm/configuracoes/profile')return crmRefProfilePage();
    if(path==='/crm/configuracoes/integracoes')return crmArchitectureIntegrationsPage();
    if(path==='/crm/configuracoes/audit')return crmRefAuditPage();
    if(path==='/crm/configuracoes/users')return crmRefUsersPage();
    if(path==='/crm/configuracoes/billing')return crmRefBillingPage();

    if(path==='/crm/administracao')return crmArchitecturePlaceholderPage('admin','structure','Estrutura Organizacional');
    if(path==='/crm/administracao/patrimonio-licencas')return crmArchitecturePlaceholderPage('admin','assets','Patrimônio e Licenças');
    return null;
  }
  // VALTREN CRM DEFINITIVE ARCHITECTURE END
'''

CSS_PATCH = r'''
/* VALTREN CRM DEFINITIVE ARCHITECTURE */
.crm-sidebar .crm-nav-subgroup{
  margin:2px 0;
  border:0;
  background:transparent;
}
.crm-sidebar .crm-nav-subgroup>summary{
  list-style:none;
  cursor:pointer;
  display:flex;
  align-items:center;
  gap:8px;
  min-height:34px;
  padding:7px 12px 7px 30px;
  font-size:inherit;
  font-weight:inherit;
}
.crm-sidebar .crm-nav-subgroup>summary::-webkit-details-marker{display:none;}
.crm-sidebar .crm-nav-subgroup>summary>b{margin-left:auto;font-size:10px;}
.crm-sidebar .crm-nav-subgroup>div{display:grid;}
.crm-sidebar .crm-nav-subgroup>div>a{padding-left:48px!important;}
'''


def apply_crm_definitive_architecture() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")

    # Remove a prior execution of this final architecture patch.
    app = re.sub(
        r"\n?  // VALTREN CRM DEFINITIVE ARCHITECTURE START\n.*?  // VALTREN CRM DEFINITIVE ARCHITECTURE END\n",
        "\n",
        app,
        flags=re.S,
    )

    # The sidebar owns these destinations; avoid duplicate tabs inside Configurações.
    app = app.replace(
        "const tabs=[['company','Empresa'],['automations','Automações'],['security','Segurança'],['integrations','Integrações'],['public','Cadastro Público'],['billing','Billing'],['users','Usuários']];",
        "const tabs=[['company','Empresa'],['automations','Automações'],['security','Segurança'],['public','Cadastro Público']];",
    )

    # Route all definitive modules through the reference router in every render path.
    old_route_tail = "path.startsWith('/crm/configuracoes')"
    new_route_tail = "(path.startsWith('/crm/configuracoes') || path.startsWith('/crm/juridico') || path === '/crm/rh' || path.startsWith('/crm/negocios') || path.startsWith('/crm/administracao'))"
    if old_route_tail not in app:
        raise RuntimeError("Âncora de roteamento de Configurações não encontrada")
    app = app.replace(old_route_tail, new_route_tail)

    anchor = "  function contactPage(query)"
    if anchor not in app:
        raise RuntimeError("Âncora contactPage ausente para arquitetura definitiva")
    app = app.replace(anchor, JS_BLOCK.rstrip() + "\n\n" + anchor, 1)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM DEFINITIVE ARCHITECTURE \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    # Structural guardrails: fail the build instead of silently publishing an incomplete sidebar.
    required = [
        "Rateios", "Participações", "Repasses", "Assuntos Jurídicos", "Compliance e Políticas",
        "Propriedade Intelectual", "Societário", "ValtrenChat", "RH", "Unidades de Negócio",
        "Meu Perfil", "Integrações", "Audit Trail", "Usuários", "Billing",
        "Estrutura Organizacional", "Patrimônio e Licenças",
    ]
    missing = [label for label in required if label not in JS_BLOCK]
    if missing:
        raise RuntimeError(f"Arquitetura definitiva incompleta: {missing}")

    print("Arquitetura definitiva do Sistema Interno aplicada ao sidebar e às rotas.")
    return 1


if __name__ == "__main__":
    apply_crm_definitive_architecture()
