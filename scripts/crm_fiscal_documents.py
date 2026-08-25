from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_fiscal_documents_core.js"
BROWSER = ROOT / "scripts" / "crm_fiscal_documents_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_fiscal_documents.css"
CACHE_VERSION = "20260825-fiscal-documents-v1"
JS_START = "  // VALTREN FISCAL DOCUMENTS START\n"
JS_END = "  // VALTREN FISCAL DOCUMENTS END\n"


def apply_crm_fiscal_documents() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()

    app = re.sub(
        r"\n?  // VALTREN FISCAL DOCUMENTS START\n.*?  // VALTREN FISCAL DOCUMENTS END\n",
        "\n",
        app,
        flags=re.S,
    )

    # The historical Invoice page/modal were reference UI only and used crmRefInvoices
    # as an independent list. Remove their executable implementations from the final
    # bundle; crmRefInvoices may remain only as an input for the explicit compatibility
    # review performed by ValtrenFiscalCore.migrateLegacy().
    app, removed_pages = re.subn(
        r"\n?\s{2}function crmRefInvoicesPage\(\)\{[^\n]*\}\n",
        "\n",
        app,
    )
    app, removed_modals = re.subn(
        r"\n?\s{2}function crmRefInvoiceModal\(\)\{[^\n]*\}\n",
        "\n",
        app,
    )
    if removed_pages < 1:
        raise RuntimeError("Página Invoice legada não encontrada para neutralização")
    if removed_modals < 1:
        raise RuntimeError("Modal Invoice legado não encontrado para neutralização")

    app = app.replace(
        "if(kind==='invoice') html=crmRefInvoiceModal();",
        "if(kind==='invoice'){crmFiscalOpenCreate();return;}",
    )

    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Notas Fiscais: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    # /notas-fiscais is the canonical route. /invoices is retained only as a
    # compatibility alias because the definitive sidebar already points to it;
    # the alias normalizes the browser hash without changing sidebar structure.
    route_old = "if(path==='/crm/financeiro/invoices')return crmRefInvoicesPage();"
    if route_old not in app:
        raise RuntimeError("Rota Invoice legada não encontrada")
    route_new = (
        "if(path==='/crm/financeiro/invoices')return crmFiscalLegacyInvoicesRoute();\n"
        "    if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();"
    )
    app = app.replace(route_old, route_new)

    required = [
        "ValtrenFiscalCore",
        "state.crmFiscalDocuments",
        "function crmFiscalDocumentsPage()",
        "function crmFiscalOpenCreate()",
        "function crmFiscalOpenForm(direction)",
        "function crmFiscalOpenDetail(id)",
        "function crmFiscalAccountingFeed(filters={})",
        "crmFinanceService()",
        "crmCanonicalPartyService()",
        "Criar Nota",
        "Entrada",
        "Saída",
        "Status Fiscal",
        "Status Financeiro",
        "competenceDate",
        "fiscal_document",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Notas Fiscais incompleto no bundle: {missing}")

    if "function crmRefInvoicesPage()" in app or "function crmRefInvoiceModal()" in app:
        raise RuntimeError("Implementação Invoice legada permaneceu executável no bundle")
    if "return crmRefInvoicesPage();" in app:
        raise RuntimeError("Rota legada ainda aponta para crmRefInvoicesPage")
    if "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();" not in app:
        raise RuntimeError("Rota canônica de Notas Fiscais ausente")
    if "if(path==='/crm/financeiro')return crmTransactionsPage();" not in app:
        raise RuntimeError("Transações deixou de ser a rota financeira canônica")
    if "if(path==='/crm/financeiro/accounting')return crmAccountingPage();" not in app:
        raise RuntimeError("Contabilidade deixou de ser canônica")

    # Validate the definitive sidebar, but do not edit its structure/order.
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
    css = re.sub(r"\n?/\* VALTREN FISCAL DOCUMENTS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Financeiro → Notas Fiscais materializado como fonte fiscal canônica; Invoice legado neutralizado; Transações, Contabilidade e sidebar preservados.")
    return 1


if __name__ == "__main__":
    apply_crm_fiscal_documents()
