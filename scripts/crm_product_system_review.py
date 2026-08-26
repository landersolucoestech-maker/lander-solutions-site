from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260826-product-system-review-v4"
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
    # O limite é contextual: usamos a primeira ocorrência da âncora NOMINAL
    # declarada depois do início único. Não existe fallback para "próxima função".
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
.crm-app-shell{display:block;grid-template-columns:none;min-height:100vh;background:var(--crm-bg);color:var(--crm-text)}.crm-main{width:100%;min-width:0;margin:0}.crm-app-shell .crm-topbar{min-height:88px;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;gap:24px;background:var(--crm-surface);border-bottom:1px solid var(--crm-border);box-sizing:border-box}.crm-app-shell .crm-topbar>div:first-child{min-width:0}.crm-app-shell .crm-topbar h1{margin:2px 0 4px;line-height:1.15}.crm-app-shell .crm-topbar p{margin:0;color:var(--crm-muted);max-width:760px}.crm-workspace{width:min(100%,1500px);margin:0 auto;padding:var(--crm-space-6);box-sizing:border-box}.crm-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:var(--crm-space-5)}.crm-page-header h2{margin:0 0 6px;font-size:24px;line-height:1.2}.crm-page-header p{margin:0;color:var(--crm-muted)}
.crm-kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}.crm-kpi{min-width:0;background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);padding:18px;box-shadow:var(--crm-shadow-sm)}.crm-kpi>span{display:block;color:var(--crm-muted);font-size:12px;font-weight:700}.crm-kpi>strong{display:block;margin-top:9px;font-size:22px;line-height:1.15;overflow-wrap:anywhere}.crm-kpi>small{display:block;margin-top:7px;color:var(--crm-muted);font-size:10px;line-height:1.35}.crm-panel{background:var(--crm-surface);border:1px solid var(--crm-border);border-radius:var(--crm-radius-md);box-shadow:var(--crm-shadow-sm);padding:20px}.crm-panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px}.crm-panel-heading span{color:var(--crm-muted);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em}.crm-panel-heading h2{font-size:18px;margin:4px 0 0}
.crm-empty-state{min-height:130px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:24px;border:1px dashed var(--crm-border);border-radius:var(--crm-radius-md);background:var(--crm-surface-soft)}.crm-empty-state strong{font-size:15px}.crm-empty-state p{max-width:620px;margin:8px auto 0;color:var(--crm-muted);font-size:13px;line-height:1.55}.crm-empty-action{margin-top:14px;color:var(--crm-text);font-weight:700;text-decoration:none}.crm-auth-disabled-state{min-height:180px}.crm-settings-readonly-brand{display:flex;align-items:center;gap:14px}.crm-settings-readonly-brand img{width:46px;height:46px;object-fit:contain}.crm-settings-readonly-brand div{display:flex;flex-direction:column;gap:4px}.crm-settings-readonly-brand span{color:var(--crm-muted);font-size:12px}.crm-integration-grid-readonly article{min-height:150px}.crm-integration-note{display:block;color:var(--crm-muted);font-size:10px;line-height:1.45;margin-top:8px}
.crm-table-wrap,.crm-rel-table-wrap,.crm-fidelity-table-wrap{max-width:100%;overflow:auto}.crm-table th,.crm-table td,.crm-rel-table th,.crm-rel-table td,.crm-fidelity-table th,.crm-fidelity-table td{vertical-align:middle}.crm-table th,.crm-rel-table th,.crm-fidelity-table th{white-space:nowrap}.crm-rel-table td,.crm-table td,.crm-fidelity-table td{padding-top:12px;padding-bottom:12px}.crm-ref-form-grid input,.crm-ref-form-grid select,.crm-ref-form-grid textarea,.crm-rel-field input,.crm-rel-field select,.crm-rel-field textarea{min-height:42px;border-radius:var(--crm-radius-sm);border-color:var(--crm-border);box-sizing:border-box}.crm-modal,.crm-drawer,.crm-rel-modal{max-width:calc(100vw - 28px)}
.crm-global-loading{position:fixed;inset:0;z-index:2000;display:grid;place-items:center;background:var(--crm-bg)}.crm-global-loading-inner{width:min(300px,70vw);display:grid;justify-items:center;gap:20px}.crm-global-loading-inner img{width:90px;max-height:80px;object-fit:contain}.crm-global-loading-bar{width:100%;height:4px;border-radius:999px;overflow:hidden;background:rgba(11,29,58,.12)}.crm-global-loading-bar::after{content:"";display:block;width:38%;height:100%;border-radius:inherit;background:var(--crm-accent);animation:crm-loading-slide 1.2s ease-in-out infinite}@keyframes crm-loading-slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
@media(max-width:1200px){.crm-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:980px) and (min-width:761px){.crm-workspace{padding:24px}.crm-app-shell .crm-topbar{padding-inline:24px}}
@media(max-width:760px){.crm-app-shell .crm-topbar{min-height:auto;padding:18px;align-items:flex-start;flex-direction:column}.crm-workspace{padding:18px}.crm-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.crm-page-header{flex-direction:column}.crm-panel{padding:16px}}
@media(max-width:480px){.crm-kpi-grid{grid-template-columns:1fr}.crm-workspace{padding:14px}.crm-panel{border-radius:10px}}
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
    print("Revisão global transversal materializada: Account Menu, auth desativada, estados vazios, settings transparentes e design system consolidados.")
    return 1


if __name__ == "__main__":
    apply_crm_product_system_review()
