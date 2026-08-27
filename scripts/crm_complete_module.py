from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
DOMAIN_JS = ROOT / "scripts" / "crm_complete_domain.js"
BROWSER_JS = ROOT / "scripts" / "crm_complete_browser.js"
HARDENING_JS = ROOT / "scripts" / "crm_complete_hardening.js"
MODULE_CSS = ROOT / "scripts" / "crm_complete_module.css"
CACHE_VERSION = "20260827-crm-complete-v4"
JS_START = "  // VALTREN CRM COMPLETE START\n"
JS_END = "  // VALTREN CRM COMPLETE END\n"
CONTACTS_CSS_MARKER = "/* VALTREN CRM CONTACTS WORKSPACE */"
CONTACTS_CSS = r'''
/* VALTREN CRM CONTACTS WORKSPACE */
.crm-full-workspace{max-width:none;margin:0;width:100%}
.crm-full-workspace>.crm-full-tabs{margin-top:0}
.crm-relationships-topbar{justify-content:flex-end}
@media(max-width:760px){.crm-relationships-topbar{padding-left:12px!important;padding-right:12px!important}.crm-relationships-topbar .crm-header-actions{width:100%}}
'''

CRM_VISIBLE_TABS_OLD = "const CRM_FULL_TABS=[['contacts','Contatos'],['companies','Empresas'],['customers','Clientes'],['leads','Leads'],['interactions','Interações']];"
CRM_VISIBLE_TABS_NEW = "const CRM_FULL_TABS=[['contacts','Contatos'],['leads','Leads']];"
CRM_IDENTITY_BLOCK = '''function crmFullBreadcrumb(tab){const label=CRM_FULL_TABS.find(([id])=>id===tab)?.[1]||'Contatos';return `<nav class="crm-full-breadcrumb" aria-label="Breadcrumb"><a href="#/crm/relationships">CRM</a><span>/</span><strong>${label}</strong></nav>`;}
function crmFullHeader(tab){
  const config={contacts:['Contatos','Pessoas relacionadas comercial ou institucionalmente à Valtren.','Novo Contato','contact'],companies:['Empresas','Organizações relacionadas à Valtren sem duplicação por papel.','Nova Empresa','company'],customers:['Clientes','Visão de Pessoas e Organizações que possuem o papel Cliente.','Novo Cliente','customer'],leads:['Leads','Oportunidades comerciais vinculadas a identidades canônicas.','Novo Lead','lead'],interactions:['Interações','Histórico real de relacionamento comercial e institucional.','Nova Interação','interaction']},[title,description,actionLabel,kind]=config[tab];
  return `<div class="crm-full-section-header"><div><h2>${title}</h2><p>${description}</p></div><button class="crm-rel-primary" type="button" data-action="crm-full-create" data-kind="${kind}">${icon('plus',16)} ${actionLabel}</button></div>`;
}
'''
CRM_PAGE_OLD = '''function crmRelationshipsPage(query){
  crmFullService();const tab=crmFullCurrentTab(query),content={contacts:crmFullContactsView,companies:crmFullCompaniesView,customers:crmFullCustomersView,leads:crmFullLeadsView,interactions:crmFullInteractionsView}[tab]();
  return `<div class="crm-app-shell crm-full-shell">${crmRelSidebar('relationships')}<main class="crm-main"><header class="crm-topbar"><div><h1>CRM</h1><p>Relacionamentos comerciais sobre Pessoas e Organizações canônicas</p></div>${crmHeaderActions('')}</header><section class="crm-workspace crm-rel-workspace crm-full-workspace" aria-label="CRM">${crmFullBreadcrumb(tab)}${crmFullHeader(tab)}${crmFullTabs(tab)}${content}</section></main></div>`;
}
'''
CRM_PAGE_NEW = '''function crmRelationshipsPage(query){
  crmFullService();const tab=crmFullCurrentTab(query),content=(tab==='leads'?crmFullLeadsView:crmFullContactsView)();
  return `<div class="crm-app-shell crm-full-shell">${crmRelSidebar('relationships')}<main class="crm-main"><header class="crm-topbar crm-relationships-topbar">${crmHeaderActions(tab)}</header><section class="crm-workspace crm-rel-workspace crm-full-workspace" aria-label="${tab==='leads'?'Leads':'Contatos'}">${crmFullTabs(tab)}${content}</section></main></div>`;
}
'''


