from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260826-product-system-review-v2"
HEADER_START = "  // VALTREN CRM GLOBAL HEADER START\n"
HEADER_END = "  // VALTREN CRM GLOBAL HEADER END\n"


def _replace_function(source: str, name: str, replacement: str) -> str:
    start = source.find(f"  function {name}(")
    if start < 0:
        raise RuntimeError(f"Função materializada não encontrada: {name}")
    end = source.find("\n  function ", start + 3)
    if end < 0:
        raise RuntimeError(f"Limite da função materializada não encontrado: {name}")
    return source[:start] + replacement.rstrip() + source[end:]


HEADER_HELPERS = r'''  // VALTREN CRM GLOBAL HEADER START
  function crmGlobalLoadingScreen(){
    return `<div class="crm-global-loading" role="status" aria-live="polite"><div class="crm-global-loading-inner"><img src="assets/valtren-logo.svg" alt="Valtren Solutions"><div class="crm-global-loading-bar" aria-hidden="true"></div><span class="sr-only">Carregando</span></div></div>`;
  }

  function crmHeaderActions(context=''){
    const create = context === 'contacts'
      ? `<button class="crm-header-create" type="button" data-action="crm-rel-create" data-kind="contacts">${icon('plus',15)}<span>Novo Contato</span></button>`
      : context === 'leads'
        ? `<button class="crm-header-create" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>`
        : '';
    return `<div class="crm-header-actions">${create}<details class="crm-account-menu"><summary aria-label="Menu da conta"><span class="crm-account-icon" aria-hidden="true">${icon('user',16)}</span><span class="crm-account-copy"><strong>Conta</strong><small>Autenticação desativada</small></span><span class="crm-account-chevron" aria-hidden="true">⌄</span></summary><div class="crm-account-popover"><strong>Sem sessão ativa</strong><p>Este ambiente não possui autenticação ou usuário conectado. Nenhuma identidade é simulada.</p><a href="#/crm/configuracoes">Configurações</a></div></details></div>`;
  }

  function crmHeaderCloseMenus(){
    document.querySelectorAll('.crm-account-menu[open]').forEach((menu)=>menu.removeAttribute('open'));
  }
  // VALTREN CRM GLOBAL HEADER END
'''

EMPTY_RELATIONSHIP_STATE = r'''  function crmRelEnsureState(){
    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];
    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];
  }
'''

EMPTY_USERS = r'''  function crmFullUsers(){
    return [];
  }
'''

