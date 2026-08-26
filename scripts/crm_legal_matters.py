from __future__ import annotations
from pathlib import Path
from crm_legal_materializer_utils import APP, CSS, replace_marked_block, replace_route, replace_css, validate_legal_sidebar, validate_previous_owners, update_cache_version

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "crm_legal_matters_core.js"
BROWSER = ROOT / "scripts" / "crm_legal_matters_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_legal_matters.css"
CONSISTENCY_CSS = ROOT / "scripts" / "crm_legal_matters_consistency.css"
JS_START = "  // VALTREN LEGAL MATTERS START\n"
JS_END = "  // VALTREN LEGAL MATTERS END\n"
OLD_ROUTE = "if(path==='/crm/juridico')return crmArchitecturePlaceholderPage('legal','matters','Assuntos Jurídicos');"
NEW_ROUTE = "if(path==='/crm/juridico')return crmLegalMattersPage();"

def apply_crm_legal_matters() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists(): raise FileNotFoundError(path)
    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
    if any(x in core for x in ["createTransaction(", "createAccounting", "createPayout(", "createParticipation("]):
        raise RuntimeError("Assuntos Jurídicos contém responsabilidade financeira indevida")
    body = core + "\n\n" + browser
    app = replace_marked_block(app, JS_START, JS_END, body)
    app = replace_route(app, OLD_ROUTE, NEW_ROUTE, "Assuntos Jurídicos")
    required = ["ValtrenLegalMatterCore", "state.crmLegalMatters", "function crmLegalMattersPage()", "function crmLegalMattersFeed", "function crmLegalMatterDeadlinesFeed", "estimatedExposure", "settlements", "metadata-only"]
    missing = [x for x in required if x not in app]
    if missing: raise RuntimeError(f"Assuntos Jurídicos incompleto no bundle: {missing}")
    if OLD_ROUTE in app or app.count(NEW_ROUTE) != 1: raise RuntimeError("Handler canônico de Assuntos Jurídicos inválido")
    validate_previous_owners(app); validate_legal_sidebar(app)
    APP.write_text(app, encoding="utf-8")
    module_css = MODULE_CSS.read_text(encoding="utf-8").rstrip() + "\n" + CONSISTENCY_CSS.read_text(encoding="utf-8")
    css = replace_css(CSS.read_text(encoding="utf-8"), "VALTREN LEGAL MATTERS", module_css)
    CSS.write_text(css, encoding="utf-8"); update_cache_version()
    print("Jurídico → Assuntos Jurídicos materializado como owner canônico de demandas, partes, prazos, eventos, risco, documentos e acordos; escala visual normalizada; sem criar movimentos financeiros.")
    return 1

if __name__ == "__main__": apply_crm_legal_matters()
