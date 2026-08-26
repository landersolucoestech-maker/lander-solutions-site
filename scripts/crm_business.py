from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_business_core.js"
BROWSER = ROOT / "scripts" / "crm_business_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_business.css"
CACHE_VERSION = "20260826-business-catalog-v1"
JS_START = "  // VALTREN BUSINESS CATALOG START\n"
JS_END = "  // VALTREN BUSINESS CATALOG END\n"


def _replace_one_line_function(app: str, name: str, replacement: str) -> str:
    pattern = rf"function {re.escape(name)}\([^\n]*\)\{{[^\n]*\}}"
    matches = list(re.finditer(pattern, app))
    if len(matches) != 1:
        raise RuntimeError(f"Adapter {name} divergente: {len(matches)} ocorrência(s)")
    return re.sub(pattern, replacement, app, count=1)


def _replace_block_function(app: str, name: str, next_name: str, replacement: str) -> str:
    pattern = rf"function {re.escape(name)}\([^\n]*?\)\{{.*?\n\}}\nfunction {re.escape(next_name)}"
    matches = list(re.finditer(pattern, app, flags=re.S))
    if len(matches) != 1:
        raise RuntimeError(f"Adapter em bloco {name} divergente: {len(matches)} ocorrência(s)")
    return re.sub(pattern, replacement + "\nfunction " + next_name, app, count=1, flags=re.S)


def _assert_business_code_generator(source: str, location: str) -> None:
    """Validate the canonical generator structurally instead of grepping runtime codes."""
    compact = re.sub(r"\s+", "", source)
    checks = {
        "mapeamento product → PRD, service → SRV e business_unit → BU": "constprefix=(kind)=>kind==='product'?'PRD':kind==='service'?'SRV':'BU';",
        "função nextCode usa o prefixo e a coleção da dimensão": "functionnextCode(kind){constp=prefix(kind),rows=entityRows(kind)||[]",
        "sequência usa o maior código existente sem colisão": "constnext=(numbers.length?Math.max(...numbers):0)+1",
        "padding determinístico de três dígitos": "String(next).padStart(3,'0')",
        "Produto usa nextCode(product)": "input.code||nextCode('product')",
        "Serviço usa nextCode(service)": "input.code||nextCode('service')",
        "Unidade usa nextCode(business_unit)": "input.code||nextCode('business_unit')",
    }
    missing = [label for label, token in checks.items() if token not in compact]
    if missing:
        raise RuntimeError(f"Gerador canônico de códigos de Negócios inválido em {location}: {missing}")


