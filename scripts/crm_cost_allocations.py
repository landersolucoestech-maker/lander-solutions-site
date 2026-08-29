from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MODULE_DIR = ROOT / "src" / "modules" / "finance" / "allocations"
CORE = MODULE_DIR / "core.js"
BROWSER = MODULE_DIR / "browser.js"
MODULE_CSS = MODULE_DIR / "styles.css"
CACHE_VERSION = "20260829-finance-allocations-module-v1"
JS_START = "  // VALTREN COST ALLOCATIONS START\n"
JS_END = "  // VALTREN COST ALLOCATIONS END\n"


def apply_crm_cost_allocations() -> int:
    for path in (APP, CSS, CORE, BROWSER, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)

    app = APP.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8").strip()
    browser = BROWSER.read_text(encoding="utf-8").strip()

    app = re.sub(
        r"\n?  // VALTREN COST ALLOCATIONS START\n.*?  // VALTREN COST ALLOCATIONS END\n",
        "\n",
        app,
        flags=re.S,
    )

    app, replaced_finance_editor = re.subn(
        r"function crmFinanceOpenAllocation\(id\)\{[^\n]*\}\n",
        "function crmFinanceOpenAllocation(id){const tx=crmFinanceService().getTransaction(id);if(!tx)return;location.hash=`#/crm/financeiro/rateios?source=${encodeURIComponent(id)}&new=1`; }\n",
        app,
        count=1,
    )
    if replaced_finance_editor != 1:
        raise RuntimeError(f"Editor simples de rateio em Transações não pôde ser convertido em compatibilidade: {replaced_finance_editor}")

    refresh_old = "function crmFinanceRefresh(){crmFinanceSyncLegacy();if(typeof renderCurrentWithoutReset==='function')renderCurrentWithoutReset();}"
    refresh_new = "function crmFinanceRefresh(){crmFinanceSyncLegacy();if(typeof crmCostAllocationService==='function')crmCostAllocationService().refreshAllConsistency();if(typeof renderCurrentWithoutReset==='function')renderCurrentWithoutReset();}"
    if refresh_old not in app:
        raise RuntimeError("Ponto de integração de consistência em Transações não encontrado")
    app = app.replace(refresh_old, refresh_new, 1)

    accounting_return = "  return state.__crmAccountingService;\n}"
    accounting_return_new = "  if(typeof crmCostAllocationService==='function')crmCostAllocationService().refreshAllConsistency();\n  return state.__crmAccountingService;\n}"
    if accounting_return not in app:
        raise RuntimeError("Adapter de leitura da Contabilidade não encontrado")
    app = app.replace(accounting_return, accounting_return_new, 1)

    dimension_pattern = re.compile(
        r"    function dimensionAmount\(tx,filters=\{\}\)\{.*?\n    \}\n\n    function accountingIssues",
        re.S,
    )
    dimension_replacement = r'''    function dimensionAmount(tx,filters={}){
      const dimension=filters.dimension||'',productId=filters.productId||'',serviceId=filters.serviceId||'',businessUnitId=filters.businessUnitId||'';
      if(!dimension&&!productId&&!serviceId&&!businessUnitId)return roundMoney(tx.amount);
      const allocations=(Array.isArray(tx.allocations)?tx.allocations:[]).filter((item)=>item.source!=='cost_allocation'||item.status==='posted');
      if(allocations.length){
        const amount=allocations.reduce((sum,item)=>{
          const type=item.destinationType||item.dimension||'';
          const destinationId=item.destinationId||item.productId||item.serviceId||item.businessUnitId||'';
          const matches=dimension==='corporate'?type==='corporate':productId?type==='product'&&destinationId===productId:serviceId?type==='service'&&destinationId===serviceId:businessUnitId?type==='business_unit'&&destinationId===businessUnitId:false;
          if(!matches)return sum;
          if(item.amount!=null)return sum+num(item.amount);
          if(item.percentage!=null)return sum+(num(tx.amount)*num(item.percentage)/100);
          return sum;
        },0);
        return roundMoney(amount);
      }
      const meta=getTransactionMeta(tx.id)||{};
      if(dimension==='corporate')return tx.businessDimension==='corporate'?roundMoney(tx.amount):0;
      if(productId)return tx.businessDimension==='product'&&tx.productId===productId?roundMoney(tx.amount):0;
      if(serviceId)return meta.serviceId===serviceId?roundMoney(tx.amount):0;
      if(businessUnitId)return meta.businessUnitId===businessUnitId?roundMoney(tx.amount):0;
      return roundMoney(tx.amount);
    }

    function accountingIssues'''
    app, dimension_count = dimension_pattern.subn(dimension_replacement, app, count=1)
    if dimension_count != 1:
        raise RuntimeError(f"dimensionAmount da Contabilidade não pôde ser adaptado: {dimension_count}")

    row_filters_old = "      if(filters.serviceId&&meta.serviceId!==filters.serviceId)return null;\n      if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId)return null;"
    row_filters_new = "      const effectiveAllocations=(Array.isArray(tx.allocations)?tx.allocations:[]).filter((item)=>item.source!=='cost_allocation'||item.status==='posted');\n      const allocatedTo=(type,id)=>effectiveAllocations.some((item)=>(item.destinationType||item.dimension)===type&&(item.destinationId||item.productId||item.serviceId||item.businessUnitId||'')===id);\n      if(filters.serviceId&&meta.serviceId!==filters.serviceId&&!allocatedTo('service',filters.serviceId))return null;\n      if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId&&!allocatedTo('business_unit',filters.businessUnitId))return null;"
    if app.count(row_filters_old) != 1:
        raise RuntimeError(f"Filtro dimensional rowFor não encontrado de forma inequívoca: {app.count(row_filters_old)}")
    app = app.replace(row_filters_old, row_filters_new, 1)

    list_filters_old = "        if(filters.serviceId&&meta.serviceId!==filters.serviceId)continue;\n        if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId)continue;"
    list_filters_new = "        const effectiveAllocations=(Array.isArray(tx.allocations)?tx.allocations:[]).filter((item)=>item.source!=='cost_allocation'||item.status==='posted');\n        const allocatedTo=(type,id)=>effectiveAllocations.some((item)=>(item.destinationType||item.dimension)===type&&(item.destinationId||item.productId||item.serviceId||item.businessUnitId||'')===id);\n        if(filters.serviceId&&meta.serviceId!==filters.serviceId&&!allocatedTo('service',filters.serviceId))continue;\n        if(filters.businessUnitId&&meta.businessUnitId!==filters.businessUnitId&&!allocatedTo('business_unit',filters.businessUnitId))continue;"
    if app.count(list_filters_old) != 1:
        raise RuntimeError(f"Filtro dimensional listEntries não encontrado de forma inequívoca: {app.count(list_filters_old)}")
    app = app.replace(list_filters_old, list_filters_new, 1)

    issues_old = "      const issues=[],resolved=resolveClassification(tx),meta=getTransactionMeta(tx.id);"
    issues_new = "      const issues=[],resolved=resolveClassification(tx),meta=getTransactionMeta(tx.id);\n      if(tx.metadata?.costAllocationProjection?.status==='needs_review')issues.push('allocation_needs_review');"
    if issues_old not in app:
        raise RuntimeError("Ponto de pendência contábil para Rateios não encontrado")
    app = app.replace(issues_old, issues_new, 1)

    block = JS_START + core + "\n\n" + browser + "\n" + JS_END
    anchor = "  function contactPage(query)"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora contactPage inválida para Rateios: {app.count(anchor)} ocorrência(s)")
    app = app.replace(anchor, block + "\n" + anchor, 1)

    route_old = "if(path==='/crm/financeiro/rateios')return crmArchitecturePlaceholderPage('accounting','rateios','Rateios');"
    if route_old not in app:
        raise RuntimeError("Placeholder canônico de Rateios não encontrado")
    route_new = "if(path==='/crm/financeiro/rateios'){const page=crmCostAllocationsPage();const info=routeInfo();if(info.query.get('new')==='1'){const source=info.query.get('source')||'';setTimeout(()=>crmCostAllocationOpenEditor('',source),0);}return page;}"
    app = app.replace(route_old, route_new, 1)

    required = [
        "ValtrenCostAllocationCore",
        "state.crmCostAllocations",
        "function crmCostAllocationsPage()",
        "function crmCostAllocationOpenEditor",
        "function crmCostAllocationOpenDetail",
        "Novo Rateio",
        "Rascunhos",
        "Em revisão",
        "Aprovados",
        "Postados",
        "Estornados",
        "Percentual",
        "Valor fixo",
        "Divisão igual",
        "Direcionador",
        "sourceTransactionId",
        "cost_allocation",
        "allocation_needs_review",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Rateios incompleto no bundle: {missing}")

    if "if(path==='/crm/financeiro/rateios')return crmArchitecturePlaceholderPage" in app:
        raise RuntimeError("Placeholder de Rateios sobreviveu no bundle")
    if "if(path==='/crm/financeiro')return crmTransactionsPage();" not in app:
        raise RuntimeError("Transações deixou de ser canônica")
    if "if(path==='/crm/financeiro/accounting')return crmAccountingPage();" not in app:
        raise RuntimeError("Contabilidade deixou de ser canônica")
    if "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();" not in app:
        raise RuntimeError("Notas Fiscais deixou de ser canônica")
    if "createTransaction(" in browser:
        raise RuntimeError("UI de Rateios não pode criar movimentação financeira")

    sidebar_start = app.find("// VALTREN SIDEBAR ARCHITECTURE START")
    sidebar_end = app.find("// VALTREN SIDEBAR ARCHITECTURE END", sidebar_start)
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Bloco canônico da Sidebar não localizado para validação")
    sidebar = app[sidebar_start:sidebar_end]
    expected_finance = ["Transações", "Contabilidade", "Notas Fiscais", "Rateios", "Participações", "Repasses"]
    missing_sidebar = [label for label in expected_finance if label not in sidebar]
    if missing_sidebar:
        raise RuntimeError(f"Sidebar financeiro sofreu regressão: {missing_sidebar}")
    forbidden_sidebar = ["Direcionadores", "Critérios de Rateio", "Alocações", "Memória de Cálculo"]
    leaked = [label for label in forbidden_sidebar if label in sidebar]
    if leaked:
        raise RuntimeError(f"Submódulo indevido foi adicionado ao sidebar: {leaked}")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN COST ALLOCATIONS \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text_value = path.read_text(encoding="utf-8")
        text_value = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text_value)
        text_value = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text_value)
        path.write_text(text_value, encoding="utf-8")

    print("Financeiro → Rateios materializado a partir de src/modules/finance/allocations, preservando projeção contábil, Transações, Notas Fiscais e sidebar.")
    return 1


if __name__ == "__main__":
    apply_crm_cost_allocations()
