from __future__ import annotations
from pathlib import Path
from crm_legal_materializer_utils import APP, CSS, replace_marked_block, replace_route, replace_css, validate_legal_sidebar, validate_previous_owners, update_cache_version
from crm_accessibility_semantics import OWNER_STATIC_LABELS, apply_accessible_names

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "crm_corporate_governance_core.js"
BROWSER = ROOT / "scripts" / "crm_corporate_governance_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_corporate_governance.css"
CONSISTENCY_CSS = ROOT / "scripts" / "crm_corporate_governance_consistency.css"
JS_START = "  // VALTREN CORPORATE GOVERNANCE START\n"
JS_END = "  // VALTREN CORPORATE GOVERNANCE END\n"
OLD_ROUTE = "if(path==='/crm/juridico/societario')return crmArchitecturePlaceholderPage('legal','corporate','Societário');"
NEW_ROUTE = "if(path==='/crm/juridico/societario')return crmCorporateGovernancePage();"

def apply_crm_corporate_governance() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists(): raise FileNotFoundError(path)
    app = APP.read_text(encoding="utf-8"); core = CORE.read_text(encoding="utf-8").strip(); browser = apply_accessible_names(BROWSER.read_text(encoding="utf-8").strip(), OWNER_STATIC_LABELS["corporate_governance"])
    forbidden = ["createParticipation(", "createPayout(", "createTransaction(", "economicRule.percentage=", "participationAmount=", "payoutAmount="]
    leaked = [x for x in forbidden if x in core]
    if leaked: raise RuntimeError(f"Societário violou separação de ownership: {leaked}")
    app = replace_marked_block(app, JS_START, JS_END, core + "\n\n" + browser)
    app = replace_route(app, OLD_ROUTE, NEW_ROUTE, "Societário")
    required = ["ValtrenCorporateGovernanceCore", "state.crmCorporateGovernance", "function crmCorporateGovernancePage()", "function crmCorporateStructureFeed", "function crmCorporateShareholdersFeed", "resolveCorporateStructureAt", "corporate_ownership_is_not_economic_participation", "financialEffect:'none_automatic'", "economicParticipationFeed:undefined", "payoutFeed:undefined", "createFinancialTransaction:undefined"]
    missing = [x for x in required if x not in app]
    if missing: raise RuntimeError(f"Societário incompleto no bundle: {missing}")
    if OLD_ROUTE in app or app.count(NEW_ROUTE) != 1: raise RuntimeError("Handler canônico de Societário inválido")
    for token in ["state.crmEconomicParticipations", "state.crmPayouts", "function crmParticipationObligationsFeed", "function crmPayoutService()"]:
        if token not in app: raise RuntimeError(f"Owner Financeiro ausente após Societário: {token}")
    validate_previous_owners(app); validate_legal_sidebar(app)
    APP.write_text(app, encoding="utf-8")
    module_css = MODULE_CSS.read_text(encoding="utf-8").rstrip() + "\n" + CONSISTENCY_CSS.read_text(encoding="utf-8")
    CSS.write_text(replace_css(CSS.read_text(encoding="utf-8"), "VALTREN CORPORATE GOVERNANCE", module_css), encoding="utf-8"); update_cache_version()
    print("Jurídico → Societário materializado com estruturas históricas, sócios, holdings, capital, aportes, administradores e atos; escala visual normalizada e ownership econômico preservado.")
    return 1

if __name__ == "__main__": apply_crm_corporate_governance()
