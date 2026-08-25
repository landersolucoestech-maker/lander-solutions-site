from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"


def apply_crm_header_context_actions() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)

    app = APP.read_text(encoding="utf-8")

    old_signature = "  function crmHeaderActions(){\n"
    new_signature = "  function crmHeaderActions(context=''){\n"
    if old_signature not in app:
        raise RuntimeError("crmHeaderActions signature not found")
    app = app.replace(old_signature, new_signature, 1)

    old_buttons = '''      <button class="crm-header-create crm-header-create-contact" type="button" data-action="crm-rel-create" data-kind="contacts">${icon('plus',15)}<span>Novo Contato</span></button>\n      <button class="crm-header-create crm-header-create-lead" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>'''
    new_buttons = '''      ${context === 'contacts' ? `<button class="crm-header-create crm-header-create-contact" type="button" data-action="crm-rel-create" data-kind="contacts">${icon('plus',15)}<span>Novo Contato</span></button>` : ''}\n      ${context === 'leads' ? `<button class="crm-header-create crm-header-create-lead" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>` : ''}'''
    if old_buttons not in app:
        raise RuntimeError("Global CRM create buttons block not found")
    app = app.replace(old_buttons, new_buttons, 1)

    dashboard_call = '''          ${crmHeaderActions()}\n        </header>\n        <section class="crm-workspace" aria-label="Dashboard">'''
    dashboard_new = '''          ${crmHeaderActions('dashboard')}\n        </header>\n        <section class="crm-workspace" aria-label="Dashboard">'''
    if dashboard_call not in app:
        raise RuntimeError("Dashboard header actions call not found")
    app = app.replace(dashboard_call, dashboard_new, 1)

    crm_call = '''          ${crmHeaderActions()}\n        </header>\n        <section class="crm-workspace crm-rel-workspace" aria-label="CRM">'''
    crm_new = '''          ${crmHeaderActions(tab)}\n        </header>\n        <section class="crm-workspace crm-rel-workspace" aria-label="CRM">'''
    if crm_call not in app:
        raise RuntimeError("CRM header actions call not found")
    app = app.replace(crm_call, crm_new, 1)

    APP.write_text(app, encoding="utf-8")
    print("Ações do header contextualizadas: Contato apenas em Contatos; Lead apenas em Leads.")
    return 1


if __name__ == "__main__":
    apply_crm_header_context_actions()