DASHBOARD = r'''  function crmDashboardPage(query){
    try { if (typeof crmCanonicalEnsureFromLegacy === 'function') crmCanonicalEnsureFromLegacy(); } catch (error) { console.error('Falha ao consolidar CRM no dashboard:', error); }
    const contacts = Array.isArray(state.crmRelContacts) ? state.crmRelContacts : [];
    const leads = Array.isArray(state.crmRelLeads) ? state.crmRelLeads : [];
    const clients = contacts.filter((item)=>{
      const roles = Array.isArray(item.canonicalRoles) ? item.canonicalRoles : [];
      const segment = String(item.segment || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
      return roles.includes('customer') || segment === 'cliente';
    });
    let transactions = [];
    try {
      if (typeof crmFinanceService === 'function') transactions = crmFinanceService().data.transactions || [];
      else if (state.crmFinancialTransactions && Array.isArray(state.crmFinancialTransactions.transactions)) transactions = state.crmFinancialTransactions.transactions;
    } catch (error) { console.error('Falha ao consolidar Financeiro no dashboard:', error); }
    const posted = transactions.filter((tx)=>tx && tx.status === 'posted' && !tx.isDemo);
    const revenue = posted.filter((tx)=>tx.financialNature === 'revenue').reduce((sum,tx)=>sum + Number(tx.amount || 0),0);
    const expenses = posted.filter((tx)=>tx.financialNature === 'expense').reduce((sum,tx)=>sum + Number(tx.amount || 0),0);
    const result = revenue - expenses;
    const pendingTransactions = transactions.filter((tx)=>tx && tx.status === 'pending' && !tx.isDemo).length;
    const openLeads = leads.filter((lead)=>!['converted','convertido'].includes(String(lead.stage || '').toLowerCase())).length;
    const money = (value)=>Number(value || 0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
    const kpi = (label,value,meta='')=>`<article class="crm-kpi"><span>${label}</span><strong>${value}</strong>${meta?`<small>${meta}</small>`:''}</article>`;
    const attention = [];
    if (openLeads) attention.push(`<a href="#/crm/relationships?tab=leads"><strong>${openLeads}</strong><span>lead${openLeads===1?'':'s'} em acompanhamento</span><small>Revisar pipeline comercial</small></a>`);
    if (pendingTransactions) attention.push(`<a href="#/crm/financeiro"><strong>${pendingTransactions}</strong><span>transaç${pendingTransactions===1?'ão':'ões'} pendente${pendingTransactions===1?'':'s'}</span><small>Classificar ou lançar no Financeiro</small></a>`);
    const attentionBody = attention.length ? `<div class="crm-dashboard-attention-grid">${attention.join('')}</div>` : `<div class="crm-empty-state"><strong>Nenhuma pendência consolidada</strong><p>O dashboard exibirá aqui apenas itens reais que exigirem atenção.</p></div>`;
    const noData = !contacts.length && !leads.length && !posted.length;
    return `<div class="crm-app-shell">${crmRelSidebar('dashboard','dashboard')}<main class="crm-main"><header class="crm-topbar"><div><span>Sistema Interno</span><h1>Dashboard</h1><p>Visão objetiva dos dados reais já registrados no sistema.</p></div>${crmHeaderActions('dashboard')}</header><section class="crm-workspace crm-dashboard-workspace" aria-label="Dashboard"><div class="crm-page-header"><div><h2>Visão geral</h2><p>Indicadores essenciais de CRM e Financeiro, sem duplicar os módulos operacionais.</p></div></div><div class="crm-kpi-grid crm-dashboard-kpis">${kpi('Contatos',contacts.length)}${kpi('Leads',leads.length)}${kpi('Clientes',clients.length)}${kpi('Receitas',money(revenue),'Transações lançadas')}${kpi('Despesas',money(expenses),'Transações lançadas')}${kpi('Resultado',money(result),'Receitas − despesas')}</div>${noData?`<section class="crm-panel"><div class="crm-empty-state"><strong>Ainda não há dados operacionais</strong><p>Cadastre contatos, leads ou transações reais para alimentar esta visão. O sistema não cria números fictícios para preencher o dashboard.</p></div></section>`:''}<div class="crm-dashboard-grid"><section class="crm-panel"><div class="crm-panel-heading"><div><span>Prioridades</span><h2>O que precisa de atenção</h2></div></div>${attentionBody}</section><section class="crm-panel"><div class="crm-panel-heading"><div><span>Navegação</span><h2>Acessos principais</h2></div></div><nav class="crm-dashboard-shortcuts" aria-label="Acessos principais"><a href="#/crm/relationships">CRM<span>Contatos, clientes e leads</span></a><a href="#/crm/financeiro">Financeiro<span>Transações e conciliação operacional</span></a><a href="#/crm/negocios">Negócios<span>Produtos, serviços e unidades</span></a><a href="#/crm/juridico">Jurídico<span>Assuntos, contratos e demais owners jurídicos</span></a></nav></section></div></section></main></div>`;
  }
'''

SETTINGS_COMPANY = r'''  function crmSettingsCompanyBody(){
    return `${crmFidelityPanel('Empresa','Identidade institucional do Sistema Interno',`<div class="crm-settings-readonly-brand"><img src="assets/valtren-logo.svg" alt="Valtren Solutions"><div><strong>VALTREN SOLUTIONS</strong><span>Configuração institucional</span></div></div>`)}${crmFidelityPanel('Persistência','',crmRefEmpty('Configuração ainda não conectada','Dados institucionais editáveis exigem uma camada real de persistência. Nenhuma alteração é simulada neste frontend.'))}`;
  }
'''

SETTINGS_NOTIFICATIONS = r'''  function crmSettingsNotificationsBody(){
    return crmFidelityPanel('Notificações','',crmRefEmpty('Serviço de notificações não configurado','Preferências e entregas serão habilitadas quando existir um serviço real de notificações e persistência.'));
  }
'''

SETTINGS_SECURITY = r'''  function crmSettingsSecurityBody(){
    return crmFidelityPanel('Segurança','',`<div class="crm-empty-state crm-auth-disabled-state"><strong>Autenticação desativada</strong><p>Não há senha, MFA, sessão, bloqueio ou usuário autenticado ativos neste ambiente. Esses controles só serão configuráveis quando houver um provedor real de identidade.</p></div>`);
  }
'''

