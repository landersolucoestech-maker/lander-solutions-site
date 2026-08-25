from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CACHE_VERSION = "20260825-finance-transactions-label-v1"


def apply_crm_finance_transactions_label_fix() -> int:
    app = APP.read_text(encoding="utf-8")

    # Rename only the first financial submenu entry. The parent group remains "Financeiro".
    app = app.replace("['finance','Financeiro']", "['finance','Transações']")
    app = app.replace('["finance","Financeiro"]', '["finance","Transações"]')

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print('Sub-menu financeiro renomeado para "Transações" no CRM.')
    return 1


if __name__ == "__main__":
    apply_crm_finance_transactions_label_fix()
