from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CACHE_VERSION = "20260825-finance-transactions-label-v5"


def apply_crm_finance_transactions_label_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    # Rename only the first financial submenu entry. The parent group remains "Financeiro".
    app = app.replace("['finance','Financeiro']", "['finance','Transações']")
    app = app.replace('["finance","Financeiro"]', '["finance","Transações"]')

    # Legacy/reference implementation: keep Transactions immediately to the left of New Rule.
    rules_actions = '<div class="crm-ref-actions right"><button class="primary" data-action="crm-ref-open" data-kind="categorization-rule">${crmRefIcon(\'plus\')} Nova Regra</button></div>'
    rules_actions_with_transactions = '<div class="crm-ref-actions right"><a class="secondary crm-ref-transactions-button" href="#/crm/financeiro">${crmRefIcon(\'database\')} Transações</a><button class="primary" data-action="crm-ref-open" data-kind="categorization-rule">${crmRefIcon(\'plus\')} Nova Regra</button></div>'
    app = app.replace(rules_actions, rules_actions_with_transactions)

    previous_rules_actions = '<div class="crm-ref-actions right"><a class="secondary" href="#/crm/financeiro">${crmRefIcon(\'database\')} Transações</a><button class="primary" data-action="crm-ref-open" data-kind="categorization-rule">${crmRefIcon(\'plus\')} Nova Regra</button></div>'
    app = app.replace(previous_rules_actions, rules_actions_with_transactions)

    previous_button_rules_actions = '<div class="crm-ref-actions right"><button type="button" class="secondary crm-ref-transactions-button" style="order:-1" onclick="location.hash=\'#/crm/financeiro\'">${crmRefIcon(\'database\')} Transações</button><button class="primary" data-action="crm-ref-open" data-kind="categorization-rule">${crmRefIcon(\'plus\')} Nova Regra</button></div>'
    app = app.replace(previous_button_rules_actions, rules_actions_with_transactions)

    # Fidelity implementation used by the published GitHub Pages screen.
    # Its actions are rendered directly inside .crm-fidelity-top-actions in source order,
    # so Transactions must come first to appear immediately LEFT of New Rule.
    fidelity_rules_actions = "const actions=`<button class=\"primary\" data-action=\"crm-ref-open\" data-kind=\"categorization-rule\">${crmRefIcon('plus')} Nova Regra</button>`;"
    fidelity_rules_actions_with_transactions = "const actions=`<a class=\"secondary crm-ref-transactions-button\" href=\"#/crm/financeiro\">${crmRefIcon('database')} Transações</a><button class=\"primary\" data-action=\"crm-ref-open\" data-kind=\"categorization-rule\">${crmRefIcon('plus')} Nova Regra</button>`;"
    app = app.replace(fidelity_rules_actions, fidelity_rules_actions_with_transactions)

    # Categories Financeiras: rename ONLY its navigation button from
    # "Voltar ao Financeiro" to "Transações", preserving the same destination.
    fidelity_categories_actions = '<a class="secondary" href="#/crm/financeiro">← Voltar ao Financeiro</a><button class="primary" data-action="crm-ref-open" data-kind="category">${crmRefIcon(\'plus\')} Criar</button>'
    fidelity_categories_actions_transactions = '<a class="secondary" href="#/crm/financeiro">Transações</a><button class="primary" data-action="crm-ref-open" data-kind="category">${crmRefIcon(\'plus\')} Criar</button>'
    app = app.replace(fidelity_categories_actions, fidelity_categories_actions_transactions)

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print('Botão de Categorias Financeiras renomeado para "Transações"; demais ajustes financeiros preservados.')
    return 1


if __name__ == "__main__":
    apply_crm_finance_transactions_label_fix()