SETTINGS_INTEGRATIONS = r'''  function crmSettingsIntegrationsBody(){
    const integrations=['WhatsApp','Resend','Autentique','NFS-e / Nota Fiscal','Instagram','Facebook','YouTube','TikTok','Google Ads','Soundcharts'];
    const cards=integrations.map((name)=>`<article><strong>${name}</strong><span class="crm-ref-badge">Não configurado</span><small>Sem credenciais ou conexão ativa</small><span class="crm-integration-note">Credenciais devem ser configuradas fora do frontend, em infraestrutura segura.</span></article>`).join('');
    return crmFidelityPanel('Integrações','Conexões externas previstas para configuração futura.',`<div class="crm-ref-integration-grid crm-integration-grid-readonly">${cards}</div>`);
  }
'''

SETTINGS_AUDIT = r'''  function crmSettingsAuditBody(){
    return crmFidelityPanel('Auditoria','',crmRefEmpty('Auditoria ainda não possui fonte de eventos','Quando houver backend e event store reais, os eventos serão exibidos aqui em modo somente leitura.'));
  }
'''

SETTINGS_USERS = r'''  function crmSettingsUsersBody(){
    return crmFidelityPanel('Usuários e Permissões','',`<div class="crm-empty-state crm-auth-disabled-state"><strong>Autenticação desativada</strong><p>Convites, usuários, papéis, permissões, MFA e sessões não são simulados. Esta área será habilitada somente com uma fonte de identidade real.</p></div>`);
  }
'''

PROFILE = r'''  function crmCanonicalProfilePage(){
    const breadcrumb=crmArchitectureBreadcrumb([{label:'Conta',href:'#/crm/meu-perfil'}]);
    const body=crmFidelityPanel('Conta','',`<div class="crm-empty-state crm-auth-disabled-state"><strong>Autenticação desativada</strong><p>Não existe perfil de usuário ou sessão ativa para editar. A rota é mantida apenas por compatibilidade de navegação enquanto a autenticação estiver desativada.</p><a class="crm-empty-action" href="#/crm/configuracoes">Ir para Configurações</a></div>`);
    return crmFidelityPage('','profile','Conta','Estado de acesso do Sistema Interno','',`${breadcrumb}${body}`);
  }
'''

