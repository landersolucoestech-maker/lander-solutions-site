from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-definitive-architecture-v3"

JS_BLOCK = r'''  // VALTREN CRM DEFINITIVE ARCHITECTURE START
  function crmArchitecturePlaceholderPage(active,sub,title,description='Estrutura do módulo preparada para a próxima etapa de implementação.'){
    const body=crmFidelityPanel(title,'',crmRefEmpty('Módulo preparado para implementação','A estrutura e a rota já fazem parte da arquitetura oficial do Sistema Interno.'));
    return crmFidelityPage(active,sub,title,description,'',body);
  }

  function crmArchitectureBreadcrumb(items){
    return `<nav class="crm-architecture-breadcrumb" aria-label="Breadcrumb">${items.map((item,index)=>{
      const last=index===items.length-1;
      return `${index?'<span>/</span>':''}${last?`<strong>${esc(item.label)}</strong>`:`<a href="${item.href}">${esc(item.label)}</a>`}`;
    }).join('')}</nav>`;
  }

  function crmAdminPlaceholderPage(sub,title,description='Estrutura administrativa preparada para a próxima etapa de implementação.'){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Administração',href:'#/crm/administracao'},{label:title,href:sub==='structure'?'#/crm/administracao':'#/crm/administracao/patrimonio-licencas'}]);
    const body=crmFidelityPanel(title,'',crmRefEmpty('Módulo preparado para implementação','A estrutura e a rota já fazem parte da arquitetura oficial do Sistema Interno.'));
    return crmFidelityPage('admin',sub,title,description,'',`${breadcrumb}${body}`);
  }

  function crmCanonicalSettingsPage(){
    const allowed=['general','company','notifications','preferences'];
    const tab=allowed.includes(state.crmRefSettingsTab)?state.crmRefSettingsTab:'general';
    let body='';
    if(tab==='general')body=crmFidelityPanel('Geral','Parâmetros gerais do Sistema Interno',`<div class="crm-ref-form-grid">${crmRefSelect('Idioma','language',[['pt-BR','Português (Brasil)']])}${crmRefSelect('Fuso horário','timezone',[['America/Sao_Paulo','America/Sao_Paulo']])}${crmRefSelect('Moeda','currency',[['BRL','Real brasileiro (BRL)']])}${crmRefSelect('Formato de data','dateFormat',[['dd/mm/yyyy','DD/MM/AAAA']])}</div>`);
    if(tab==='company')body=`<div class="crm-ref-grid settings-company-grid">${crmFidelityPanel('Identidade Visual','Identidade institucional utilizada nas áreas internas',`<div class="crm-ref-logo-upload"><img src="assets/valtren-logo.svg" alt="Valtren"><h2>VALTREN SOLUTIONS</h2><button>Alterar logo</button></div>`)}${crmFidelityPanel('Empresa','Dados institucionais e cadastrais',`<div class="crm-ref-form-grid">${crmRefField('Razão Social','legalName')}${crmRefField('Nome Fantasia','tradeName','text','VALTREN SOLUTIONS')}${crmRefField('CNPJ','cnpj')}${crmRefField('Endereço Completo','address')}${crmRefField('Telefone','phone')}${crmRefField('E-mail','companyEmail','email')}${crmRefField('Responsável','responsible')}</div>`)}</div>`;
    if(tab==='notifications')body=crmFidelityPanel('Notificações','Canais, frequência, tipos, horários e eventos do sistema',`<div class="crm-ref-settings-blocks"><article><h4>Canais</h4><label><input type="checkbox" checked> Notificações no sistema</label><label><input type="checkbox"> E-mail</label></article><article><h4>Frequência</h4><label>Frequência de envio<select><option>Imediato</option><option>Diário</option><option>Semanal</option></select></label><label>Horário preferido<input type="time"></label></article><article><h4>Eventos</h4><label><input type="checkbox" checked> Eventos operacionais</label><label><input type="checkbox" checked> Eventos financeiros</label><label><input type="checkbox" checked> Alertas do sistema</label></article></div>`);
    if(tab==='preferences')body=crmFidelityPanel('Preferências do Sistema','Comportamentos, padrões e parâmetros globais',`<div class="crm-ref-form-grid">${crmRefSelect('Página inicial','homeModule',[['dashboard','Dashboard']])}${crmRefSelect('Paginação padrão','pageSize',[['10','10 itens'],['25','25 itens'],['50','50 itens']])}${crmRefSelect('Confirmação para exclusões','deleteConfirm',[['enabled','Obrigatória']])}</div>`);
    const tabs=`<nav class="crm-ref-ai-tabs crm-fidelity-local-tabs">${[['general','Geral'],['company','Empresa'],['notifications','Notificações'],['preferences','Preferências do Sistema']].map(([id,label])=>`<button class="${tab===id?'active':''}" data-action="crm-ref-settings-tab" data-tab="${id}">${label}</button>`).join('')}</nav>`;
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Configurações',href:'#/crm/configuracoes'}]);
    return crmFidelityPage('settings','settings','Configurações','Parâmetros globais do Sistema Interno','',`${breadcrumb}${tabs}${body}`);
  }

  function crmCanonicalProfilePage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Meu Perfil',href:'#/crm/meu-perfil'}]);
    const body=`${crmFidelityPanel('Informações Pessoais','Seus dados e preferências pessoais',`<div class="crm-ref-profile-head"><div>AD</div><div><h2>${esc(state.crmUserName||'Administrador')}</h2><p>Usuário</p></div><button>Alterar foto</button><button>Remover</button></div><div class="crm-ref-form-grid">${crmRefField('Nome Completo','name','text','',state.crmUserName||'Administrador')}${crmRefField('E-mail','email','email')}${crmRefField('Telefone','phone')}${crmRefField('Departamento','department','text','Selecione o departamento')}${crmRefField('Cargo','role','text','Selecione o cargo')}</div>`)}${crmFidelityPanel('Segurança da Minha Conta','Senha, MFA e sessões próprias',`<div class="crm-ref-form-grid">${crmRefField('Senha Atual','currentPassword','password')}${crmRefField('Nova Senha','newPassword','password')}${crmRefField('Confirmar Nova Senha','confirmPassword','password')}</div><div class="crm-ref-settings-blocks"><article><h4>MFA</h4><p>Gerencie a autenticação multifator da sua conta.</p></article><article><h4>Sessões</h4><button>Encerrar outras sessões</button></article></div>`)}`;
    return crmFidelityPage('','profile','Meu Perfil','Gerencie seus dados e segurança pessoal','',`${breadcrumb}${body}`);
  }

  function crmAdminAccessPage(){
    crmRefEnsureState();
    const rows=state.crmRefUsers||[];
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Administração',href:'#/crm/administracao'},{label:'Acessos e Permissões',href:'#/crm/administracao/acessos-permissoes'}]);
    const actions=`<button class="primary" data-action="crm-ref-open" data-kind="user">${crmRefIcon('plus')} Convidar usuário</button>`;
    const filters=crmRefToolbar(`<label class="crm-ref-search">${icon('search',14)}<input placeholder="Buscar por nome ou e-mail…"></label><select><option>Todos os papéis</option></select><select><option>Todos os status</option><option>Ativo</option><option>Inativo</option><option>Suspenso</option></select>`);
    const k=`<div class="crm-ref-kpis four">${crmRefKpi('Usuários Ativos',rows.length)}${crmRefKpi('Convites Pendentes',0)}${crmRefKpi('Papéis',0)}${crmRefKpi('Permissões',0)}</div>`;
    const table=crmFidelityTable('Usuários e Acessos','Usuários, papéis, status e controle de acesso',['Nome','Papel','Telefone','Criado em','Status','Ações'],'Nenhum usuário encontrado');
    const roles=crmFidelityPanel('Papéis e Permissões','Defina papéis, permissões, escopos, restrições e unidades autorizadas',crmRefEmpty('Nenhum papel disponível','Os papéis e permissões serão sincronizados com a camada de autorização do sistema.'),'<button>Criar Papel</button>');
    return crmFidelityPage('admin','access','Acessos e Permissões','Gerencie usuários, convites, papéis, permissões, MFA, sessões e status de acesso',actions,`${breadcrumb}${k}${filters}${table}${roles}`);
  }

  function crmAdminAuditPage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Administração',href:'#/crm/administracao'},{label:'Auditoria',href:'#/crm/administracao/auditoria'}]);
    const filters=crmFidelityPanel('Filtros','',`${crmRefToolbar(`<input type="date" placeholder="Data início"><input type="date" placeholder="Data fim"><label class="crm-ref-search">${icon('search',14)}<input placeholder="Pesquisar por ação, ator, ID ou correlação…"></label><select><option>Entidade</option></select><select><option>Tipo de ação</option></select><button>Limpar filtros</button>`)}`,'<button>Atualizar</button>');
    const table=crmFidelityTable('Eventos de Auditoria','Registro somente leitura das alterações e ações do sistema',['','Timestamp','Ator','Papel','Ação','Entidade','ID','Método'],'Nenhum evento encontrado');
    return crmFidelityPage('admin','audit','Auditoria','Histórico somente leitura das alterações e ações do sistema','',`${breadcrumb}${filters}${table}`);
  }

  function crmAdminIntegrationsPage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Administração',href:'#/crm/administracao'},{label:'Integrações',href:'#/crm/administracao/integracoes'}]);
    const body=`${crmFidelityPanel('Integrações','Conecte e configure as integrações do Sistema Interno.',`<div class="crm-ref-integration-grid">${['Soundcharts','Meta','Google Ads','TikTok Ads','YouTube Ads','Spotify Ads'].map(x=>`<article><strong>${x}</strong><span class="crm-ref-badge">Não conectado</span><button>Configurar</button></article>`).join('')}</div>`)}${crmFidelityPanel('Distribuidoras','Conecte contas de distribuidoras quando aplicável.',crmRefEmpty('Nenhuma distribuidora conectada'))}`;
    return crmFidelityPage('admin','integrations','Integrações','Gerencie as integrações administrativas do Sistema Interno','',`${breadcrumb}${body}`);
  }

  function crmLegacyRoute(canonicalHash,render){
    if(window.location.hash!==canonicalHash)history.replaceState(null,'',canonicalHash);
    return render();
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
    const administration=[
      ['structure','Estrutura Organizacional','#/crm/administracao'],
      ['assets','Patrimônio e Licenças','#/crm/administracao/patrimonio-licencas'],
      ['access','Acessos e Permissões','#/crm/administracao/acessos-permissoes'],
      ['audit','Auditoria','#/crm/administracao/auditoria'],
      ['integrations','Integrações','#/crm/administracao/integracoes']
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
      ${nav('#/crm/configuracoes','Configurações','settings','settings')}
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

    if(path==='/crm/configuracoes')return crmCanonicalSettingsPage();
    if(path==='/crm/meu-perfil')return crmCanonicalProfilePage();

    if(path==='/crm/administracao')return crmAdminPlaceholderPage('structure','Estrutura Organizacional');
    if(path==='/crm/administracao/patrimonio-licencas')return crmAdminPlaceholderPage('assets','Patrimônio e Licenças');
    if(path==='/crm/administracao/acessos-permissoes')return crmAdminAccessPage();
    if(path==='/crm/administracao/auditoria')return crmAdminAuditPage();
    if(path==='/crm/administracao/integracoes')return crmAdminIntegrationsPage();

    if(path==='/crm/configuracoes/profile')return crmLegacyRoute('#/crm/meu-perfil',crmCanonicalProfilePage);
    if(path==='/crm/configuracoes/users')return crmLegacyRoute('#/crm/administracao/acessos-permissoes',crmAdminAccessPage);
    if(path==='/crm/configuracoes/audit')return crmLegacyRoute('#/crm/administracao/auditoria',crmAdminAuditPage);
    if(path==='/crm/configuracoes/integracoes')return crmLegacyRoute('#/crm/administracao/integracoes',crmAdminIntegrationsPage);
    if(path==='/crm/configuracoes/billing')return crmLegacyRoute('#/crm/configuracoes',crmCanonicalSettingsPage);
    return null;
  }

  if(!window.__valtrenCanonicalAccountMenuBound){
    window.__valtrenCanonicalAccountMenuBound=true;
    document.addEventListener('click',(event)=>{
      const target=event.target.closest('[data-action="crm-header-account-item"]');
      if(!target)return;
      if(target.dataset.accountItem==='profile'){
        event.preventDefault();
        location.hash='#/crm/meu-perfil';
      }
      if(target.dataset.accountItem==='settings'){
        event.preventDefault();
        location.hash='#/crm/configuracoes';
      }
    });
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
.crm-architecture-breadcrumb{
  display:flex;
  align-items:center;
  gap:7px;
  margin:0 0 14px;
  color:#64748B;
  font-size:10px;
  font-weight:700;
}
.crm-architecture-breadcrumb a{color:#64748B;text-decoration:none;}
.crm-architecture-breadcrumb strong{color:#0B1D3A;}
'''


