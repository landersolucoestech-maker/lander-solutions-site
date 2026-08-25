from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CORE = ROOT / "scripts" / "crm_economic_participations_core.js"
BROWSER = ROOT / "scripts" / "crm_economic_participations_browser.js"
MODULE_CSS = ROOT / "scripts" / "crm_economic_participations.css"
CACHE_VERSION = "20260825-economic-participations-v1"
JS_START = "  // VALTREN ECONOMIC PARTICIPATIONS START\n"
JS_END = "  // VALTREN ECONOMIC PARTICIPATIONS END\n"


def apply_crm_economic_participations() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()

    app = re.sub(
        r"\n?  // VALTREN ECONOMIC PARTICIPATIONS START\n.*?  // VALTREN ECONOMIC PARTICIPATIONS END\n",
        "\n",
        app,
        flags=re.S,
    )

    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Participações: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    route_old = "if(path==='/crm/financeiro/participacoes')return crmArchitecturePlaceholderPage('accounting','participacoes','Participações');"
    route_new = "if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();"
    if app.count(route_old) != 1:
        raise RuntimeError(f"Placeholder canônico de Participações não encontrado de forma inequívoca: {app.count(route_old)}")
    app = app.replace(route_old, route_new, 1)

    # Contratos remains the rule owner, but its published integration note must no longer
    # claim that Participações is unimplemented after this owner is materialized.
    old_legal_note = "Cálculo financeiro: Financeiro → Participações (não implementado nesta etapa)."
    new_legal_note = "Cálculo financeiro: Financeiro → Participações consome estas regras sem alterar o Contrato."
    if old_legal_note not in app:
        raise RuntimeError("Nota de integração Contratos → Participações não encontrada")
    app = app.replace(old_legal_note, new_legal_note, 1)

    # The list KPI must aggregate the complete canonical state and must not silently
    # sum incompatible currencies. Normalize the published implementation here so
    # the materialized owner is correct even if the source UI is reused independently.
    summary_old = "function crmParticipationSummary(){const service=crmParticipationService(),all=service.query({limit:50}).rows,approved=service.query({workflowStatus:'approved',limit:50}).rows,review=service.query({workflowStatus:'review',limit:50}).total,blocked=all.filter((x)=>x.calculationStatus==='blocked').length,value=approved.filter((x)=>x.consistencyStatus==='consistent').reduce((sum,x)=>sum+Number(x.participationAmount||0),0);return `<section class=\"crm-part-summary\"><article><span>Participações calculadas</span><strong>${all.filter((x)=>x.calculationStatus==='calculated').length}</strong></article><article><span>Valor aprovado</span><strong>${crmParticipationMoney(value,'BRL')}</strong></article><article><span>Pendentes de revisão</span><strong>${review}</strong></article><article><span>Cálculos bloqueados</span><strong>${blocked}</strong></article></section>`;}"
    summary_new = "function crmParticipationSummary(){const service=crmParticipationService(),all=service.data.calculations.filter((x)=>!x.isDemo),approved=all.filter((x)=>x.workflowStatus==='approved'&&x.consistencyStatus==='consistent'),review=all.filter((x)=>x.workflowStatus==='review').length,blocked=all.filter((x)=>x.calculationStatus==='blocked').length,currencies=[...new Set(approved.map((x)=>x.currency||'BRL'))],value=approved.reduce((sum,x)=>sum+Number(x.participationAmount||0),0),approvedLabel=currencies.length>1?'Múltiplas moedas':crmParticipationMoney(value,currencies[0]||'BRL');return `<section class=\"crm-part-summary\"><article><span>Participações calculadas</span><strong>${all.filter((x)=>x.calculationStatus==='calculated').length}</strong></article><article><span>Valor aprovado</span><strong>${approvedLabel}</strong></article><article><span>Pendentes de revisão</span><strong>${review}</strong></article><article><span>Cálculos bloqueados</span><strong>${blocked}</strong></article></section>`;}"
    if summary_old not in app:
        raise RuntimeError("Implementação de resumo de Participações não encontrada")
    app = app.replace(summary_old, summary_new, 1)

    required = [
        "ValtrenParticipationCore",
        "state.crmEconomicParticipations",
        "function crmEconomicParticipationsPage()",
        "function crmParticipationService()",
        "function crmParticipationObligationsFeed(filters={})",
        "Calcular Participações",
        "Base de Cálculo",
        "Base Distribuível",
        "Memória de Cálculo",
        "Conflito contratual de vigência.",
        "sourceSnapshotHash",
        "ruleSnapshotHash",
        "crmContractEconomicRulesFeed",
        "crmContractResolveEconomicRuleForPeriod",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Participações incompleto no bundle: {missing}")

    if route_old in app:
        raise RuntimeError("Placeholder de Participações sobreviveu no bundle")

    # Canonical owners consumed by Participações must remain intact.
    owners = [
        "if(path==='/crm/financeiro')return crmTransactionsPage();",
        "if(path==='/crm/financeiro/accounting')return crmAccountingPage();",
        "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();",
        "if(path==='/crm/financeiro/rateios'){const page=crmCostAllocationsPage();",
        "if(path==='/crm/juridico/contratos')return crmLegalContractsPage();",
        "if(path==='/crm/juridico/contratos/templates')return crmLegalTemplatesPage();",
        "if(path==='/crm/juridico/contratos/variaveis')return crmLegalVariablesPage();",
    ]
    missing_owners = [route for route in owners if route not in app]
    if missing_owners:
        raise RuntimeError(f"Owner canônico sofreu regressão durante Participações: {missing_owners}")

    payout_placeholder = "if(path==='/crm/financeiro/repasses')return crmArchitecturePlaceholderPage('accounting','repasses','Repasses');"
    if payout_placeholder not in app:
        raise RuntimeError("Financeiro → Repasses deixou de permanecer placeholder")

    # Participações is calculation/approval only. Settlement remains a future owner.
    forbidden = [
        "createTransaction(",
        "createPayout(",
        "paidAmount",
        "participationRules",
        "partnerPercentages",
        "revenueShareRules",
        "productPartnerRules",
        "shareholder",
        "partnerOwnership",
        "equityPercentage",
        "sharePercentage",
    ]
    leaked = [item for item in forbidden if item in core or item in browser]
    if leaked:
        raise RuntimeError(f"Participações contém responsabilidade proibida/concorrente: {leaked}")

    sidebar_start = app.rfind("function crmRelSidebar")
    sidebar_end = app.find("function crmReferenceRoute", sidebar_start)
    sidebar = app[sidebar_start:sidebar_end]
    expected_finance = ["Transações", "Contabilidade", "Notas Fiscais", "Rateios", "Participações", "Repasses"]
    missing_sidebar = [label for label in expected_finance if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar Financeiro sofreu regressão: {missing_sidebar}")
    forbidden_sidebar = ["Cálculos", "Obrigações", "Memória de Participações", "Beneficiários"]
    leaked_sidebar = [label for label in forbidden_sidebar if label in sidebar]
    if leaked_sidebar:
        raise RuntimeError(f"Submódulo indevido de Participações foi adicionado ao sidebar: {leaked_sidebar}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN ECONOMIC PARTICIPATIONS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", value)
        value = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", value)
        path.write_text(value, encoding="utf-8")

    print("Financeiro → Participações materializado como camada canônica de cálculo/aprovação de direitos econômicos contratuais; Contratos permanece owner das regras; Repasses permanece placeholder.")
    return 1


if __name__ == "__main__":
    apply_crm_economic_participations()
