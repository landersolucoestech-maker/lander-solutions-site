from __future__ import annotations
from pathlib import Path
from crm_legal_materializer_utils import APP, CSS, replace_marked_block, replace_route, replace_css, validate_legal_sidebar, validate_previous_owners, update_cache_version
from crm_accessibility_semantics import OWNER_STATIC_LABELS, apply_accessible_names

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "src" / "modules" / "legal" / "intellectual-property"
CORE = MODULE_DIR / "core.js"
BROWSER = MODULE_DIR / "browser.js"
MODULE_CSS = MODULE_DIR / "styles.css"
CONSISTENCY_CSS = MODULE_DIR / "consistency.css"
JS_START = "  // VALTREN INTELLECTUAL PROPERTY START\n"
JS_END = "  // VALTREN INTELLECTUAL PROPERTY END\n"
OLD_ROUTE = "if(path==='/crm/juridico/propriedade-intelectual')return crmArchitecturePlaceholderPage('legal','ip','Propriedade Intelectual');"
NEW_ROUTE = "if(path==='/crm/juridico/propriedade-intelectual')return crmIntellectualPropertyPage();"

def apply_crm_intellectual_property() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS, CONSISTENCY_CSS):
        if not path.exists(): raise FileNotFoundError(path)
    app = APP.read_text(encoding="utf-8"); core = CORE.read_text(encoding="utf-8").strip(); browser = apply_accessible_names(BROWSER.read_text(encoding="utf-8").strip(), OWNER_STATIC_LABELS["intellectual_property"])
    if any(x in core for x in ["softwareLicenseSeat", "operationalLicense", "createTransaction(", "createContract("]): raise RuntimeError("Propriedade Intelectual contém responsabilidade indevida")
    app = replace_marked_block(app, JS_START, JS_END, core + "\n\n" + browser)
    app = replace_route(app, OLD_ROUTE, NEW_ROUTE, "Propriedade Intelectual")
    required = ["ValtrenIntellectualPropertyCore", "state.crmIntellectualProperty", "function crmIntellectualPropertyPage()", "function crmIntellectualPropertyFeed", "function crmIntellectualPropertyDeadlinesFeed", "termsOwner:'contract'", "Status registrado exige número de registro", "metadata-only"]
    missing = [x for x in required if x not in app]
    if missing: raise RuntimeError(f"Propriedade Intelectual incompleta no bundle: {missing}")
    if OLD_ROUTE in app or app.count(NEW_ROUTE) != 1: raise RuntimeError("Handler canônico de Propriedade Intelectual inválido")
    validate_previous_owners(app); validate_legal_sidebar(app)
    APP.write_text(app, encoding="utf-8")
    module_css = MODULE_CSS.read_text(encoding="utf-8").rstrip() + "\n" + CONSISTENCY_CSS.read_text(encoding="utf-8")
    CSS.write_text(replace_css(CSS.read_text(encoding="utf-8"), "VALTREN INTELLECTUAL PROPERTY", module_css), encoding="utf-8"); update_cache_version()
    print("Jurídico → Propriedade Intelectual materializado a partir de src/modules/legal/intellectual-property.")
    return 1

if __name__ == "__main__": apply_crm_intellectual_property()