CSS_PATCH = r'''
/* VALTREN PRODUCT SYSTEM REVIEW */
:root{--crm-bg:#f4f6f8;--crm-surface:#fff;--crm-surface-soft:#f8fafc;--crm-text:#0b1d3a;--crm-muted:#687386;--crm-border:rgba(11,29,58,.12);--crm-accent:#d4af37;--crm-danger:#a72828;--crm-radius-sm:8px;--crm-radius-md:12px;--crm-radius-lg:16px;--crm-shadow-sm:0 1px 2px rgba(11,29,58,.05);--crm-space-1:6px;--crm-space-2:10px;--crm-space-3:14px;--crm-space-4:18px;--crm-space-5:24px;--crm-space-6:30px}
.crm-app-shell{display:block;grid-template-columns:none;min-height:100vh;background:var(--crm-bg);color:var(--crm-text);padding-left:250px}.crm-sidebar{position:fixed;inset:0 auto 0 0;width:250px;height:100vh;box-sizing:border-box;overflow-y:auto;overscroll-behavior:contain;z-index:100}.crm-main{width:100%;min-width:0;margin:0}.crm-app-shell .crm-topbar{min-height:88px;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;gap:24px;background:var(--crm-surface);border-bottom:1px solid var(--crm-border);box-sizing:border-box}.crm-app-shell .crm-topbar>div:first-child{min-width:0}.crm-app-shell .crm-topbar h1{margin:2px 0 4px;line-height:1.15}.crm-app-shell .crm-topbar p{margin:0;color:var(--crm-muted);max-width:760px}.crm-workspace{width:min(100%,1500px);margin:0 auto;padding:var(--crm-space-6);box-sizing:border-box}.crm-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:var(--crm-space-5)}.crm-page-header h2{margin:0 0 6px;font-size:24px;line-height:1.2}.crm-page-header p{margin:0;color:var(--crm-muted)}
.crm-header-actions{display:flex;align-items:center;gap:10px;flex:0 0 auto}.crm-header-create{min-height:40px;border:0;border-radius:var(--crm-radius-sm);background:var(--crm-text);color:#fff;padding:0 15px;display:inline-flex;align-items:center;gap:8px;font:inherit;font-weight:700;cursor:pointer}.crm-account-menu{position:relative}.crm-account-menu>summary{list-style:none;min-height:44px;display:flex;align-items:center;gap:10px;padding:5px 10px;border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);background:var(--crm-surface);cursor:pointer}.crm-account-menu>summary::-webkit-details-marker{display:none}.crm-account-icon{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:var(--crm-surface-soft);border:1px solid var(--crm-border)}.crm-account-copy{display:flex;flex-direction:column;align-items:flex-start;line-height:1.15}.crm-account-copy strong{font-size:13px}.crm-account-copy small{font-size:10px;color:var(--crm-muted);margin-top:3px}.crm-account-chevron{color:var(--crm-muted)}.crm-account-popover{position:absolute;right:0;top:calc(100% + 8px);width:min(320px,calc(100vw - 28px));padding:16px;border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);background:var(--crm-surface);box-shadow:0 16px 40px rgba(11,29,58,.16);z-index:500}.crm-account-popover p{font-size:12px;line-height:1.5;color:var(--crm-muted);margin:7px 0 12px}.crm-account-popover a{color:var(--crm-text);font-weight:700;text-decoration:none}
.crm-kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}.crm-kpi{min-width:0;background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);padding:18px;box-shadow:var(--crm-shadow-sm)}.crm-kpi>span{display:block;color:var(--crm-muted);font-size:12px;font-weight:700}.crm-kpi>strong{display:block;margin-top:9px;font-size:22px;line-height:1.15;overflow-wrap:anywhere}.crm-kpi>small{display:block;margin-top:7px;color:var(--crm-muted);font-size:10px;line-height:1.35}.crm-dashboard-workspace{display:grid;gap:var(--crm-space-5)}.crm-dashboard-workspace>.crm-page-header{margin-bottom:0}.crm-dashboard-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}.crm-panel{background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);box-shadow:var(--crm-shadow-sm);padding:20px}.crm-panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px}.crm-panel-heading span{color:var(--crm-muted);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em}.crm-panel-heading h2{font-size:18px;margin:4px 0 0}.crm-dashboard-attention-grid,.crm-dashboard-shortcuts{display:grid;gap:10px}.crm-dashboard-attention-grid a,.crm-dashboard-shortcuts a{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;align-items:center;padding:12px;border:1px solid var(--crm-border);border-radius:var(--crm-radius-sm);color:var(--crm-text);text-decoration:none;background:var(--crm-surface)}.crm-dashboard-attention-grid a strong{grid-row:1/3;font-size:22px}.crm-dashboard-attention-grid a small,.crm-dashboard-shortcuts a span{grid-column:2;color:var(--crm-muted);font-size:11px}.crm-dashboard-shortcuts a{grid-template-columns:1fr}.crm-dashboard-shortcuts a span{grid-column:1}
.crm-empty-state{min-height:130px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:24px;border:1px dashed var(--crm-border);border-radius:var(--crm-radius-md);background:var(--crm-surface-soft)}.crm-empty-state strong{font-size:15px}.crm-empty-state p{max-width:620px;margin:8px auto 0;color:var(--crm-muted);font-size:13px;line-height:1.55}.crm-empty-action{margin-top:14px;color:var(--crm-text);font-weight:700;text-decoration:none}.crm-auth-disabled-state{min-height:180px}.crm-settings-readonly-brand{display:flex;align-items:center;gap:14px}.crm-settings-readonly-brand img{width:46px;height:46px;object-fit:contain}.crm-settings-readonly-brand div{display:flex;flex-direction:column;gap:4px}.crm-settings-readonly-brand span{color:var(--crm-muted);font-size:12px}.crm-integration-grid-readonly article{min-height:150px}.crm-integration-note{display:block;color:var(--crm-muted);font-size:10px;line-height:1.45;margin-top:8px}
.crm-table-wrap,.crm-rel-table-wrap,.crm-fidelity-table-wrap{max-width:100%;overflow:auto}.crm-table th,.crm-table td,.crm-rel-table th,.crm-rel-table td,.crm-fidelity-table th,.crm-fidelity-table td{vertical-align:middle}.crm-table th,.crm-rel-table th,.crm-fidelity-table th{white-space:nowrap}.crm-rel-table td,.crm-table td,.crm-fidelity-table td{padding-top:12px;padding-bottom:12px}.crm-ref-form-grid input,.crm-ref-form-grid select,.crm-ref-form-grid textarea,.crm-rel-field input,.crm-rel-field select,.crm-rel-field textarea{min-height:42px;border-radius:var(--crm-radius-sm);border-color:var(--crm-border);box-sizing:border-box}.crm-modal,.crm-drawer,.crm-rel-modal{max-width:calc(100vw - 28px)}
.crm-global-loading{position:fixed;inset:0;z-index:2000;display:grid;place-items:center;background:var(--crm-bg)}.crm-global-loading-inner{width:min(300px,70vw);display:grid;justify-items:center;gap:20px}.crm-global-loading-inner img{width:90px;max-height:80px;object-fit:contain}.crm-global-loading-bar{width:100%;height:4px;border-radius:999px;overflow:hidden;background:rgba(11,29,58,.12)}.crm-global-loading-bar::after{content:"";display:block;width:38%;height:100%;border-radius:inherit;background:var(--crm-accent);animation:crm-loading-slide 1.2s ease-in-out infinite}@keyframes crm-loading-slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
@media(max-width:1200px){.crm-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.crm-dashboard-grid{grid-template-columns:1fr}}
@media(max-width:980px) and (min-width:761px){.crm-app-shell{padding-left:210px}.crm-sidebar{width:210px}.crm-workspace{padding:24px}.crm-app-shell .crm-topbar{padding-inline:24px}}
@media(max-width:760px){.crm-app-shell{padding-left:0}.crm-sidebar{position:static;width:auto;height:auto;max-height:none;overflow:visible}.crm-app-shell .crm-topbar{min-height:auto;padding:18px;align-items:flex-start;flex-direction:column}.crm-header-actions{width:100%;justify-content:space-between}.crm-account-menu{margin-left:auto}.crm-workspace{padding:18px}.crm-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.crm-page-header{flex-direction:column}.crm-panel{padding:16px}}
@media(max-width:480px){.crm-kpi-grid{grid-template-columns:1fr}.crm-header-create{flex:1;justify-content:center}.crm-account-copy{display:none}.crm-workspace{padding:14px}.crm-panel{border-radius:10px}}
'''