def apply_crm_business() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()
    _assert_business_code_generator(core, "crm_business_core.js")

    # The Business owner runs after the already-materialized domains so these adapters
    # patch the final runtime helpers rather than being overwritten by later stages.
    app = re.sub(r"\n*  // VALTREN BUSINESS CATALOG START\n.*?  // VALTREN BUSINESS CATALOG END\n+", "\n", app, flags=re.S)
    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Negócios: {app.count(anchor)} ocorrência(s)")
    at = app.index(anchor)
    app = app[:at].rstrip("\n") + "\n\n" + block + "\n" + app[at:]

    business_start = app.find(JS_START)
    business_end = app.find(JS_END, business_start)
    if business_start < 0 or business_end <= business_start:
        raise RuntimeError("Bloco canônico de Negócios não localizado após injeção")
    _assert_business_code_generator(app[business_start:business_end + len(JS_END)], "app.js materializado")

    routes = {
        "if(path==='/crm/negocios')return crmArchitecturePlaceholderPage('business','products','Produtos');": "if(path==='/crm/negocios')return crmBusinessProductsPage();",
        "if(path==='/crm/negocios/servicos')return crmArchitecturePlaceholderPage('business','services','Serviços');": "if(path==='/crm/negocios/servicos')return crmBusinessServicesPage();",
        "if(path==='/crm/negocios/unidades')return crmArchitecturePlaceholderPage('business','units','Unidades de Negócio');": "if(path==='/crm/negocios/unidades')return crmBusinessUnitsPage();",
    }
    for old, new in routes.items():
        old_count, new_count = app.count(old), app.count(new)
        if old_count == 1 and new_count == 0:
            app = app.replace(old, new, 1)
        elif old_count == 0 and new_count == 1:
            pass
        else:
            raise RuntimeError(f"Rota de Negócios ambígua: placeholder={old_count}, handler={new_count}, rota={new}")

    # Minimal adapters: no workflow/calculation/status code from completed owners is changed.
    adapters = {
        "crmFinanceProducts": "function crmFinanceProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}):[];}",
        "crmFinanceProductLabel": "function crmFinanceProductLabel(tx){if(tx.businessDimension==='corporate')return 'Corporativo';if(tx.businessDimension==='product')return typeof crmBusinessDimensionLabel==='function'?crmBusinessDimensionLabel('product',tx.productId):(tx.productId||'Referência não resolvida');if(Array.isArray(tx.allocations)&&tx.allocations.length>1)return `${tx.allocations.length} destinos · Rateado`;return 'Selecionar';}",
        "crmAccountingProducts": "function crmAccountingProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}):[];}",
        "crmAccountingServices": "function crmAccountingServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}):[];}",
        "crmAccountingUnits": "function crmAccountingUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}):[];}",
        "crmFiscalProducts": "function crmFiscalProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmFiscalServices": "function crmFiscalServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmFiscalUnits": "function crmFiscalUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmCostAllocationProducts": "function crmCostAllocationProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmCostAllocationServices": "function crmCostAllocationServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmCostAllocationUnits": "function crmCostAllocationUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmCostAllocationResolveDestination": "function crmCostAllocationResolveDestination(type,id){if(type==='corporate')return true;return typeof crmBusinessService==='function'&&crmBusinessService().validateReference(type,id,{allowHistorical:false});}",
        "crmLegalProducts": "function crmLegalProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmLegalServices": "function crmLegalServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmLegalUnits": "function crmLegalUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}).filter((x)=>['active','paused'].includes(x.status)):[];}",
        "crmLegalResolveReference": "function crmLegalResolveReference(type,id){if(typeof crmBusinessResolveDimension!=='function')return null;const row=crmBusinessResolveDimension(type,id);return row.resolved&&!['archived','retired'].includes(row.status)?row:null;}",
        "crmParticipationProducts": "function crmParticipationProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}):[];}",
        "crmParticipationServices": "function crmParticipationServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}):[];}",
        "crmParticipationUnits": "function crmParticipationUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}):[];}",
        "crmParticipationReferenceLabel": "function crmParticipationReferenceLabel(row){if(row.productId)return crmBusinessDimensionLabel('product',row.productId);if(row.serviceId)return crmBusinessDimensionLabel('service',row.serviceId);if(row.businessUnitId)return crmBusinessDimensionLabel('business_unit',row.businessUnitId);return 'Geral';}",
        "crmPayoutProducts": "function crmPayoutProducts(){return typeof crmBusinessProductsFeed==='function'?crmBusinessProductsFeed({includeArchived:false}):[];}",
        "crmPayoutServices": "function crmPayoutServices(){return typeof crmBusinessServicesFeed==='function'?crmBusinessServicesFeed({includeArchived:false}):[];}",
        "crmPayoutUnits": "function crmPayoutUnits(){return typeof crmBusinessUnitsFeed==='function'?crmBusinessUnitsFeed({includeArchived:false}):[];}",
        "crmPayoutReferenceLabel": "function crmPayoutReferenceLabel(row){if(row.productId)return crmBusinessDimensionLabel('product',row.productId);if(row.serviceId)return crmBusinessDimensionLabel('service',row.serviceId);if(row.businessUnitId)return crmBusinessDimensionLabel('business_unit',row.businessUnitId);return 'Geral';}",
    }
    for name, replacement in adapters.items():
        app = _replace_one_line_function(app, name, replacement)

    cost_label = """function crmCostAllocationDestinationLabel(line){
  if(!line)return '—';
  if(line.destinationType==='corporate')return 'Corporativo';
  if(['product','service','business_unit'].includes(line.destinationType)&&typeof crmBusinessDimensionLabel==='function')return crmBusinessDimensionLabel(line.destinationType,line.destinationId);
  return line.destinationId||line.destinationType||'Referência não resolvida';
}"""
    app = _replace_block_function(app, "crmCostAllocationDestinationLabel", "crmCostAllocationPeriodRange", cost_label)

    required = [
        "ValtrenBusinessCore", "state.crmBusinessCatalog", "function crmBusinessProductsPage()", "function crmBusinessServicesPage()",
        "function crmBusinessUnitsPage()", "function crmBusinessProductsFeed", "function crmBusinessServicesFeed", "function crmBusinessUnitsFeed",
        "function crmBusinessResolveDimension", "Referência não resolvida", "potential_catalog_reference",
    ]
    missing = [x for x in required if x not in app]
    if missing:
        raise RuntimeError(f"Negócios incompleto no bundle: {missing}")
    for old, new in routes.items():
        if old in app or app.count(new) != 1:
            raise RuntimeError(f"Rota canônica de Negócios inválida após patch: {new}")

    previous_owners = [
        "if(path==='/crm/financeiro')return crmTransactionsPage();",
        "if(path==='/crm/financeiro/accounting')return crmAccountingPage();",
        "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();",
        "if(path==='/crm/financeiro/rateios'){const page=crmCostAllocationsPage();",
        "if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();",
        "if(path==='/crm/financeiro/repasses')return crmPayoutsPage();",
        "if(path==='/crm/juridico/contratos')return crmLegalContractsPage();",
        "if(path==='/crm/juridico/contratos/templates')return crmLegalTemplatesPage();",
        "if(path==='/crm/juridico/contratos/variaveis')return crmLegalVariablesPage();",
    ]
    regressions = [x for x in previous_owners if x not in app]
    if regressions:
        raise RuntimeError(f"Owner concluído sofreu regressão durante Negócios: {regressions}")

    sidebar_start_marker = "// VALTREN SIDEBAR ARCHITECTURE START"
    sidebar_end_marker = "// VALTREN SIDEBAR ARCHITECTURE END"
    sidebar_start = app.find(sidebar_start_marker)
    sidebar_end = app.find(sidebar_end_marker, sidebar_start + len(sidebar_start_marker)) if sidebar_start >= 0 else -1
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Markers canônicos da Sidebar não localizados")
    sidebar = app[sidebar_start:sidebar_end]
    business_at = sidebar.find("const business=[")
    business_end = sidebar.find("];", business_at)
    if business_at < 0 or business_end <= business_at:
        raise RuntimeError("Bloco Negócios do sidebar não localizado")
    business_sidebar = sidebar[business_at:business_end]
    for label in ["Produtos", "Serviços", "Unidades de Negócio"]:
        if label not in business_sidebar:
            raise RuntimeError(f"Sidebar Negócios sem item obrigatório: {label}")
    for label in ["Projetos", "Portfolio", "Portfólio", "Sistemas", "Categorias", "Planos", "Preços", "Modelos"]:
        if label in business_sidebar:
            raise RuntimeError(f"Submódulo indevido em Negócios: {label}")

    forbidden_parallel = ["state.financeProducts=", "state.accountingProducts=", "state.contractProducts=", "state.marketingProducts=", "state.fiscalServices=", "state.payoutBusinessUnits="]
    leaked = [x for x in forbidden_parallel if x in app]
    if leaked:
        raise RuntimeError(f"Catálogo paralelo detectado: {leaked}")
    forbidden_real_seed = ["Music OS 360", "Vivendo da Música", "Dica de Cria", "Visa Fácil"]
    seeded = [x for x in forbidden_real_seed if x in core or x in browser]
    if seeded:
        raise RuntimeError(f"Produto real foi hardcoded indevidamente: {seeded}")
    forbidden_responsibilities = ["createTransaction(", "createFiscalDocument(", "createContract(", "participationAmount", "payoutAmount", "taxAmount", "grossRevenue", "netRevenue"]
    leaked_domain = [x for x in forbidden_responsibilities if x in core]
    if leaked_domain:
        raise RuntimeError(f"Negócios contém responsabilidade financeira/jurídica indevida: {leaked_domain}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN BUSINESS CATALOG \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", value)
        value = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", value)
        path.write_text(value, encoding="utf-8")

    print("Negócios → Produtos, Serviços e Unidades de Negócio materializados como catálogo canônico único; módulos concluídos recebem apenas adapters de lookup/label/validação.")
    return 1


if __name__ == "__main__":
    apply_crm_business()
