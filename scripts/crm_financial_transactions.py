from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MODULE_DIR = ROOT / "web" / "src" / "modules" / "finance" / "transactions"
DOMAIN = MODULE_DIR / "core.js"
BROWSER = MODULE_DIR / "browser.js"
MODULE_CSS = MODULE_DIR / "styles.css"
CONSISTENCY_CSS = MODULE_DIR / "consistency.css"
CACHE_VERSION = "20260829-finance-transactions-module-v1"
JS_START = "  // VALTREN FINANCIAL TRANSACTIONS START\n"
JS_END = "  // VALTREN FINANCIAL TRANSACTIONS END\n"


def apply_crm_financial_transactions() -> int:
    for path in (APP, CSS, DOMAIN, BROWSER, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    domain = DOMAIN.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
    block = JS_START + domain + "\n\n" + browser + "\n" + JS_END

    app = re.sub(
        r"\n?  // VALTREN FINANCIAL TRANSACTIONS START\n.*?  // VALTREN FINANCIAL TRANSACTIONS END\n",
        "\n",
        app,
        flags=re.S,
    )

    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Transações: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    route_pattern = "if(path==='/crm/financeiro')return crmRefFinancePage();"
    if app.count(route_pattern) < 1:
        raise RuntimeError("Rota canônica de Financeiro não encontrada")
    app = app.replace(route_pattern, "if(path==='/crm/financeiro')return crmTransactionsPage();")

    required = [
        "ValtrenFinanceCore",
        "state.crmFinancialTransactions",
        "function crmTransactionsPage()",
        "Pendentes",
        "Lançadas",
        "Excluídas",
        "Origem/Destino",
        "Produto/Sistema",
        "crmCanonicalPartyService()",
        "function crmFinanceOpenDetail",
        "function crmFinanceOpenAllocation",
        "function crmFinanceOpenMatch",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Transações incompleto no bundle: {missing}")

    if "if(path==='/crm/financeiro')return crmTransactionsPage();" not in app:
        raise RuntimeError("Rota Financeiro não aponta para Transações canônicas")

    sidebar_start = app.find("// VALTREN SIDEBAR ARCHITECTURE START")
    sidebar_end = app.find("// VALTREN SIDEBAR ARCHITECTURE END", sidebar_start)
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Bloco canônico da Sidebar não localizado para validação")
    sidebar = app[sidebar_start:sidebar_end]
    expected_finance = ["Transações", "Contabilidade", "Notas Fiscais", "Rateios", "Participações", "Repasses"]
    missing_sidebar = [label for label in expected_finance if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar financeiro sofreu regressão: {missing_sidebar}")
    forbidden_sidebar = ["Categorias Financeiras", "Regras de Categorização", "Automações Financeiras"]
    leaked = [label for label in forbidden_sidebar if label in sidebar]
    if leaked:
        raise RuntimeError(f"Item financeiro indevido voltou ao sidebar: {leaked}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN FINANCIAL TRANSACTIONS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    module_css = MODULE_CSS.read_text(encoding="utf-8").strip()
    consistency_css = CONSISTENCY_CSS.read_text(encoding="utf-8").strip()
    CSS.write_text(css.rstrip() + "\n\n" + module_css + "\n" + consistency_css + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Financeiro → Transações materializado a partir de web/src/modules/finance/transactions, preservando a rota e a arquitetura existentes.")
    return 1


if __name__ == "__main__":
    apply_crm_financial_transactions()