def apply_crm_product_system_review() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    start = app.find(HEADER_START)
    end = app.find(HEADER_END, start) if start >= 0 else -1
    if start < 0 or end < 0:
        raise RuntimeError("Bloco compartilhado do Account Menu não encontrado")
    app = app[:start] + HEADER_HELPERS + app[end + len(HEADER_END):]
    for name, replacement in {
        "crmRelEnsureState": EMPTY_RELATIONSHIP_STATE,
        "crmFullUsers": EMPTY_USERS,
        "crmDashboardPage": DASHBOARD,
        "crmSettingsCompanyBody": SETTINGS_COMPANY,
        "crmSettingsNotificationsBody": SETTINGS_NOTIFICATIONS,
        "crmSettingsSecurityBody": SETTINGS_SECURITY,
        "crmSettingsIntegrationsBody": SETTINGS_INTEGRATIONS,
        "crmSettingsAuditBody": SETTINGS_AUDIT,
        "crmSettingsUsersBody": SETTINGS_USERS,
        "crmCanonicalProfilePage": PROFILE,
    }.items():
        app = _replace_function(app, name, replacement)
    for old, new in [
        ("Protótipo · dados ilustrativos", ""),
        ("CRM Integrado", "Sistema Interno"),
        ("Módulos do CRM", "Módulos do Sistema Interno"),
        ("Não conectado", "Não configurado"),
        ("state.crmUserName || 'Administrador'", "state.crmUserName || ''"),
        ("state.crmUserName||'Administrador'", "state.crmUserName||''"),
    ]:
        app = app.replace(old, new)
    APP.write_text(app, encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN PRODUCT SYSTEM REVIEW \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    print("Revisão global materializada: dados demo removidos, dashboard real, Account Menu transparente, settings sem ações falsas e UI consolidada.")
    return 1


if __name__ == "__main__":
    apply_crm_product_system_review()
