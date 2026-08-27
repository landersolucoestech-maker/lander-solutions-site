from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260827-product-system-review-v6"
CSS_MARKER = "/* VALTREN PRODUCT SYSTEM REVIEW */"


def _replace_between(source: str, start_anchor: str, end_anchor: str, replacement: str, label: str) -> str:
    start_count = source.count(start_anchor)
    if start_count != 1:
        raise RuntimeError(f"Âncora inicial de {label} divergente: {start_count}")
    start = source.index(start_anchor)
    search_from = start + len(start_anchor)
    end = source.find(end_anchor, search_from)
    if end < 0:
        raise RuntimeError(f"Âncora final nominal de {label} ausente após o início")
    if end <= start:
        raise RuntimeError(f"Ordem de âncoras inválida em {label}")
    desired = replacement.rstrip() + "\n\n"
    current = source[start:end]
    return source if current == desired else source[:start] + desired + source[end:]


EMPTY_RELATIONSHIP_STATE = r'''  function crmRelEnsureState(){
    if (!Array.isArray(state.crmRelContacts)) state.crmRelContacts = [];
    if (!Array.isArray(state.crmRelLeads)) state.crmRelLeads = [];
    crmCanonicalEnsureFromLegacy();
  }
'''

EMPTY_USERS = r'''  function crmFullUsers(){
    return [];
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
    const integrations=['WhatsApp','Resend','Autentique','NFS-e / Nota Fiscal','Instagram','Facebook','YouTube','TikTok','Google Ads'];
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
:root{
  --crm-bg:#F4F6F8;
  --crm-surface:#FFFFFF;
  --crm-surface-soft:#F8FAFC;
  --crm-surface-muted:#EEF2F6;
  --crm-text:#0B1D3A;
  --crm-muted:#5F6F82;
  --crm-subtle:#7E8B9C;
  --crm-border:#D9E1E9;
  --crm-border-strong:#C8D2DD;
  --crm-accent:#D4AF37;
  --crm-accent-soft:#FFF7D6;
  --crm-danger:#A72828;
  --crm-radius-sm:7px;
  --crm-radius-md:10px;
  --crm-radius-lg:12px;
  --crm-shadow-sm:0 1px 2px rgba(11,29,58,.045);
  --crm-shadow-md:0 8px 24px rgba(11,29,58,.08);
  --crm-space-1:4px;
  --crm-space-2:8px;
  --crm-space-3:12px;
  --crm-space-4:16px;
  --crm-space-5:20px;
  --crm-space-6:24px;
  --crm-space-7:32px;
  --crm-font-xs:11px;
  --crm-font-sm:12px;
  --crm-font-md:13px;
  --crm-font-base:14px;
  --crm-font-lg:16px;
  --crm-font-xl:20px;
  --crm-font-title:24px;
}
html,body{background:var(--crm-bg)}
.crm-app-shell{display:block;grid-template-columns:none;min-height:100vh;background:var(--crm-bg);color:var(--crm-text);font-family:Montserrat,Arial,sans-serif;font-size:var(--crm-font-base);line-height:1.45}
.crm-app-shell *{box-sizing:border-box}
.crm-main{width:100%;min-width:0;margin:0;background:var(--crm-bg)}
.crm-app-shell h1,.crm-app-shell h2,.crm-app-shell h3,.crm-app-shell h4{font-family:Raleway,Arial,sans-serif;color:var(--crm-text)}
.crm-app-shell .crm-topbar{min-height:76px;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px;background:var(--crm-surface);border-bottom:1px solid var(--crm-border);box-sizing:border-box}
.crm-app-shell .crm-topbar>div:first-child{min-width:0}
.crm-app-shell .crm-topbar h1{margin:0 0 3px;font-size:22px;line-height:1.2;font-weight:800;letter-spacing:-.01em}
.crm-app-shell .crm-topbar p{margin:0;color:var(--crm-muted);font-size:12px;line-height:1.4;max-width:760px}
.crm-workspace,.crm-ref-workspace,.crm-agenda-workspace{width:min(100%,1440px);margin:0 auto;padding:var(--crm-space-6);box-sizing:border-box;color:var(--crm-text);color-scheme:light}
.crm-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:var(--crm-space-5)}
.crm-page-header>div:first-child{min-width:0}
.crm-page-header h1,.crm-page-header h2{margin:0 0 4px;font-size:var(--crm-font-title);line-height:1.2;font-weight:800;letter-spacing:-.015em}
.crm-page-header p{margin:0;color:var(--crm-muted);font-size:var(--crm-font-md);line-height:1.45;max-width:780px}
.crm-page-header-actions,.crm-ref-actions{display:flex;align-items:center;justify-content:flex-end;gap:8px;flex-wrap:wrap}
.crm-app-shell button,.crm-app-shell .crm-empty-action,.crm-app-shell a.crm-empty-action{font-family:Raleway,Arial,sans-serif;font-size:var(--crm-font-sm);font-weight:700}
.crm-app-shell button{min-height:36px;padding:8px 12px;border-radius:var(--crm-radius-sm)}
.crm-ref-actions button,.crm-ref-actions a,.crm-legal-secondary-action{height:auto!important;min-height:36px!important;padding:8px 12px!important;border:1px solid var(--crm-border-strong)!important;border-radius:var(--crm-radius-sm)!important;background:#FFFFFF!important;color:var(--crm-text)!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;gap:6px!important;text-decoration:none!important;font:700 var(--crm-font-sm)/1.2 Raleway,Arial,sans-serif!important;cursor:pointer}
.crm-ref-actions .primary,.crm-ref-actions button.primary{background:var(--crm-text)!important;color:#FFFFFF!important;border-color:var(--crm-text)!important}
.crm-ref-actions a:hover,.crm-legal-secondary-action:hover{background:var(--crm-surface-soft)!important;border-color:#AEBBC9!important}
.crm-architecture-breadcrumb{gap:7px!important;margin:0 0 14px!important;color:var(--crm-muted)!important;font-size:var(--crm-font-xs)!important;font-weight:700!important;line-height:1.4!important}
.crm-architecture-breadcrumb a{color:var(--crm-muted)!important;text-decoration:none!important}.crm-architecture-breadcrumb strong{color:var(--crm-text)!important}
.crm-ref-subtabs a,.crm-ref-pnl-tabs button,.crm-ref-ai-tabs button{min-height:34px!important;height:auto!important;padding:7px 10px!important;font:700 var(--crm-font-sm)/1.25 Raleway,Arial,sans-serif!important}
.crm-ref-toolbar{gap:8px!important;padding:10px!important;background:var(--crm-surface-soft)!important;border-color:var(--crm-border)!important}
.crm-ref-toolbar input,.crm-ref-toolbar select,.crm-ref-search{min-height:36px!important;height:36px!important;font:500 var(--crm-font-sm)/1.3 Montserrat,Arial,sans-serif!important;color:var(--crm-text)!important}
.crm-ref-search input{height:34px!important;font-size:var(--crm-font-sm)!important}
.crm-ref-period{font-size:var(--crm-font-sm)!important;color:var(--crm-muted)!important}
.crm-kpi-grid,.crm-ref-kpis,.crm-rel-kpis{gap:12px}
.crm-kpi,.crm-ref-kpi,.crm-rel-kpi{min-width:0;background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);padding:15px 16px;box-shadow:var(--crm-shadow-sm);color:var(--crm-text)}
.crm-kpi>span,.crm-ref-kpi>span,.crm-rel-kpi>span{display:block;color:var(--crm-muted);font-size:var(--crm-font-sm)!important;font-weight:700;line-height:1.35}
.crm-kpi>strong,.crm-ref-kpi>strong,.crm-rel-kpi>strong{display:block;margin-top:7px;font-size:20px!important;line-height:1.15;overflow-wrap:anywhere;color:var(--crm-text)}
.crm-kpi>small,.crm-ref-kpi>small,.crm-rel-kpi>small{display:block;margin-top:5px;color:var(--crm-muted);font-size:var(--crm-font-xs)!important;line-height:1.4}
.crm-panel,.crm-ref-panel,.crm-rel-list-panel,.crm-ref-table-card,.crm-legal-table-card{background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);box-shadow:var(--crm-shadow-sm);color:var(--crm-text)}
.crm-panel{padding:16px}
.crm-panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
.crm-panel-heading span{color:var(--crm-muted);font-size:var(--crm-font-xs);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.crm-panel-heading h2{font-size:var(--crm-font-lg);line-height:1.3;margin:3px 0 0}
.crm-ref-table-card>header h3,.crm-ref-panel>header h3{font-size:14px!important;line-height:1.3!important;color:var(--crm-text)!important}.crm-ref-table-card>header p,.crm-ref-panel>header p{font:400 var(--crm-font-xs)/1.45 Montserrat,Arial,sans-serif!important;color:var(--crm-muted)!important}.crm-ref-table-card>header>span{font-size:var(--crm-font-xs)!important;color:var(--crm-muted)!important}
.crm-ref-badge,.crm-ref-mini-badges span{font-size:var(--crm-font-xs)!important;line-height:1.2!important;padding:5px 8px!important}
.crm-ref-empty strong{font-size:13px!important;color:var(--crm-text)!important}.crm-ref-empty span{font:400 var(--crm-font-xs)/1.45 Montserrat,Arial,sans-serif!important;color:var(--crm-muted)!important}
.crm-ref-field>span,.crm-ref-form-grid label,.crm-rel-field label{font-size:var(--crm-font-xs)!important;line-height:1.35!important;color:var(--crm-muted)!important}
.crm-ref-field>small{font-size:var(--crm-font-xs)!important;color:var(--crm-muted)!important}
.crm-ref-settings-blocks h4,.crm-ref-integration-grid strong{font-size:13px!important;color:var(--crm-text)!important}.crm-ref-settings-blocks p,.crm-ref-settings-blocks label,.crm-ref-integration-grid article small{font-size:var(--crm-font-xs)!important;line-height:1.45!important;color:var(--crm-muted)!important}
.crm-empty-state{min-height:116px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;border:1px dashed var(--crm-border-strong);border-radius:var(--crm-radius-md);background:var(--crm-surface-soft);color:var(--crm-text)}
.crm-empty-state strong{font-size:14px;color:var(--crm-text)}
.crm-empty-state p{max-width:620px;margin:6px auto 0;color:var(--crm-muted);font-size:12px;line-height:1.5}
.crm-empty-action{margin-top:12px;color:var(--crm-text);text-decoration:none}
.crm-auth-disabled-state{min-height:156px}
.crm-settings-readonly-brand{display:flex;align-items:center;gap:12px}
.crm-settings-readonly-brand img{width:42px;height:42px;object-fit:contain}
.crm-settings-readonly-brand div{display:flex;flex-direction:column;gap:3px}
.crm-settings-readonly-brand span{color:var(--crm-muted);font-size:var(--crm-font-sm)}
.crm-integration-grid-readonly{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.crm-integration-grid-readonly article{min-height:126px;padding:14px;background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);color:var(--crm-text)}
.crm-integration-grid-readonly article strong{font-size:13px;color:var(--crm-text)}
.crm-integration-grid-readonly article small,.crm-integration-note{display:block;color:var(--crm-muted);font-size:var(--crm-font-xs)!important;line-height:1.45}
.crm-integration-note{margin-top:6px}
.crm-table-wrap,.crm-rel-table-wrap,.crm-fidelity-table-wrap,.crm-ref-table-wrap,.crm-legal-table-wrap{max-width:100%;overflow:auto}
.crm-table,.crm-rel-table,.crm-fidelity-table,.crm-ref-table-wrap table,.crm-legal-table-wrap table{font-size:12px;color:var(--crm-text)}
.crm-table th,.crm-rel-table th,.crm-fidelity-table th,.crm-ref-table-wrap th,.crm-legal-table-wrap th{white-space:nowrap;color:var(--crm-muted);font-size:11px!important;font-weight:800;line-height:1.3;background:var(--crm-surface-soft)}
.crm-table td,.crm-rel-table td,.crm-fidelity-table td,.crm-ref-table-wrap td,.crm-legal-table-wrap td{vertical-align:middle;color:var(--crm-text);font-size:12px!important;line-height:1.4}
.crm-rel-table td,.crm-table td,.crm-fidelity-table td{padding-top:10px;padding-bottom:10px}
.crm-ref-form-grid input,.crm-ref-form-grid select,.crm-ref-form-grid textarea,.crm-rel-field input,.crm-rel-field select,.crm-rel-field textarea,.crm-legal-toolbar input,.crm-legal-toolbar select{min-height:38px;border-radius:var(--crm-radius-sm);border-color:var(--crm-border-strong);background:#FFFFFF;color:var(--crm-text);font:500 var(--crm-font-sm)/1.35 Montserrat,Arial,sans-serif!important;box-sizing:border-box;color-scheme:light}
.crm-ref-form-grid textarea,.crm-rel-field textarea{min-height:88px}
.crm-app-shell input::placeholder,.crm-app-shell textarea::placeholder{color:#8795A6;opacity:1}
.crm-modal,.crm-drawer,.crm-rel-modal,.crm-agenda-modal,.crm-ref-modal{max-width:calc(100vw - 28px);background:#FFFFFF;color:var(--crm-text);border-color:var(--crm-border);border-radius:var(--crm-radius-lg);box-shadow:var(--crm-shadow-md);color-scheme:light}
.crm-ref-modal>header h2{font-size:18px!important}.crm-ref-modal>header p,.crm-ref-modal-body,.crm-ref-modal footer button{font-size:var(--crm-font-sm)!important}.crm-ref-modal footer button{min-height:36px!important;height:auto!important}
#crm-rel-modal-root,#crm-agenda-modal-root,#crm-ref-modal-root,#crm-legal-overlay-root{--crm-text:#0B1D3A;--crm-muted:#5F6F82;--crm-border:#D9E1E9;color-scheme:light}
#crm-rel-modal-root .crm-rel-modal,#crm-rel-modal-root .crm-rel-modal-header,#crm-rel-modal-root .crm-rel-modal-body,#crm-rel-modal-root .crm-rel-modal-footer,#crm-agenda-modal-root .crm-agenda-modal,#crm-agenda-modal-root .crm-agenda-modal>header,#crm-agenda-modal-root .crm-agenda-modal-body,#crm-agenda-modal-root .crm-agenda-modal footer,#crm-ref-modal-root .crm-ref-modal,#crm-ref-modal-root .crm-ref-modal>header,#crm-ref-modal-root .crm-ref-modal-body,#crm-ref-modal-root .crm-ref-modal footer,#crm-legal-overlay-root .crm-legal-overlay,#crm-legal-overlay-root .crm-legal-modal,#crm-legal-overlay-root .crm-legal-drawer{background:#FFFFFF!important;color:#0B1D3A!important;border-color:#D9E1E9!important;color-scheme:light!important}
#crm-rel-modal-root h1,#crm-rel-modal-root h2,#crm-rel-modal-root h3,#crm-agenda-modal-root h1,#crm-agenda-modal-root h2,#crm-agenda-modal-root h3,#crm-ref-modal-root h1,#crm-ref-modal-root h2,#crm-ref-modal-root h3,#crm-legal-overlay-root h1,#crm-legal-overlay-root h2,#crm-legal-overlay-root h3{color:#0B1D3A!important}
#crm-rel-modal-root p,#crm-agenda-modal-root p,#crm-ref-modal-root p,#crm-legal-overlay-root p{color:#5F6F82}
#crm-rel-modal-root input,#crm-rel-modal-root select,#crm-rel-modal-root textarea,#crm-agenda-modal-root input,#crm-agenda-modal-root select,#crm-agenda-modal-root textarea,#crm-ref-modal-root input,#crm-ref-modal-root select,#crm-ref-modal-root textarea,#crm-legal-overlay-root input,#crm-legal-overlay-root select,#crm-legal-overlay-root textarea{background:#FFFFFF!important;color:#0B1D3A!important;-webkit-text-fill-color:#0B1D3A!important;border-color:#C8D2DD!important;color-scheme:light!important;font-size:var(--crm-font-sm)!important}
.crm-global-loading{position:fixed;inset:0;z-index:2000;display:grid;place-items:center;background:var(--crm-bg)}
.crm-global-loading-inner{width:min(280px,70vw);display:grid;justify-items:center;gap:16px}
.crm-global-loading-inner img{width:78px;max-height:70px;object-fit:contain}
.crm-global-loading-bar{width:100%;height:4px;border-radius:999px;overflow:hidden;background:rgba(11,29,58,.12)}
.crm-global-loading-bar::after{content:"";display:block;width:38%;height:100%;border-radius:inherit;background:var(--crm-accent);animation:crm-loading-slide 1.2s ease-in-out infinite}
@keyframes crm-loading-slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
@media(max-width:1200px){.crm-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:980px) and (min-width:761px){.crm-workspace,.crm-ref-workspace,.crm-agenda-workspace{padding:20px}.crm-app-shell .crm-topbar{padding-inline:20px}}
@media(max-width:760px){.crm-app-shell .crm-topbar{min-height:auto;padding:14px 16px;align-items:flex-start;flex-direction:column}.crm-workspace,.crm-ref-workspace,.crm-agenda-workspace{padding:16px}.crm-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.crm-page-header{flex-direction:column;margin-bottom:16px}.crm-page-header h1,.crm-page-header h2{font-size:21px}.crm-panel{padding:14px}.crm-ref-actions{width:100%;justify-content:flex-start}}
@media(max-width:480px){.crm-kpi-grid{grid-template-columns:1fr}.crm-workspace,.crm-ref-workspace,.crm-agenda-workspace{padding:12px}.crm-panel{border-radius:8px}.crm-page-header-actions,.crm-ref-actions{width:100%;justify-content:flex-start}}
'''

