from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-definitive-architecture-v4"

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
    const href=sub==='structure'?'#/crm/administracao':'#/crm/administracao/patrimonio-licencas';
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Administração',href:'#/crm/administracao'},{label:title,href}]);
    const body=crmFidelityPanel(title,'',crmRefEmpty('Módulo preparado para implementação','A estrutura e a rota já fazem parte da arquitetura oficial do Sistema Interno.'));
    return crmFidelityPage('admin',sub,title,description,'',`${breadcrumb}${body}`);
  }

  function crmSettingsCompanyBody(){
    const identity=crmFidelityPanel('Identidade Visual','Identidade institucional utilizada nas áreas internas',`<div class="crm-ref-logo-upload"><img src="assets/valtren-logo.svg" alt="Valtren"><h2>VALTREN SOLUTIONS</h2><button>Alterar logo</button></div>`);
    const company=crmFidelityPanel('Empresa','Dados institucionais e cadastrais',`<div class="crm-ref-form-grid">${crmRefField('Razão Social','legalName')}${crmRefField('Nome Fantasia','tradeName','text','VALTREN SOLUTIONS')}${crmRefField('CNPJ','cnpj')}${crmRefField('Inscrição Estadual','stateRegistration')}${crmRefField('Inscrição Municipal','municipalRegistration')}${crmRefField('Endereço Completo','address')}${crmRefField('Telefone','phone')}${crmRefField('E-mail','companyEmail','email')}${crmRefField('Site','website','url')}${crmRefField('Responsável','responsible')}</div>`);
    const institutional=crmFidelityPanel('Parâmetros Institucionais','Idioma, moeda, fuso horário e formatos globais da empresa',`<div class="crm-ref-form-grid">${crmRefSelect('Idioma','language',[['pt-BR','Português (Brasil)']])}${crmRefSelect('Moeda','currency',[['BRL','Real brasileiro (BRL)']])}${crmRefSelect('Fuso horário','timezone',[['America/Sao_Paulo','America/Sao_Paulo']])}${crmRefSelect('Formato de data','dateFormat',[['dd/mm/yyyy','DD/MM/AAAA']])}</div>`);
    return `<div class="crm-ref-grid settings-company-grid">${identity}${company}</div>${institutional}`;
  }

  function crmSettingsNotificationsBody(){
    return crmFidelityPanel('Notificações','Preferências globais de canais, frequência, horários, eventos e alertas',`<div class="crm-ref-settings-blocks"><article><h4>Canais</h4><label><input type="checkbox" checked> Notificações no sistema</label><label><input type="checkbox"> E-mail</label></article><article><h4>Frequência e Horários</h4><label>Frequência de envio<select><option>Imediato</option><option>Diário</option><option>Semanal</option></select></label><label>Horário preferido<input type="time"></label></article><article><h4>Eventos e Alertas</h4><label><input type="checkbox" checked> Eventos operacionais</label><label><input type="checkbox" checked> Eventos financeiros</label><label><input type="checkbox" checked> Alertas do sistema</label></article></div>`);
  }

  function crmSettingsSecurityBody(){
    return crmFidelityPanel('Segurança','Políticas e parâmetros globais de segurança do Sistema Interno',`<div class="crm-ref-form-grid">${crmRefField('Tamanho mínimo de senha','passwordMinLength','number','12')}${crmRefSelect('Política de MFA','mfaPolicy',[['optional','Opcional'],['required','Obrigatório']])}${crmRefField('Duração da sessão (minutos)','sessionDuration','number','480')}${crmRefField('Tentativas antes do bloqueio','maxLoginAttempts','number','5')}${crmRefField('Duração do bloqueio (minutos)','lockDuration','number','30')}${crmRefSelect('Confirmação para ações destrutivas','destructiveConfirm',[['required','Obrigatória']])}</div><div class="crm-ref-settings-blocks"><article><h4>Autenticação</h4><p>Políticas globais de senha, MFA e proteção de acesso.</p></article><article><h4>Sessões</h4><p>Parâmetros de duração, expiração e segurança das sessões.</p></article><article><h4>Bloqueios</h4><p>Controle de tentativas, bloqueios e proteção contra acesso indevido.</p></article></div>`);
  }

  function crmSettingsIntegrationsBody(){
    const integrations=['Soundcharts','Meta','Google Ads','TikTok Ads','YouTube Ads','Spotify Ads'];
    const cards=integrations.map(x=>`<article><strong>${x}</strong><span class="crm-ref-badge">Não conectado</span><small>Conexão ainda não validada</small><button>Configurar</button></article>`).join('');
    return `${crmFidelityPanel('Integrações','Conecte e configure integrações externas do Sistema Interno.',`<div class="crm-ref-integration-grid">${cards}</div>`)}${crmFidelityPanel('Distribuidoras','Conecte contas de distribuidoras quando aplicável.',crmRefEmpty('Nenhuma distribuidora conectada'))}`;
  }

  function crmSettingsAuditBody(){
    const filters=crmFidelityPanel('Filtros','',`${crmRefToolbar(`<input type="date" placeholder="Data início"><input type="date" placeholder="Data fim"><label class="crm-ref-search">${icon('search',14)}<input placeholder="Pesquisar por usuário, ação, entidade, registro ou request ID…"></label><select><option>Módulo</option></select><select><option>Ação</option></select><button>Limpar filtros</button>`)}`,'<button>Atualizar</button>');
    const table=crmFidelityTable('Eventos de Auditoria','Registro somente leitura das alterações e ações do sistema',['Data e hora','Usuário','Módulo','Ação','Entidade','Registro','Método','Request ID','Origem'],'Nenhum evento encontrado');
    return `${filters}${table}`;
  }

  function crmSettingsUsersBody(){
    crmRefEnsureState();
    const rows=state.crmRefUsers||[];
    const actions=`<button class="primary" data-action="crm-ref-open" data-kind="user">${crmRefIcon('plus')} Convidar usuário</button>`;
    const filters=crmRefToolbar(`<label class="crm-ref-search">${icon('search',14)}<input placeholder="Buscar por nome ou e-mail…"></label><select><option>Todos os papéis</option></select><select><option>Todos os status</option><option>Ativo</option><option>Inativo</option><option>Suspenso</option></select>`);
    const k=`<div class="crm-ref-kpis four">${crmRefKpi('Usuários Ativos',rows.length)}${crmRefKpi('Convites Pendentes',0)}${crmRefKpi('Papéis',0)}${crmRefKpi('Permissões',0)}</div>`;
    const table=crmFidelityTable('Usuários','Usuários autorizados a utilizar o Sistema Interno',['Nome','Papel do Sistema','Telefone','Criado em','Status','Ações'],'Nenhum usuário encontrado');
    const roles=crmFidelityPanel('Papéis e Permissões','Papéis, permissões, escopos, restrições e unidades autorizadas',crmRefEmpty('Nenhum papel disponível','Crie ou sincronize papéis e permissões para controlar o acesso ao sistema.'),'<button>Criar Papel</button>');
    const access=crmFidelityPanel('Segurança por Usuário','MFA, sessões, ativação, suspensão e revogação de acesso',crmRefEmpty('Nenhuma configuração individual disponível'));
    return `${actions}${k}${filters}${table}${roles}${access}`;
  }

  function crmCanonicalSettingsPage(){
    const tabs=[
      ['empresa','Empresa'],
      ['notificacoes','Notificações'],
      ['seguranca','Segurança'],
      ['integracoes','Integrações'],
      ['auditoria','Auditoria'],
      ['usuarios','Usuários']
    ];
    const requested=routeInfo().query.get('tab')||'empresa';
    const tab=tabs.some(([id])=>id===requested)?requested:'empresa';
    const bodies={
      empresa:crmSettingsCompanyBody,
      notificacoes:crmSettingsNotificationsBody,
      seguranca:crmSettingsSecurityBody,
      integracoes:crmSettingsIntegrationsBody,
      auditoria:crmSettingsAuditBody,
      usuarios:crmSettingsUsersBody
    };
    const tabnav=`<nav class="crm-ref-ai-tabs crm-fidelity-local-tabs" aria-label="Seções de Configurações">${tabs.map(([id,label])=>`<button class="${tab===id?'active':''}" data-action="crm-ref-settings-tab" data-tab="${id}" aria-pressed="${tab===id?'true':'false'}">${label}</button>`).join('')}</nav>`;
    const currentLabel=tabs.find(([id])=>id===tab)?.[1]||'Empresa';
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Configurações',href:'#/crm/configuracoes'},{label:currentLabel,href:`#/crm/configuracoes?tab=${tab}`}]);
    return crmFidelityPage('settings','settings','Configurações','Parâmetros globais do Sistema Interno','',`${breadcrumb}${tabnav}${bodies[tab]()}`);
  }

  function crmCanonicalProfilePage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Meu Perfil',href:'#/crm/meu-perfil'}]);
    const body=`${crmFidelityPanel('Informações Pessoais','Seus dados e preferências pessoais',`<div class="crm-ref-profile-head"><div>AD</div><div><h2>${esc(state.crmUserName||'Administrador')}</h2><p>Usuário</p></div><button>Alterar foto</button><button>Remover</button></div><div class="crm-ref-form-grid">${crmRefField('Nome Completo','name','text','',state.crmUserName||'Administrador')}${crmRefField('E-mail','email','email')}${crmRefField('Telefone','phone')}${crmRefField('Departamento','department','text','Selecione o departamento')}${crmRefField('Cargo','role','text','Selecione o cargo')}</div>`)}${crmFidelityPanel('Segurança da Minha Conta','Senha, MFA e sessões próprias',`<div class="crm-ref-form-grid">${crmRefField('Senha Atual','currentPassword','password')}${crmRefField('Nova Senha','newPassword','password')}${crmRefField('Confirmar Nova Senha','confirmPassword','password')}</div><div class="crm-ref-settings-blocks"><article><h4>MFA</h4><p>Gerencie a autenticação multifator da sua conta.</p></article><article><h4>Sessões</h4><button>Encerrar outras sessões</button></article></div>`)}`;
    return crmFidelityPage('','profile','Meu Perfil','Gerencie seus dados e segurança pessoal','',`${breadcrumb}${body}`);
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

    if(path==='/crm/configuracoes/profile')return crmLegacyRoute('#/crm/meu-perfil',crmCanonicalProfilePage);
    if(path==='/crm/configuracoes/users'||path==='/crm/administracao/acessos-permissoes')return crmLegacyRoute('#/crm/configuracoes?tab=usuarios',crmCanonicalSettingsPage);
    if(path==='/crm/configuracoes/audit'||path==='/crm/administracao/auditoria')return crmLegacyRoute('#/crm/configuracoes?tab=auditoria',crmCanonicalSettingsPage);
    if(path==='/crm/configuracoes/integracoes'||path==='/crm/administracao/integracoes')return crmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);
    if(path==='/crm/configuracoes/billing')return crmLegacyRoute('#/crm/configuracoes?tab=empresa',crmCanonicalSettingsPage);
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
.crm-ref-integration-grid article small{display:block;margin-top:4px;color:#64748B;font-size:9px;}
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

    old_settings_handler = "if(a==='crm-ref-settings-tab'){state.crmRefSettingsTab=t.dataset.tab;renderCurrentWithoutReset();return;}"
    new_settings_handler = "if(a==='crm-ref-settings-tab'){const next=t.dataset.tab;if(routeInfo().path==='/crm/configuracoes'){location.hash=`#/crm/configuracoes?tab=${encodeURIComponent(next)}`;return;}state.crmRefSettingsTab=next;renderCurrentWithoutReset();return;}"
    if old_settings_handler not in app:
        raise RuntimeError("Handler de tabs de Configurações não encontrado")
    app = app.replace(old_settings_handler, new_settings_handler, 1)

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
    if "nav('#/crm/configuracoes','Configurações'" not in sidebar_source:
        raise RuntimeError("Configurações não está materializado como módulo único")
    if "subgroup('settings','Configurações'" in sidebar_source:
        raise RuntimeError("Configurações ainda está sendo materializado como grupo")

    forbidden_sidebar = ["Meu Perfil", "Acessos e Permissões", "Auditoria", "Integrações", "Usuários", "Billing"]
    leaked = [label for label in forbidden_sidebar if label in sidebar_source]
    if leaked:
        raise RuntimeError(f"Itens proibidos ainda presentes no sidebar definitivo: {leaked}")

    admin_source = sidebar_source.split("const administration=[", 1)[1].split("];", 1)[0]
    required_admin = ["Estrutura Organizacional", "Patrimônio e Licenças"]
    missing_admin = [label for label in required_admin if label not in admin_source]
    if missing_admin:
        raise RuntimeError(f"Administração incompleta: {missing_admin}")
    forbidden_admin = ["Acessos e Permissões", "Auditoria", "Integrações"]
    leaked_admin = [label for label in forbidden_admin if label in admin_source]
    if leaked_admin:
        raise RuntimeError(f"Administração contém itens revogados: {leaked_admin}")

    settings_source = JS_BLOCK.split("  function crmCanonicalSettingsPage", 1)[1].split("  function crmCanonicalProfilePage", 1)[0]
    expected_tabs = ["['empresa','Empresa']", "['notificacoes','Notificações']", "['seguranca','Segurança']", "['integracoes','Integrações']", "['auditoria','Auditoria']", "['usuarios','Usuários']"]
    positions = [settings_source.find(item) for item in expected_tabs]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise RuntimeError("Abas de Configurações ausentes ou fora da ordem oficial")
    if "['general','Geral']" in settings_source or "Preferências do Sistema" in settings_source:
        raise RuntimeError("Abas legadas Geral/Preferências do Sistema ainda presentes")

    required_routes = [
        "#/crm/meu-perfil",
        "#/crm/configuracoes?tab=empresa",
        "#/crm/configuracoes?tab=notificacoes",
        "#/crm/configuracoes?tab=seguranca",
        "#/crm/configuracoes?tab=integracoes",
        "#/crm/configuracoes?tab=auditoria",
        "#/crm/configuracoes?tab=usuarios",
    ]
    missing_routes = [route for route in required_routes if route not in JS_BLOCK and route not in new_settings_handler]
    if missing_routes:
        raise RuntimeError(f"Deep links canônicos ausentes: {missing_routes}")

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

    print("Configurações materializado com seis abas internas; Administração restrita a dois submódulos; Meu Perfil preservado no menu do usuário.")
    return 1


if __name__ == "__main__":
    apply_crm_definitive_architecture()
