from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
SCRIPTS = ROOT / "scripts"
WORKFLOWS = ROOT / ".github" / "workflows"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def workflow_text() -> str:
    files = [*sorted(WORKFLOWS.glob("*.yml")), *sorted(WORKFLOWS.glob("*.yaml"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def scan_materialized_admin_expectations() -> None:
    sanctioned = {
        "test_crm_accounting.base.js",
        "test_crm_accounting.js",
        "test_crm_fiscal_documents.js",
        "test_crm_cost_allocations.js",
        "test_crm_legal_contracts.base.js",
        "test_crm_legal_contracts.js",
        "test_crm_legal_contracts_ui.base.js",
        "test_crm_legal_contracts_ui.js",
        "test_crm_economic_participations.js",
        "test_crm_economic_participations.js.part06",
        "test_crm_economic_participations_ui.js",
        "test_crm_economic_participations_ui.js.part03",
        "test_crm_payouts.js",
        "test_crm_payouts_ui.base.js",
        "test_crm_payouts_ui.js",
        "test_crm_business.js",
        "test_materialized_admin_compatibility.js",
    }
    legacy_pattern = re.compile(
        r"Administra(?:ção|cao)[^\n'`]{0,90}(?:dois itens|itens canônicos|dois itens canônicos atuais|preserva os dois itens)[\s\S]{0,900}?Estrutura Organizacional[\s\S]{0,900}?Patrimônio e Licenças",
        re.IGNORECASE,
    )
    unexpected: list[str] = []
    for path in sorted(SCRIPTS.glob("test*.js*")):
        text = path.read_text(encoding="utf-8")
        if legacy_pattern.search(text) and path.name not in sanctioned:
            unexpected.append(path.name)
    require(
        not unexpected,
        f"Expectations materializadas históricas de Administração encontradas fora das âncoras sancionadas: {unexpected}",
    )

    common = (SCRIPTS / "test_materialized_admin_compatibility.js").read_text(encoding="utf-8")
    for target in (
        "test_crm_fiscal_documents.js",
        "test_crm_cost_allocations.js",
        "test_crm_payouts.js",
        "test_crm_business.js",
    ):
        require(target in common, f"Wrapper comum não mapeia {target}")
    require("Administração legacy preservada fora da Sidebar" in common, "Wrapper comum não exige Administração fora da Sidebar")
    require("Áreaadministrativaaindanãoimplementadacomodomíniooperacional." in common, "Wrapper comum não exige mensagem legacy honesta")

    dedicated_wrappers = {
        "Accounting": ("test_crm_accounting.js", "test_crm_accounting.base.js"),
        "Contratos": ("test_crm_legal_contracts.js", "test_crm_legal_contracts.base.js"),
        "Contratos UI": ("test_crm_legal_contracts_ui.js", "test_crm_legal_contracts_ui.base.js"),
        "Participações": ("test_crm_economic_participations.js", ".part"),
        "Participações UI": ("test_crm_economic_participations_ui.js", ".part"),
        "Repasses UI": ("test_crm_payouts_ui.js", "test_crm_payouts_ui.base.js"),
    }
    for label, (filename, backing) in dedicated_wrappers.items():
        text = (SCRIPTS / filename).read_text(encoding="utf-8")
        require("Administração legacy preservada fora da Sidebar" in text, f"Wrapper de {label} não substitui a expectation histórica de Administração")
        require("Áreaadministrativaaindanãoimplementadacomodomíniooperacional." in text, f"Wrapper de {label} não exige compatibilidade honesta")
        require(backing in text, f"Wrapper de {label} não referencia sua base/parts canônica")

    workflows = workflow_text()
    for target in (
        "test_crm_fiscal_documents.js",
        "test_crm_cost_allocations.js",
        "test_crm_payouts.js",
        "test_crm_business.js",
    ):
        direct_patterns = (
            f"readonly_suite scripts/{target} --materialized",
            f"node scripts/{target} --materialized",
        )
        require(not any(pattern in workflows for pattern in direct_patterns), f"Workflow voltou a executar {target} diretamente em --materialized")
        required = f"test_materialized_admin_compatibility.js scripts/{target} --materialized"
        require(required in workflows, f"Workflow não usa wrapper materializado para {target}")


def scan_rateios_ui_wrapper_contract() -> None:
    wrapper_path = SCRIPTS / "test_crm_cost_allocations_ui.js"
    base_path = SCRIPTS / "test_crm_cost_allocations_ui.base.js"
    require(wrapper_path.exists(), "Wrapper materializado de Rateios UI ausente")
    require(base_path.exists(), "Base canônica de Rateios UI ausente")
    require(
        git_blob_sha(base_path.read_bytes()) == "098cf1ef08b22be9e30d2837d3b998d4fbfe2c4f",
        "Base de Rateios UI divergiu do blob canônico 098cf1ef08b22be9e30d2837d3b998d4fbfe2c4f",
    )
    wrapper = wrapper_path.read_text(encoding="utf-8")
    require("test_crm_cost_allocations_ui.base.js" in wrapper, "Wrapper de Rateios UI não referencia a base canônica")
    require("process.argv.includes('--materialized')" in wrapper, "Wrapper de Rateios UI não separa source de materialized")
    require("oldSidebarOfficial" in wrapper and "oldSidebarBoundary" in wrapper, "Wrapper de Rateios UI não ancora testes 74 e 75")
    require("VALTREN SIDEBAR ARCHITECTURE START" in wrapper and "VALTREN SIDEBAR ARCHITECTURE END" in wrapper, "Wrapper de Rateios UI não usa os markers canônicos")
    for token in ("Direcionadores", "Critérios de Rateio", "Alocações", "Memória de Cálculo"):
        require(token in wrapper, f"Wrapper de Rateios UI perdeu verificação do termo: {token}")
    require("lastIndexOf('function crmRelSidebar')" in wrapper, "Âncora histórica de Rateios UI não está presente")
    require("indexOf('function crmReferenceRoute'" in wrapper, "Âncora histórica crmReferenceRoute de Rateios UI não está presente")

    workflows = workflow_text()
    require("test_crm_cost_allocations_ui.base.js --materialized" not in workflows, "Workflow não pode executar a base de Rateios UI diretamente em --materialized")
    require("scripts/test_crm_cost_allocations_ui.js --materialized" in workflows, "Workflow não executa o wrapper de Rateios UI em --materialized")


def scan_new_wrapper_bases() -> None:
    expected = {
        "test_crm_complete.base.js": ("19f2832c02a3ea03c448407e90f6a9ca919b71a3", "test_crm_complete.js"),
        "test_crm_complete_hardening.base.js": ("86579a695989fcf57d7757dd66d551a1fcff7d8d", "test_crm_complete_hardening.js"),
        "test_crm_financial_transactions.base.js": ("7a9b24c8c093294b7989720755a678abbec31016", "test_crm_financial_transactions.js"),
        "test_crm_fiscal_documents_ui.base.js": ("a397117f4ea459b47cb39b3a4b0d637700cb3457", "test_crm_fiscal_documents_ui.js"),
        "test_crm_legal_matters_ui.base.js": ("737658eddd83195981a0dd41fe11152ce8f59586", "test_crm_legal_matters_ui.js"),
    }
    generic = (SCRIPTS / "test_materialized_sidebar_boundaries.js").read_text(encoding="utf-8")
    require("module.exports={specs,transform,runBase}" in generic, "Wrapper genérico de boundary não exporta contrato reutilizável")
    require("VALTREN SIDEBAR ARCHITECTURE START" in generic and "VALTREN SIDEBAR ARCHITECTURE END" in generic, "Wrapper genérico não usa markers canônicos")
    workflows = workflow_text()
    for base_name, (blob_sha, wrapper_name) in expected.items():
        base_path = SCRIPTS / base_name
        wrapper_path = SCRIPTS / wrapper_name
        require(base_path.exists(), f"Base canônica ausente: {base_name}")
        require(git_blob_sha(base_path.read_bytes()) == blob_sha, f"Base canônica divergiu do blob esperado: {base_name}")
        wrapper = wrapper_path.read_text(encoding="utf-8")
        require(base_name in wrapper, f"Wrapper {wrapper_name} não referencia {base_name}")
        require("test_materialized_sidebar_boundaries.js" in wrapper, f"Wrapper {wrapper_name} não usa o helper canônico de boundary")
        require(wrapper_name in generic, f"Helper genérico não mapeia {wrapper_name}")
        require(f"scripts/{base_name} --materialized" not in workflows, f"Workflow executa base diretamente em materialized: {base_name}")
        require(f"scripts/{wrapper_name} --materialized" in workflows, f"Workflow não executa wrapper em materialized: {wrapper_name}")


def scan_fragile_sidebar_boundaries() -> None:
    historical_sources = {
        "test_crm_accounting.base.js": 1,
        "test_crm_complete.base.js": 2,
        "test_crm_complete_hardening.base.js": 1,
        "test_crm_financial_transactions.base.js": 2,
        "test_crm_fiscal_documents.js": 1,
        "test_crm_fiscal_documents_ui.base.js": 1,
        "test_crm_cost_allocations.js": 2,
        "test_crm_cost_allocations_ui.base.js": 2,
        "test_crm_legal_contracts_ui.base.js": 3,
        "parts/tests/economic_participations/test_crm_economic_participations_ui.js.part03": 2,
        "test_crm_payouts.js": 1,
        "test_crm_payouts_ui.base.js": 1,
        "test_crm_legal_matters_ui.base.js": 1,
    }
    boundary_wrappers = {
        "test_crm_accounting.js",
        "test_materialized_admin_compatibility.js",
        "test_crm_cost_allocations_ui.js",
        "test_crm_legal_contracts_ui.js",
        "test_crm_economic_participations_ui.js",
        "test_crm_payouts_ui.js",
        "test_materialized_sidebar_boundaries.js",
    }
    negative_validators = {"test_crm_business_ui.js", "test_crm_sidebar_architecture.js"}
    js_start = "lastIndexOf('function crmRelSidebar')"
    js_end = "indexOf('function crmReferenceRoute'"
    py_start = 'app.rfind("function crmRelSidebar")'
    py_end = 'app.find("function crmReferenceRoute"'
    fragile_tokens = (js_start, js_end, py_start, py_end)

    for filename, expected_count in historical_sources.items():
        text = (SCRIPTS / filename).read_text(encoding="utf-8")
        require(text.count(js_start) == expected_count, f"Contagem de boundary START histórica inesperada em {filename}")
        require(text.count(js_end) == expected_count, f"Contagem de boundary END histórica inesperada em {filename}")

    for filename in boundary_wrappers:
        text = (SCRIPTS / filename).read_text(encoding="utf-8")
        require("VALTREN SIDEBAR ARCHITECTURE START" in text, f"Wrapper {filename} não aponta para marker START")
        require("VALTREN SIDEBAR ARCHITECTURE END" in text, f"Wrapper {filename} não aponta para marker END")

    for filename in negative_validators:
        text = (SCRIPTS / filename).read_text(encoding="utf-8")
        for line in text.splitlines():
            if any(token in line for token in (py_start, py_end)):
                require(("assert(!" in line or "must(!" in line) and "includes" in line, f"Boundary Python legado não está em assertion negativa em {filename}")

    known = set(historical_sources) | boundary_wrappers | negative_validators
    unexpected: list[str] = []
    for path in sorted(SCRIPTS.glob("test*.js*")):
        if path.name in known:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in fragile_tokens):
            unexpected.append(path.name)
    require(not unexpected, f"Boundary frágil de Sidebar encontrado fora dos harnesses explicitamente tratados: {unexpected}")

    legacy_labels = ("ValtrenChat", "RH", "Administração", "Estrutura Organizacional", "Patrimônio e Licenças")
    positive: list[str] = []
    for path in sorted(SCRIPTS.glob("test*.js*")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not any(label in line for label in legacy_labels):
                continue
            if "sidebar.includes" in line and "!sidebar.includes" not in line:
                positive.append(f"{path.name}:{line_no}")
            if "hasAll(sidebar" in line and any(label in line for label in legacy_labels):
                positive.append(f"{path.name}:{line_no}")
    require(not positive, "Expectations positivas de item legacy na Sidebar encontradas em: " + ", ".join(sorted(set(positive))))


def main() -> int:
    require(APP.exists(), "app.js materializado ausente")
    app = APP.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", app)

    expected = {
        "Dashboard global": "path==='/dashboard'",
        "Dashboard alias legacy": "path==='/crm/dashboard'||path==='/crm'",
        "CRM": "path==='/crm/relationships'",
        "Agenda global": "path==='/agenda'",
        "Agenda alias legacy": "path==='/crm/agenda'",
        "Financeiro / Transações": "if(path==='/crm/financeiro')returncrmTransactionsPage();",
        "Financeiro / Contabilidade": "if(path==='/crm/financeiro/accounting')returncrmAccountingPage();",
        "Financeiro / Notas Fiscais": "if(path==='/crm/financeiro/notas-fiscais')returncrmFiscalDocumentsPage();",
        "Financeiro / Rateios": "if(path==='/crm/financeiro/rateios'){constpage=crmCostAllocationsPage();",
        "Financeiro / Participações": "if(path==='/crm/financeiro/participacoes')returncrmEconomicParticipationsPage();",
        "Financeiro / Repasses": "if(path==='/crm/financeiro/repasses')returncrmPayoutsPage();",
        "Jurídico / Assuntos": "if(path==='/crm/juridico')returncrmLegalMattersPage();",
        "Jurídico / Contratos": "if(path==='/crm/juridico/contratos')returncrmLegalContractsPage();",
        "Jurídico / Templates": "if(path==='/crm/juridico/contratos/templates')returncrmLegalTemplatesPage();",
        "Jurídico / Variáveis": "if(path==='/crm/juridico/contratos/variaveis')returncrmLegalVariablesPage();",
        "Jurídico / Compliance": "if(path==='/crm/juridico/compliance')returncrmCompliancePage();",
        "Jurídico / Propriedade Intelectual": "if(path==='/crm/juridico/propriedade-intelectual')returncrmIntellectualPropertyPage();",
        "Jurídico / Societário": "if(path==='/crm/juridico/societario')returncrmCorporateGovernancePage();",
        "Marketing": "if(path.startsWith('/crm/marketing'))returncrmMarketingPage(path);",
        "Negócios / Produtos": "if(path==='/crm/negocios')returncrmBusinessProductsPage();",
        "Negócios / Serviços": "if(path==='/crm/negocios/servicos')returncrmBusinessServicesPage();",
        "Negócios / Unidades": "if(path==='/crm/negocios/unidades')returncrmBusinessUnitsPage();",
        "Relatórios": "if(path==='/crm/relatorios')",
        "Configurações": "if(path==='/crm/configuracoes')returncrmCanonicalSettingsPage();",
        "ValtrenChat legacy": "if(path==='/crm/valtrenchat'||path==='/crm/musicchat')returncrmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);",
    }
    missing = [label for label, token in expected.items() if token not in compact]
    require(not missing, f"Rotas canônicas/compatíveis ausentes ou divergentes: {missing}")

    require("path==='/crm/rh'" in compact, "Rota legacy de RH ausente")
    require("DomíniodeRHaindanãoimplementado." in compact, "RH legacy não informa honestamente que não está implementado")
    require("path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas'" in compact, "Rotas legacy de Administração ausentes")
    require("Áreaadministrativaaindanãoimplementadacomodomíniooperacional." in compact, "Administração legacy não informa honestamente que não está implementada")
    require("Não configurado" in app, "Semântica canônica de integração 'Não configurado' ausente")

    forbidden_routes = {
        "placeholder Jurídico / Assuntos": "if(path==='/crm/juridico')returncrmArchitecturePlaceholderPage('legal','matters'",
        "placeholder Jurídico / Compliance": "if(path==='/crm/juridico/compliance')returncrmArchitecturePlaceholderPage",
        "placeholder Jurídico / PI": "if(path==='/crm/juridico/propriedade-intelectual')returncrmArchitecturePlaceholderPage",
        "placeholder Jurídico / Societário": "if(path==='/crm/juridico/societario')returncrmArchitecturePlaceholderPage",
        "placeholder Financeiro / Rateios": "if(path==='/crm/financeiro/rateios')returncrmArchitecturePlaceholderPage",
        "placeholder Financeiro / Participações": "if(path==='/crm/financeiro/participacoes')returncrmArchitecturePlaceholderPage",
        "placeholder Financeiro / Repasses": "if(path==='/crm/financeiro/repasses')returncrmArchitecturePlaceholderPage",
        "placeholder Negócios / Produtos": "if(path==='/crm/negocios')returncrmArchitecturePlaceholderPage",
        "placeholder Negócios / Serviços": "if(path==='/crm/negocios/servicos')returncrmArchitecturePlaceholderPage",
        "placeholder Negócios / Unidades": "if(path==='/crm/negocios/unidades')returncrmArchitecturePlaceholderPage",
    }
    leaked = [label for label, token in forbidden_routes.items() if token in compact]
    require(not leaked, f"Placeholder sobreviveu em owner já implementado: {leaked}")

    sidebar_start = app.find("// VALTREN SIDEBAR ARCHITECTURE START")
    sidebar_end = app.find("// VALTREN SIDEBAR ARCHITECTURE END", sidebar_start)
    require(sidebar_start >= 0 and sidebar_end > sidebar_start, "Bloco canônico da Sidebar ausente")
    sidebar = app[sidebar_start:sidebar_end]
    for required_label in ("Dashboard", "CRM", "Agenda", "Financeiro", "Jurídico", "Marketing", "Negócios", "Relatórios", "Configurações"):
        require(required_label in sidebar, f"Item canônico ausente da Sidebar: {required_label}")
    for forbidden_label in ("ValtrenChat", "RH", "Administração"):
        require(forbidden_label not in sidebar, f"Item legacy indevido reapareceu na Sidebar: {forbidden_label}")

    declarations = re.findall(r"(?m)^\s*function\s+crmRelSidebar\s*\(", app)
    require(len(declarations) == 1, f"crmRelSidebar declarations != 1: {len(declarations)}")

    scan_materialized_admin_expectations()
    scan_rateios_ui_wrapper_contract()
    scan_new_wrapper_bases()
    scan_fragile_sidebar_boundaries()
    print(f"route-guards: PASS ({len(expected) + 6} contratos verificados; crmRelSidebar=1; admin-expectations=clean; boundaries=clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
