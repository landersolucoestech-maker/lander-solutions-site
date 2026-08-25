from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CACHE_VERSION = "20260825-financial-automations-removed-v1"


def apply_crm_financial_automations_remove() -> int:
    app = APP.read_text(encoding="utf-8")

    # Remove submenu entries from both the legacy and fidelity implementations.
    app = app.replace(",['automations','Automações Financeiras']", "")
    app = app.replace(',["automations","Automações Financeiras"]', "")

    # Remove any visible shortcut/action that opens the removed module.
    app = re.sub(
        r'<a\b[^>]*href="#/crm/financeiro/automations"[^>]*>.*?</a>',
        '',
        app,
        flags=re.S,
    )

    # Remove route handlers for the module.
    app = re.sub(
        r"\s*if\(path===['\"]\/crm\/financeiro\/automations['\"]\)return crmRefFinancialRulesPage\(\);",
        "",
        app,
    )

    # Remove the page and modal implementations, including duplicate legacy/fidelity copies.
    app = re.sub(r"\n\s*function crmRefFinancialRulesPage\(\)\{[^\n]*\}\n?", "\n", app)
    app = re.sub(r"\n\s*function crmRefFinancialRuleModal\(\)\{[^\n]*\}\n?", "\n", app)

    # Remove state/bootstrap and modal dispatch tied only to Financial Automations.
    app = re.sub(r"\n\s*if\(!Array\.isArray\(state\.crmRefFinancialRules\)\)state\.crmRefFinancialRules=\[\];", "", app)
    app = re.sub(r"\n\s*if\(kind===['\"]financial-rule['\"]\)\s*html=crmRefFinancialRuleModal\(\);", "", app)

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Módulo Automações Financeiras removido do CRM.")
    return 1


if __name__ == "__main__":
    apply_crm_financial_automations_remove()
