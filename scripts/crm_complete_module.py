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
CACHE_VERSION = "20260827-crm-complete-v3"
JS_START = "  // VALTREN CRM COMPLETE START\n"
JS_END = "  // VALTREN CRM COMPLETE END\n"


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
        "const CRM_FULL_TABS=[['contacts','Contatos'],['companies','Empresas'],['customers','Clientes'],['leads','Leads'],['interactions','Interações']]",
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
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"CRM completo incompleto no bundle: {missing}")
    if fake_current_user in app:
        raise RuntimeError("CRM completo ainda fabrica usuário atual no runtime materializado")

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
    module_css = MODULE_CSS.read_text(encoding="utf-8").strip()
    CSS.write_text(css.rstrip() + "\n\n" + module_css + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("CRM completo aplicado sobre Pessoas/Organizações canônicas sem alterar sidebar ou outros módulos.")
    return 1


if __name__ == "__main__":
    apply_crm_complete_module()
