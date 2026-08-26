from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
    for forbidden_label in ("ValtrenChat", "RH", "Administração"):
        require(forbidden_label not in sidebar, f"Item legacy indevido reapareceu na Sidebar: {forbidden_label}")

    declarations = re.findall(r"(?m)^\s*function\s+crmRelSidebar\s*\(", app)
    require(len(declarations) == 1, f"crmRelSidebar declarations != 1: {len(declarations)}")

    print(f"route-guards: PASS ({len(expected) + 6} contratos verificados; crmRelSidebar=1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
