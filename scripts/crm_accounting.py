from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_accounting_core.js"
BROWSER = ROOT / "scripts" / "crm_accounting_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_accounting.css"
CACHE_VERSION = "20260825-accounting-v1"
JS_START = "  // VALTREN ACCOUNTING START\n"
JS_END = "  // VALTREN ACCOUNTING END\n"


def apply_crm_accounting() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()

    # Remove a previous materialized Accounting block, if any.
    app = re.sub(
        r"\n?  // VALTREN ACCOUNTING START\n.*?  // VALTREN ACCOUNTING END\n",
        "\n",
        app,
        flags=re.S,
    )

    # Neutralize every legacy Contabilidade page implementation. Both the reference
    # module and the fidelity layer used to define independent P&L Empresa/Projetos/Artistas.
    legacy_pattern = r"\n?  function crmRefAccountingPage\(\)\{.*?(?=\n\s{2}function crmRefInvoicesPage\(\))"
    app, removed_legacy = re.subn(legacy_pattern, "\n", app, flags=re.S)
    if removed_legacy < 1:
        raise RuntimeError("Implementação legada de Contabilidade não encontrada para neutralização")

    # The old local P&L tab handler is no longer part of the canonical architecture.
    app = app.replace(
        "if(a==='crm-ref-accounting-tab'){state.crmRefAccountingTab=t.dataset.tab;renderCurrentWithoutReset();return;}",
        "",
    )

    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Contabilidade: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    route_old = "if(path==='/crm/financeiro/accounting')return crmRefAccountingPage();"
    if route_old not in app:
        raise RuntimeError("Rota legada de Contabilidade não encontrada")
    app = app.replace(route_old, "if(path==='/crm/financeiro/accounting')return crmAccountingPage();")

    required = [
        "ValtrenAccountingCore",
        "state.crmAccounting",
        "function crmAccountingPage()",
        "function crmAccountingDreView",
        "function crmAccountingEntriesView",
        "function crmAccountingClassificationsView",
        "function crmAccountingOpenDrill",
        "state.crmFinancialTransactions",
        "crmFinanceService()",
        "Competência",
        "Caixa",
        "Receita Bruta",
        "Resultado Final",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Contabilidade incompleta no bundle: {missing}")

    if "if(path==='/crm/financeiro')return crmTransactionsPage();" not in app:
        raise RuntimeError("Transações deixou de ser a rota financeira canônica")
    if "if(path==='/crm/financeiro/accounting')return crmAccountingPage();" not in app:
        raise RuntimeError("Rota de Contabilidade não aponta para implementação canônica")

    forbidden_legacy = [
        "P&L Empresa",
        "P&L Projetos",
        "P&L Artistas",
        "P&L por Projeto",
        "P&L por Artista",
        "Artist P&L",
        "Project P&L",
    ]
    leaked = [label for label in forbidden_legacy if label in app]
    if leaked:
        raise RuntimeError(f"P&L legado reapareceu no bundle: {leaked}")

    # Validate the definitive sidebar without editing it.
    sidebar_start = app.rfind("function crmRelSidebar")
    sidebar_end = app.find("function crmReferenceRoute", sidebar_start)
    sidebar = app[sidebar_start:sidebar_end]
    expected_finance = ["Transações", "Contabilidade", "Notas Fiscais", "Rateios", "Participações", "Repasses"]
    missing_sidebar = [label for label in expected_finance if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar financeiro sofreu regressão: {missing_sidebar}")
    forbidden_sidebar = ["Categorias Financeiras", "Regras de Categorização", "Automações Financeiras"]
    leaked_sidebar = [label for label in forbidden_sidebar if label in sidebar]
    if leaked_sidebar:
        raise RuntimeError(f"Item financeiro indevido voltou ao sidebar: {leaked_sidebar}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN ACCOUNTING \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Financeiro → Contabilidade materializado sobre Transações canônicas; P&L legado neutralizado; sidebar preservado.")
    return 1


if __name__ == "__main__":
    apply_crm_accounting()