REPLACEMENTS = [
    ("  function crmRelEnsureState(){", "  function crmRelActions(", EMPTY_RELATIONSHIP_STATE, "crmRelEnsureState"),
    ("  function crmFullUsers(){", "  function crmFullResponsibleName(", EMPTY_USERS, "crmFullUsers"),
    ("  function crmSettingsCompanyBody(){", "  function crmSettingsNotificationsBody(){", SETTINGS_COMPANY, "crmSettingsCompanyBody"),
    ("  function crmSettingsNotificationsBody(){", "  function crmSettingsSecurityBody(){", SETTINGS_NOTIFICATIONS, "crmSettingsNotificationsBody"),
    ("  function crmSettingsSecurityBody(){", "  function crmSettingsIntegrationsBody(){", SETTINGS_SECURITY, "crmSettingsSecurityBody"),
    ("  function crmSettingsIntegrationsBody(){", "  function crmSettingsAuditBody(){", SETTINGS_INTEGRATIONS, "crmSettingsIntegrationsBody"),
    ("  function crmSettingsAuditBody(){", "  function crmSettingsUsersBody(){", SETTINGS_AUDIT, "crmSettingsAuditBody"),
    ("  function crmSettingsUsersBody(){", "  function crmCanonicalSettingsPage(){", SETTINGS_USERS, "crmSettingsUsersBody"),
    ("  function crmCanonicalProfilePage(){", "  function crmLegacyRoute(", PROFILE, "crmCanonicalProfilePage"),
]


