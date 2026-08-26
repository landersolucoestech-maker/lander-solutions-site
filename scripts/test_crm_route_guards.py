from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
WORKFLOWS = ROOT / ".github" / "workflows"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def workflow_text() -> str:
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(WORKFLOWS.glob("*.yml")))
    text += "\n" + "\n".join(path.read_text(encoding="utf-8") for path in sorted(WORKFLOWS.glob("*.yaml")))
    return text


def scan_materialized_admin_expectations() -> None:
    # Historical assertions are allowed only as exact replacement anchors in the
    # sanctioned source/wrapper files below. They must never become an executable
    # final-materialized contract again.
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
    for path in sorted((ROOT / "scripts").glob("test*.js*")):
        text = path.read_text(encoding="utf-8")
        if legacy_pattern.search(text) and path.name not in sanctioned:
            unexpected.append(path.name)
    require(
        not unexpected,
        f"Expectations materializadas históricas de Administração encontradas fora das âncoras sancionadas: {unexpected}",
    )

    wrapper = (ROOT / "scripts" / "test_materialized_admin_compatibility.js").read_text(encoding="utf-8")
    for target in (
        "test_crm_fiscal_documents.js",
        "test_crm_cost_allocations.js",
        "test_crm_payouts.js",
        "test_crm_business.js",
    ):
        require(target in wrapper, f"Wrapper comum não mapeia {target}")
    require("Administração legacy preservada fora da Sidebar" in wrapper, "Wrapper comum não exige Administração fora da Sidebar")
    require("Áreaadministrativaaindanãoimplementadacomodomíniooperacional." in wrapper, "Wrapper comum não exige mensagem legacy honesta")

    dedicated_wrappers = {
        "Accounting": ("test_crm_accounting.js", "test_crm_accounting.base.js"),
        "Contratos": ("test_crm_legal_contracts.js", "test_crm_legal_contracts.base.js"),
        "Contratos UI": ("test_crm_legal_contracts_ui.js", "test_crm_legal_contracts_ui.base.js"),
        "Participações": ("test_crm_economic_participations.js", ".part"),
        "Participações UI": ("test_crm_economic_participations_ui.js", ".part"),
        "Repasses UI": ("test_crm_payouts_ui.js", "test_crm_payouts_ui.base.js"),
    }
    for label, (filename, backing) in dedicated_wrappers.items():
        text = (ROOT / "scripts" / filename).read_text(encoding="utf-8")
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
    scripts = ROOT / "scripts"
    wrapper_path = scripts / "test_crm_cost_allocations_ui.js"
    base_path = scripts / "test_crm_cost_allocations_ui.base.js"
    require(wrapper_path.exists(), "Wrapper materializado de Rateios UI ausente")
    require(base_path.exists(), "Base canônica de Rateios UI ausente")

    base_bytes = base_path.read_bytes()
    require(
        git_blob_sha(base_bytes) == "098cf1ef08b22be9e30d2837d3b998d4fbfe2c4f",
        "Base de Rateios UI divergiu do blob canônico 098cf1ef08b22be9e30d2837d3b998d4fbfe2c4f",
    )
    wrapper = wrapper_path.read_text(encoding="utf-8")
    require("test_crm_cost_allocations_ui.base.js" in wrapper, "Wrapper de Rateios UI não referencia a base canônica")
    require("process.argv.includes('--materialized')" in wrapper, "Wrapper de Rateios UI não separa source de materialized")
    require("oldSidebarOfficial" in wrapper and "oldSidebarBoundary" in wrapper, "Wrapper de Rateios UI não ancora testes 74 e 75")
    require("VALTREN SIDEBAR ARCHITECTURE START" in wrapper, "Wrapper de Rateios UI não usa marker START")
    require("VALTREN SIDEBAR ARCHITECTURE END" in wrapper, "Wrapper de Rateios UI não usa marker END")
    for token in ("Direcionadores", "Critérios de Rateio", "Alocações", "Memória de Cálculo"):
        require(token in wrapper, f"Wrapper de Rateios UI perdeu verificação do termo: {token}")
    require("lastIndexOf('function crmRelSidebar')" in wrapper, "Âncora histórica exata do wrapper de Rateios UI não está presente")
    require("indexOf('function crmReferenceRoute'" in wrapper, "Âncora histórica exata de crmReferenceRoute não está presente")

    workflows = workflow_text()
    require("test_crm_cost_allocations_ui.base.js --materialized" not in workflows, "Workflow não pode executar a base de Rateios UI diretamente em --materialized")
    require(
        "scripts/test_crm_cost_allocations_ui.js --materialized" in workflows,
        "Workflow não executa o wrapper de Rateios UI em --materialized",
    )