def _apply_crm_view_contract(browser: str) -> str:
    if CRM_VISIBLE_TABS_NEW not in browser:
        if browser.count(CRM_VISIBLE_TABS_OLD) != 1:
            raise RuntimeError(f"CRM completo: navegação visual legada divergente: {browser.count(CRM_VISIBLE_TABS_OLD)}")
        browser = browser.replace(CRM_VISIBLE_TABS_OLD, CRM_VISIBLE_TABS_NEW, 1)

    if CRM_IDENTITY_BLOCK in browser:
        browser = browser.replace(CRM_IDENTITY_BLOCK, "", 1)
    elif "function crmFullBreadcrumb(tab)" in browser or "function crmFullHeader(tab)" in browser:
        raise RuntimeError("CRM completo: bloco de identificação superior divergente")

    if CRM_PAGE_NEW not in browser:
        if browser.count(CRM_PAGE_OLD) != 1:
            raise RuntimeError(f"CRM completo: composição da página divergente: {browser.count(CRM_PAGE_OLD)}")
        browser = browser.replace(CRM_PAGE_OLD, CRM_PAGE_NEW, 1)

    forbidden = [
        "Pessoas relacionadas comercial ou institucionalmente à Valtren.",
        "function crmFullBreadcrumb(tab)",
        "function crmFullHeader(tab)",
        "['companies','Empresas']",
        "['customers','Clientes']",
        "['interactions','Interações']",
    ]
    leaked = [token for token in forbidden if token in browser]
    if leaked:
        raise RuntimeError(f"CRM completo: UI removida ainda emitida pelo owner: {leaked}")
    required = [
        CRM_VISIBLE_TABS_NEW,
        'class="crm-topbar crm-relationships-topbar">${crmHeaderActions(tab)}',
        "${crmFullTabs(tab)}${content}",
    ]
    missing = [token for token in required if token not in browser]
    if missing:
        raise RuntimeError(f"CRM completo: contrato visual novo incompleto: {missing}")
    return browser


def apply_crm_complete_module() -> int:
    for path in (APP, CSS, DOMAIN_JS, BROWSER_JS, HARDENING_JS, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    domain = DOMAIN_JS.read_text(encoding="utf-8").strip()
    browser = BROWSER_JS.read_text(encoding="utf-8").strip()
    hardening = HARDENING_JS.read_text(encoding="utf-8").strip()

    # Authentication is intentionally disabled. Do not manufacture a current user
    # for responsible/owner selectors; only real locally registered users are valid.
    fake_current_user = "add(state.crmUserId||state.crmUserName||'current',state.crmUserName||'Administrador');"
    real_current_user = "if(state.crmUserId&&state.crmUserName)add(state.crmUserId,state.crmUserName);"
    if fake_current_user not in browser:
        raise RuntimeError("CRM completo: fallback fictício de usuário não encontrado no owner de origem")
    browser = browser.replace(fake_current_user, real_current_user, 1)

    # CRM route composition is owned here: the domain may still expose Organizations,
    # Customers and Interactions, but the visual CRM navigation contains only Contacts
    # and Leads. The redundant breadcrumb/title/description block is not emitted.
    browser = _apply_crm_view_contract(browser)

    # app.js materializa os módulos dentro do shell indentado. Normalizar somente
    # declarações top-level do browser evita limites ambíguos entre materializadores
    # posteriores sem alterar o arquivo-fonte do domínio nem sua semântica.
    browser = re.sub(r"(?m)^function ", "  function ", browser)

    # Keep stable internal enums while presenting Portuguese labels in the UI.
    browser = browser.replace("${esc(context.status||'Ativo')}", "${esc(crmFullStatusLabel(context.status||'active'))}")
    browser = browser.replace("${esc(lead.priority||'-')}", "${esc(crmFullPriorityLabel(lead.priority))}")
    browser = browser.replace("${esc(item.status||'pending')}", "${esc(crmFullStatusLabel(item.status||'pending'))}")

    block = JS_START + domain + "\n\n" + browser + "\n\n" + hardening + "\n" + JS_END

    app = re.sub(
        r"\n?  // VALTREN CRM COMPLETE START\n.*?  // VALTREN CRM COMPLETE END\n",
        "\n",
        app,
        flags=re.S,
    )

    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para CRM completo: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    required = [
        "const CRM_FULL_TABS=[['contacts','Contatos'],['leads','Leads']]",
        "function crmRelationshipsPage(query)",
        "state.crmDomain=ValtrenCrmCore.ensureState(state.crmDomain)",
        "crmCanonicalUpsertLegacyRecord('contacts'",
        "crmCanonicalUpsertLegacyRecord('leads'",
        "function crmFullConvertLead(id)",
        "function crmFullInteractionsView()",
        "function crmFullCompaniesView()",
        "function crmFullCustomersView()",
        "VALTREN CRM COMPLETE HARDENING",
        "{legacy:true}",
        real_current_user,
        "crmHeaderActions(tab)",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"CRM completo incompleto no bundle: {missing}")
    if fake_current_user in app:
        raise RuntimeError("CRM completo ainda fabrica usuário atual no runtime materializado")
    if "Pessoas relacionadas comercial ou institucionalmente à Valtren." in app:
        raise RuntimeError("CRM completo ainda emite descrição redundante de Contatos")

    module_source = domain + "\n" + browser + "\n" + hardening
    forbidden_writes = [
        "state.crmRelContacts.push(",
        "state.crmRelContacts.unshift(",
        "state.crmRelContacts =",
        "state.crmRelLeads.push(",
        "state.crmRelLeads.unshift(",
        "state.crmRelLeads =",
    ]
    leaked = [item for item in forbidden_writes if item in module_source]
    if leaked:
        raise RuntimeError(f"CRM completo introduziu write direto em projeção legada: {leaked}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM COMPLETE \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    css = re.sub(r"\n?/\* VALTREN CRM CONTACTS WORKSPACE \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    module_css = MODULE_CSS.read_text(encoding="utf-8").strip()
    CSS.write_text(css.rstrip() + "\n\n" + module_css + "\n\n" + CONTACTS_CSS.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("CRM completo aplicado com navegação Contatos/Leads, cabeçalho simplificado e domínios internos preservados.")
    return 1


if __name__ == "__main__":
    apply_crm_complete_module()