def _replace_css(css: str) -> str:
    desired = CSS_PATCH.strip()
    marker_at = css.find(CSS_MARKER)
    if marker_at < 0:
        return css.rstrip() + "\n\n" + desired + "\n"
    current = css[marker_at:].strip()
    if current == desired:
        return css
    return css[:marker_at].rstrip() + "\n\n" + desired + "\n"


def apply_crm_product_system_review() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    if app.count("  function crmHeaderActions(context=''){") != 1:
        raise RuntimeError('Header owner divergente antes da revisão global')
    if 'Autenticação desativada' not in app or 'Nenhuma identidade é simulada' not in app:
        raise RuntimeError('Header owner perdeu transparência de autenticação')
    for start_anchor, end_anchor, replacement, label in REPLACEMENTS:
        app = _replace_between(app, start_anchor, end_anchor, replacement, label)
    for old, new in [
        ("Protótipo · dados ilustrativos", ""),
        ("CRM Integrado", "Sistema Interno"),
        ("Módulos do CRM", "Módulos do Sistema Interno"),
        ("Não conectado", "Não configurado"),
        ("state.crmUserName || 'Administrador'", "state.crmUserName || ''"),
        ("state.crmUserName||'Administrador'", "state.crmUserName||''"),
        ("state.crmUserInitials || 'AD'", "state.crmUserInitials || ''"),
        ("state.crmUserInitials||'AD'", "state.crmUserInitials||''"),
    ]:
        app = app.replace(old, new)
    if 'Soundcharts' in app:
        raise RuntimeError('Soundcharts não pertence ao projeto e sobreviveu à revisão global')
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css(css)
    if updated_css != css:
        CSS.write_text(updated_css, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    print("Revisão global transversal materializada: tipografia operacional >=11px, ações/filtros normalizados, contraste claro consistente e Soundcharts ausente.")
    return 1


if __name__ == "__main__":
    apply_crm_product_system_review()