def apply_crm_definitive_architecture() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")

    app = re.sub(
        r"\n?  // VALTREN CRM DEFINITIVE ARCHITECTURE START\n.*?  // VALTREN CRM DEFINITIVE ARCHITECTURE END\n",
        "\n",
        app,
        flags=re.S,
    )

    app = app.replace(
        "const CRM_REF_SETTINGS_SUB=[['settings','Configurações'],['users','Usuários'],['profile','Meu Perfil'],['audit','Audit Trail'],['billing','Billing']];",
        "const CRM_REF_SETTINGS_SUB=[['settings','Configurações']];",
    )
    app = app.replace(
        "function crmFidelitySettingsSub(){return [['settings','Configurações'],['users','Usuários'],['profile','Meu Perfil'],['audit','Audit Trail'],['billing','Billing']];}",
        "function crmFidelitySettingsSub(){return [['settings','Configurações']];}",
    )
    app = app.replace(
        "const tabs=[['company','Empresa'],['automations','Automações'],['security','Segurança'],['integrations','Integrações'],['public','Cadastro Público'],['billing','Billing'],['users','Usuários']];",
        "const tabs=[['company','Empresa']];",
    )

    app = app.replace(
        '<button type="button" data-action="crm-header-account-item" data-account-item="profile">Perfil</button>',
        '<button type="button" data-action="crm-header-account-item" data-account-item="profile">Meu Perfil</button>',
    )

    old_route_tail = "path.startsWith('/crm/configuracoes')"
    new_route_tail = "(path.startsWith('/crm/configuracoes') || path === '/crm/meu-perfil' || path.startsWith('/crm/juridico') || path === '/crm/rh' || path.startsWith('/crm/negocios') || path.startsWith('/crm/administracao'))"
    if old_route_tail not in app:
        raise RuntimeError("Âncora de roteamento de Configurações não encontrada")
    app = app.replace(old_route_tail, new_route_tail)

    anchor = "  function contactPage(query)"
    if anchor not in app:
        raise RuntimeError("Âncora contactPage ausente para arquitetura definitiva")
    app = app.replace(anchor, JS_BLOCK.rstrip() + "\n\n" + anchor, 1)

    sidebar_source = JS_BLOCK.split("  function crmRelSidebar", 1)[1].split("  function crmReferenceRoute", 1)[0]
    forbidden_sidebar = ["Meu Perfil", "Audit Trail", "Usuários", "Billing"]
    leaked = [label for label in forbidden_sidebar if label in sidebar_source]
    if leaked:
        raise RuntimeError(f"Itens proibidos ainda presentes no sidebar definitivo: {leaked}")

    required_admin = ["Estrutura Organizacional", "Patrimônio e Licenças", "Acessos e Permissões", "Auditoria", "Integrações"]
    missing_admin = [label for label in required_admin if label not in sidebar_source]
    if missing_admin:
        raise RuntimeError(f"Administração incompleta: {missing_admin}")
    if "subgroup('settings','Configurações'" in sidebar_source:
        raise RuntimeError("Configurações ainda está sendo materializado como grupo")
    if "nav('#/crm/configuracoes','Configurações'" not in sidebar_source:
        raise RuntimeError("Configurações não está materializado como módulo único")

    required_routes = [
        "#/crm/meu-perfil",
        "/crm/administracao/acessos-permissoes",
        "/crm/administracao/auditoria",
        "/crm/administracao/integracoes",
    ]
    missing_routes = [route for route in required_routes if route not in JS_BLOCK]
    if missing_routes:
        raise RuntimeError(f"Rotas canônicas ausentes: {missing_routes}")

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

    print("Configurações, Meu Perfil e Administração corrigidos conforme a arquitetura oficial.")
    return 1


if __name__ == "__main__":
    apply_crm_definitive_architecture()
