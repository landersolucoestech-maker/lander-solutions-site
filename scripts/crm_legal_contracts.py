from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MODULE_DIR = ROOT / "web" / "src" / "modules" / "legal" / "contracts"
CORE = MODULE_DIR / "core.js"
BROWSER = MODULE_DIR / "browser.js"
MODULE_CSS = MODULE_DIR / "styles.css"
CACHE_VERSION = "20260829-legal-contracts-module-v1"
JS_START = "  // VALTREN LEGAL CONTRACTS START\n"
JS_END = "  // VALTREN LEGAL CONTRACTS END\n"


def apply_crm_legal_contracts() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()

    old_contract_actions = "const actions=`<button type=\"button\" class=\"primary\" data-action=\"crm-legal-new-contract\">${icon('plus',14)} Novo Contrato</button>`;"
    new_contract_actions = "const actions=`<a class=\"crm-legal-secondary-action\" href=\"#/crm/juridico/contratos/templates\">Templates</a><a class=\"crm-legal-secondary-action\" href=\"#/crm/juridico/contratos/variaveis\">Variáveis</a><button type=\"button\" class=\"primary\" data-action=\"crm-legal-new-contract\">${icon('plus',14)} Novo Contrato</button>`;"
    if browser.count(old_contract_actions) != 1:
        raise RuntimeError(f"Ações canônicas do Page Header de Contratos divergentes: {browser.count(old_contract_actions)}")
    browser = browser.replace(old_contract_actions, new_contract_actions, 1)

    app = re.sub(
        r"\n?  // VALTREN LEGAL CONTRACTS START\n.*?  // VALTREN LEGAL CONTRACTS END\n",
        "\n",
        app,
        flags=re.S,
    )

    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Contratos: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    routes = {
        "if(path==='/crm/juridico/contratos')return crmArchitecturePlaceholderPage('legal','contracts','Contratos');":
            "if(path==='/crm/juridico/contratos')return crmLegalContractsPage();",
        "if(path==='/crm/juridico/contratos/templates')return crmArchitecturePlaceholderPage('legal','contracts-templates','Templates');":
            "if(path==='/crm/juridico/contratos/templates')return crmLegalTemplatesPage();",
        "if(path==='/crm/juridico/contratos/variaveis')return crmArchitecturePlaceholderPage('legal','contracts-variables','Variáveis');":
            "if(path==='/crm/juridico/contratos/variaveis')return crmLegalVariablesPage();",
    }
    for old, new in routes.items():
        if app.count(old) != 1:
            raise RuntimeError(f"Placeholder contratual não encontrado de forma inequívoca: {old}")
        app = app.replace(old, new, 1)

    required = [
        "ValtrenContractCore",
        "state.crmLegalContracts",
        "function crmLegalContractsPage()",
        "function crmLegalTemplatesPage()",
        "function crmLegalVariablesPage()",
        "function crmContractEconomicRulesFeed",
        "function crmContractResolveEconomicRuleForPeriod",
        "Novo Contrato",
        "Novo Template",
        "Preview A4",
        "Condições Econômicas",
        "Participações (não implementado nesta etapa)",
        "EMPRESA.RAZAO_SOCIAL",
        "CLIENTE.NOME",
        "CONTRATO.NUMERO",
        "PRODUTO.NOME",
        "SERVICO.NOME",
        "UNIDADE.NOME",
        "crm-legal-secondary-action",
        "#/crm/juridico/contratos/templates",
        "#/crm/juridico/contratos/variaveis",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Contratos incompleto no bundle: {missing}")

    for old in routes:
        if old in app:
            raise RuntimeError("Placeholder de Contratos sobreviveu no bundle")

    untouched_legal = [
        "if(path==='/crm/juridico')return crmArchitecturePlaceholderPage('legal','matters','Assuntos Jurídicos');",
        "if(path==='/crm/juridico/compliance')return crmArchitecturePlaceholderPage('legal','compliance','Compliance e Políticas');",
        "if(path==='/crm/juridico/propriedade-intelectual')return crmArchitecturePlaceholderPage('legal','ip','Propriedade Intelectual');",
        "if(path==='/crm/juridico/societario')return crmArchitecturePlaceholderPage('legal','corporate','Societário');",
    ]
    missing_untouched = [route for route in untouched_legal if route not in app]
    if missing_untouched:
        raise RuntimeError(f"Módulo Jurídico fora do escopo foi alterado: {missing_untouched}")

    finance_required = [
        "if(path==='/crm/financeiro')return crmTransactionsPage();",
        "if(path==='/crm/financeiro/accounting')return crmAccountingPage();",
        "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();",
        "if(path==='/crm/financeiro/rateios'){const page=crmCostAllocationsPage();",
    ]
    missing_finance = [route for route in finance_required if route not in app]
    if missing_finance:
        raise RuntimeError(f"Stack Financeiro sofreu regressão durante Contratos: {missing_finance}")

    participation_placeholders = [
        "if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage('accounting','participacoes','Participações');",
        "if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage('accounting','participations','Participações');",
    ]
    payout_placeholders = [
        "if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage('accounting','repasses','Repasses');",
        "if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage('accounting','payouts','Repasses');",
    ]
    if not any(marker in app for marker in participation_placeholders):
        raise RuntimeError("Financeiro → Participações deixou de permanecer placeholder")
    if not any(marker in app for marker in payout_placeholders):
        raise RuntimeError("Financeiro → Repasses deixou de permanecer placeholder")

    if "createTransaction(" in browser or "createFiscalDocument(" in browser:
        raise RuntimeError("Jurídico → Contratos não pode criar Transação ou Nota Fiscal")
    if "participationAmount" in core or "payoutAmount" in core:
        raise RuntimeError("Contratos não pode calcular Participação ou Repasse")

    sidebar_start = app.find("// VALTREN SIDEBAR ARCHITECTURE START")
    sidebar_end = app.find("// VALTREN SIDEBAR ARCHITECTURE END", sidebar_start)
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Bloco canônico da Sidebar não localizado para validação")
    sidebar = app[sidebar_start:sidebar_end]
    expected_legal = [
        "Assuntos Jurídicos",
        "Contratos",
        "Compliance e Políticas",
        "Propriedade Intelectual",
        "Societário",
    ]
    missing_sidebar = [label for label in expected_legal if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar Jurídico sofreu regressão: {missing_sidebar}")
    if "#/crm/juridico/contratos" not in sidebar:
        raise RuntimeError("Link direto de Contratos desapareceu da Sidebar")
    forbidden_sidebar = [
        "#/crm/juridico/contratos/templates",
        "#/crm/juridico/contratos/variaveis",
        ">Templates<",
        ">Variáveis<",
        "Cláusulas",
        "Aprovações",
        "Assinaturas",
        "Regras Econômicas",
        "Participantes",
    ]
    leaked = [token for token in forbidden_sidebar if token in sidebar]
    if leaked:
        raise RuntimeError(f"Submódulo contratual indevido foi adicionado ao sidebar: {leaked}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN LEGAL CONTRACTS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text_value = path.read_text(encoding="utf-8")
        text_value = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text_value)
        text_value = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text_value)
        path.write_text(text_value, encoding="utf-8")

    print("Jurídico → Contratos materializado a partir de web/src/modules/legal/contracts; Templates e Variáveis permanecem subordinados ao módulo de Contratos.")
    return 1


if __name__ == "__main__":
    apply_crm_legal_contracts()
