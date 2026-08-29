from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
START = "  // VALTREN BUSINESS UNIT CONSOLIDATION START\n"
END = "  // VALTREN BUSINESS UNIT CONSOLIDATION END\n"

BLOCK = r'''  // VALTREN BUSINESS UNIT CONSOLIDATION START
  // Product is no longer a standalone business module. During the legacy-schema
  // transition, old product/productId consumers resolve to Business Units.
  const crmBusinessLegacyProductsPage=crmBusinessProductsPage;
  crmBusinessProductsPage=crmBusinessUnitsPage;
  const crmBusinessLegacyProductsFeed=crmBusinessProductsFeed;
  crmBusinessProductsFeed=(filters={})=>crmBusinessUnitsFeed(filters);
  const crmBusinessLegacyGetProduct=crmBusinessGetProduct;
  crmBusinessGetProduct=(id)=>crmBusinessGetUnit(id);
  const crmBusinessLegacyResolveDimension=crmBusinessResolveDimension;
  crmBusinessResolveDimension=(type,id)=>crmBusinessLegacyResolveDimension(type==='product'?'business_unit':type,id);
  const crmBusinessLegacyDimensionLabel=crmBusinessDimensionLabel;
  crmBusinessDimensionLabel=(type,id)=>crmBusinessLegacyDimensionLabel(type==='product'?'business_unit':type,id);
  const crmRelSidebarWithLegacyProducts=crmRelSidebar;
  crmRelSidebar=(active='relationships',sub='')=>{
    const html=crmRelSidebarWithLegacyProducts(active,sub);
    const template=document.createElement('template');
    template.innerHTML=html;
    const products=[...template.content.querySelectorAll('a[href="#/crm/negocios"]')].filter((link)=>link.textContent.trim()==='Produtos');
    products.forEach((link)=>link.remove());
    const units=template.content.querySelector('a[href="#/crm/negocios/unidades"]');
    if(units) units.setAttribute('href','#/crm/negocios');
    return template.innerHTML;
  };
  // VALTREN BUSINESS UNIT CONSOLIDATION END
'''


def apply_business_units_consolidation() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    app = APP.read_text(encoding="utf-8")

    start_count = app.count(START)
    end_count = app.count(END)
    desired = BLOCK.rstrip() + "\n"
    if start_count == 1 and end_count == 1:
        start = app.index(START)
        end = app.index(END, start) + len(END)
        current = app[start:end]
        updated = app if current == desired else app[:start] + desired + app[end:]
    elif start_count == 0 and end_count == 0:
        anchor = "  function contactPage(query)"
        if app.count(anchor) != 1:
            raise RuntimeError(f"Âncora contactPage inválida para consolidação de Unidade de Negócio: {app.count(anchor)}")
        at = app.index(anchor)
        updated = app[:at] + desired + "\n" + app[at:]
    else:
        raise RuntimeError(f"Markers de consolidação divergentes: {start_count}/{end_count}")

    required = [
        "crmBusinessProductsPage=crmBusinessUnitsPage",
        "crmBusinessProductsFeed=(filters={})=>crmBusinessUnitsFeed(filters)",
        "crmBusinessGetProduct=(id)=>crmBusinessGetUnit(id)",
        "type==='product'?'business_unit':type",
        "link.textContent.trim()==='Produtos'",
        "units.setAttribute('href','#/crm/negocios')",
    ]
    missing = [token for token in required if token not in updated]
    if missing:
        raise RuntimeError(f"Consolidação Produto → Unidade de Negócio incompleta: {missing}")

    if len(re.findall(r"VALTREN BUSINESS UNIT CONSOLIDATION START", updated)) != 1:
        raise RuntimeError("Bloco de consolidação deve existir exatamente uma vez")

    APP.write_text(updated, encoding="utf-8")
    print("Business Unit consolidation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(apply_business_units_consolidation())
