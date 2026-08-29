from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MODULE_DIR = ROOT / "web" / "src" / "modules" / "finance" / "transactions"
DOMAIN = MODULE_DIR / "core.js"
BROWSER = MODULE_DIR / "browser.js"
PRESENTATION = MODULE_DIR / "presentation.js"
MODULE_CSS = MODULE_DIR / "styles.css"
CONSISTENCY_CSS = MODULE_DIR / "consistency.css"
CACHE_VERSION = "20260829-finance-transactions-single-value-v2"
JS_START = "  // VALTREN FINANCIAL TRANSACTIONS START\n"
JS_END = "  // VALTREN FINANCIAL TRANSACTIONS END\n"


def _remove_overridden_function(source: str, start_token: str, next_token: str) -> str:
    start = source.find(start_token)
    end = source.find(next_token, start)
    if start < 0 or end <= start:
        raise RuntimeError(f"Implementação base de Transações não localizada: {start_token}")
    if source.find(start_token, start + len(start_token)) >= 0:
        raise RuntimeError(f"Implementação base duplicada antes da apresentação final: {start_token}")
    return source[:start] + source[end:]


def _html_action_count(source: str, action: str) -> int:
    pattern = re.compile(
        rf'<(?:input|select|textarea)\b(?=[^>]*\bdata-action="{re.escape(action)}")[^>]*>',
        re.I,
    )
    return len(pattern.findall(source))


def apply_crm_financial_transactions() -> int:
    for path in (APP, CSS, DOMAIN, BROWSER, PRESENTATION, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    domain = DOMAIN.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
    presentation = PRESENTATION.read_text(encoding="utf-8").strip()

    # presentation.js owns the final row, table and page renderers. The base
    # implementations must not remain in the production bundle as dead templates.
    browser = _remove_overridden_function(browser, "function crmFinanceRow(tx)", "function crmFinanceBulkBar")
    browser = _remove_overridden_function(browser, "function crmFinanceTable()", "function crmTransactionsPage()")
    browser = _remove_overridden_function(browser, "function crmTransactionsPage()", "function crmFinanceMountOverlay")

    # Validate the final presentation itself, not helper definitions that remain in
    # the browser module for status logic and backwards-compatible internal APIs.
    if "crmFinanceStatusTabs()" in presentation:
        raise RuntimeError("Cards Pendentes/Lançadas/Excluídas ainda renderizados na apresentação final de Transações")
    if '<th class="right">Saída</th>' in presentation or '<th class="right">Entrada</th>' in presentation:
        raise RuntimeError("Colunas Saída/Entrada ainda existem separadamente na apresentação final de Transações")
    if presentation.count('<th class="right">Valor</th>') != 1:
        raise RuntimeError("Apresentação final de Transações precisa possuir exatamente uma coluna Valor")

    block = JS_START + domain + "\n\n" + browser + "\n\n" + presentation + "\n" + JS_END

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
        "Origem/Destino",
        "Produto/Sistema",
        "crmCanonicalPartyService()",
        "function crmFinanceOpenDetail",
        "function crmFinanceOpenAllocation",
        "function crmFinanceOpenMatch",
        "function crmFinanceSignedMoney",
        '<th class=\"right\">Valor</th>',
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Transações incompleto no bundle: {missing}")

    transaction_block_start = app.find(JS_START.strip())
    transaction_block_end = app.find(JS_END.strip(), transaction_block_start)
    if transaction_block_start < 0 or transaction_block_end <= transaction_block_start:
        raise RuntimeError("Bloco canônico de Transações não localizado")
    transaction_block = app[transaction_block_start:transaction_block_end]

    for action in ("crm-fin-counterparty", "crm-fin-category"):
        count = _html_action_count(transaction_block, action)
        if count != 1:
            raise RuntimeError(
                f"Controle HTML de Transações {action} divergente: esperado=1 atual={count}"
            )
        handler = f"target.matches('[data-action=\"{action}\"]')"
        handler_count = transaction_block.count(handler)
        if handler_count != 1:
            raise RuntimeError(
                f"Handler de Transações {action} divergente: esperado=1 atual={handler_count}"
            )

    uniqueness = {
        'data-action="crm-fin-page" data-page="${filters.page-1}"': 1,
        'data-action="crm-fin-page" data-page="${filters.page+1}"': 1,
        '<th class="right">Valor</th>': 1,
    }
    for token, expected in uniqueness.items():
        count = transaction_block.count(token)
        if count != expected:
            raise RuntimeError(f"Transações materializadas duplicadas para {token}: esperado={expected} atual={count}")

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

    print("Financeiro → Transações materializado com implementação única, coluna Valor e sem cards de status.")
    return 1


if __name__ == "__main__":
    apply_crm_financial_transactions()
