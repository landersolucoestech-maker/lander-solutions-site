from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_payouts_core.js"
BROWSER = ROOT / "scripts" / "crm_payouts_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_payouts.css"
CONSISTENCY_CSS = ROOT / "scripts" / "crm_payouts_consistency.css"
CACHE_VERSION = "20260826-payouts-v2"
JS_START = "  // VALTREN PAYOUTS START\n"
JS_END = "  // VALTREN PAYOUTS END\n"


def apply_crm_payouts() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
    app = re.sub(r"\n*  // VALTREN PAYOUTS START\n.*?  // VALTREN PAYOUTS END\n+", "\n", app, flags=re.S)
    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    anchor_count = app.count(anchor)
    if anchor_count != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Repasses: {anchor_count} ocorrência(s)")
    anchor_at = app.index(anchor)
    app = app[:anchor_at].rstrip("\n") + "\n\n" + block + "\n" + app[anchor_at:]

    route_old = "if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage('accounting','repasses','Repasses');"
    route_new = "if(path==='/crm/financeiro/repasses')return crmPayoutsPage();"
    old_count = app.count(route_old)
    new_count = app.count(route_new)
    if old_count == 1 and new_count == 0:
        app = app.replace(route_old, route_new, 1)
    elif old_count == 0 and new_count == 1:
        pass
    else:
        raise RuntimeError("Rota de Repasses não está em estado canônico inequívoco: " f"placeholder={old_count}, handler={new_count}")

    required = ["ValtrenPayoutCore","state.crmPayouts","function crmPayoutsPage()","function crmPayoutService()","crmParticipationObligationsFeed","Vincular pagamento","Completar pagamento","Valor devido","Saldo","Conciliação","payment.reversal_detected","source_superseded_with_payments","transactionLinks","sourceSnapshots"]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Repasses incompleto no bundle: {missing}")
    if route_old in app:
        raise RuntimeError("Placeholder de Repasses sobreviveu no bundle")
    if app.count(route_new) != 1:
        raise RuntimeError(f"Handler canônico de Repasses duplicado/ausente: {app.count(route_new)}")

    owners = ["if(path==='/crm/financeiro')return crmTransactionsPage();","if(path==='/crm/financeiro/accounting')return crmAccountingPage();","if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();","if(path==='/crm/financeiro/rateios'){const page=crmCostAllocationsPage();","if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();","if(path==='/crm/juridico/contratos')return crmLegalContractsPage();"]
    missing_owners = [route for route in owners if route not in app]
    if missing_owners:
        raise RuntimeError(f"Owner canônico sofreu regressão durante Repasses: {missing_owners}")
    forbidden = ["createTransaction(","createCalculation(","manualParticipationRule","partnerPercentage","productPartnerSplit","shareholderPercentage","equityPercentage","ownershipPercentage","quotaSocietaria"]
    leaked = [item for item in forbidden if item in core or item in browser]
    if leaked:
        raise RuntimeError(f"Repasses contém responsabilidade proibida/concorrente: {leaked}")

    sidebar_start_marker = "// VALTREN SIDEBAR ARCHITECTURE START"
    sidebar_end_marker = "// VALTREN SIDEBAR ARCHITECTURE END"
    sidebar_start = app.find(sidebar_start_marker)
    sidebar_end = app.find(sidebar_end_marker, sidebar_start + len(sidebar_start_marker)) if sidebar_start >= 0 else -1
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Markers canônicos da Sidebar não puderam ser localizados")
    sidebar = app[sidebar_start:sidebar_end]
    expected_finance = ["Transações", "Contabilidade", "Notas Fiscais", "Rateios", "Participações", "Repasses"]
    missing_sidebar = [label for label in expected_finance if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar Financeiro sofreu regressão: {missing_sidebar}")
    forbidden_sidebar = ["Obrigações", "Pagamentos", "Conciliações", "Beneficiários"]
    leaked_sidebar = [label for label in forbidden_sidebar if label in sidebar]
    if leaked_sidebar:
        raise RuntimeError(f"Submódulo indevido de Repasses foi adicionado ao sidebar: {leaked_sidebar}")

    APP.write_text(app, encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN PAYOUTS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    module_css = MODULE_CSS.read_text(encoding="utf-8").strip()
    consistency_css = CONSISTENCY_CSS.read_text(encoding="utf-8").strip()
    CSS.write_text(css.rstrip() + "\n\n" + module_css + "\n" + consistency_css + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", value)
        value = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", value)
        path.write_text(value, encoding="utf-8")

    print("Financeiro → Repasses materializado como camada canônica de liquidação/conciliação; escala visual normalizada; nenhuma Participação ou Transação é recriada.")
    return 1


if __name__ == "__main__":
    apply_crm_payouts()