def scan_fragile_sidebar_boundaries() -> None:
    # Legacy boundaries are permitted only as exact, inert replacement anchors in
    # the Rateios UI base/wrapper pair. Executable materialized checks must use the
    # canonical START/END markers.
    old_74 = "test('74 sidebar publicado continua oficial',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);['Transações','Contabilidade','Notas Fiscais','Rateios','Participações','Repasses'].forEach((x)=>assert(sidebar.includes(x)));});"
    old_75 = "test('75 nenhum subitem de Rateios foi publicado no sidebar',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),sidebar=app.slice(start,end);['Direcionadores','Critérios de Rateio','Alocações','Memória de Cálculo'].forEach((x)=>assert(!sidebar.includes(x)));});"
    allowed_exact = {
        "test_crm_cost_allocations_ui.base.js": (old_74, old_75),
        "test_crm_cost_allocations_ui.js": (old_74, old_75),
    }
    fragile_tokens = (
        "lastIndexOf('function crmRelSidebar')",
        'lastIndexOf("function crmRelSidebar")',
        "indexOf('function crmReferenceRoute'",
        'indexOf("function crmReferenceRoute"',
        "app.rfind(\"function crmRelSidebar\")",
        "app.find(\"function crmReferenceRoute\"",
    )
    unexpected_boundaries: list[str] = []
    positive_legacy_sidebar_expectations: list[str] = []
    legacy_labels = ("ValtrenChat", "RH", "Administração", "Estrutura Organizacional", "Patrimônio e Licenças")

    for path in sorted((ROOT / "scripts").glob("test*.js*")):
        text = path.read_text(encoding="utf-8")
        scrubbed = text
        for anchor in allowed_exact.get(path.name, ()):
            count = scrubbed.count(anchor)
            require(count == 1, f"Âncora histórica de boundary esperada exatamente 1 vez em {path.name}; encontrada {count}")
            scrubbed = scrubbed.replace(anchor, "", 1)
        if any(token in scrubbed for token in fragile_tokens):
            unexpected_boundaries.append(path.name)

        for line_no, line in enumerate(text.splitlines(), start=1):
            if "sidebar.includes" not in line or "assert(" not in line:
                continue
            if "!sidebar.includes" in line:
                continue
            if any(label in line for label in legacy_labels):
                positive_legacy_sidebar_expectations.append(f"{path.name}:{line_no}")

    require(
        not unexpected_boundaries,
        f"Boundaries frágeis de Sidebar encontrados fora das âncoras exatas sancionadas: {unexpected_boundaries}",
    )
    require(
        not positive_legacy_sidebar_expectations,
        "Expectations positivas de item legacy na Sidebar encontradas em: " + ", ".join(positive_legacy_sidebar_expectations),
    )


def main() -> int:
    require(APP.exists(), "app.js materializado ausente")
    app = APP.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", app)

    expected = {
        "Dashboard + alias /crm": "elseif(path==='/crm/dashboard'||path==='/crm')app.innerHTML=crmDashboardPage(query);",
        "CRM": "elseif(path==='/crm/relationships')app.innerHTML=crmRelationshipsPage(query);",
        "Agenda": "elseif(path==='/crm/agenda')app.innerHTML=crmAgendaPage(query);",
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
        "Marketing": "if(path.startsWith('/crm/marketing'))returncrmMarketingUnavailablePage();",
        "Negócios / Produtos": "if(path==='/crm/negocios')returncrmBusinessProductsPage();",
        "Negócios / Serviços": "if(path==='/crm/negocios/servicos')returncrmBusinessServicesPage();",
        "Negócios / Unidades": "if(path==='/crm/negocios/unidades')returncrmBusinessUnitsPage();",
        "Relatórios": "if(path==='/crm/relatorios')",
        "Configurações": "if(path==='/crm/configuracoes')returncrmCanonicalSettingsPage();",
        "ValtrenChat legacy": "if(path==='/crm/valtrenchat'||path==='/crm/musicchat')returncrmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);",
    }
    missing = [label for label, token in expected.items() if token not in compact]
    require(not missing, f"Rotas canônicas/compatíveis ausentes ou divergentes: {missing}")

    # Compatibility routes are certified by observable contract, not by forcing a
    # particular placeholder implementation. This prevents the guard from becoming
    # an owner of RH/Administração while still requiring honest behavior.
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
    scan_fragile_sidebar_boundaries()
    print(f"route-guards: PASS ({len(expected) + 6} contratos verificados; crmRelSidebar=1; admin-expectations=clean; boundaries=clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
