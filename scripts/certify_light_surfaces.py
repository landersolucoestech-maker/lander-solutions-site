#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from selenium.webdriver.common.by import By

import certify_light_surfaces_base as base

# Full canonical surface/layout matrix for the autonomous certification round.
# 1920/1600 validate the intentionally unbounded workspace; 320 is a smoke width.
FULL_VIEWPORTS = [1920, 1600, 1440, 1280, 1024, 768, 390, 320]
FULL_ROUTES = {
    "dashboard": "#/crm/dashboard",
    "crm-contatos": "#/crm/relationships?tab=contacts",
    "crm-leads": "#/crm/relationships?tab=leads",
    "agenda": "#/crm/agenda",
    "transacoes": "#/crm/financeiro",
    "contabilidade": "#/crm/financeiro/accounting",
    "notas-fiscais": "#/crm/financeiro/invoices",
    "rateios": "#/crm/financeiro/rateios",
    "participacoes": "#/crm/financeiro/participacoes",
    "repasses": "#/crm/financeiro/repasses",
    "assuntos-juridicos": "#/crm/juridico",
    "contratos": "#/crm/juridico/contratos",
    "templates": "#/crm/juridico/contratos/templates",
    "variaveis": "#/crm/juridico/contratos/variaveis",
    "compliance": "#/crm/juridico/compliance",
    "propriedade-intelectual": "#/crm/juridico/propriedade-intelectual",
    "societario": "#/crm/juridico/societario",
    "marketing": "#/crm/marketing",
    "negocios": "#/crm/negocios",
    "relatorios": "#/crm/relatorios",
    "configuracoes": "#/crm/configuracoes",
}

base.ROUTES = FULL_ROUTES
base.VIEWPORTS = FULL_VIEWPORTS
base.SCREENSHOT_ROUTES = set(FULL_ROUTES)
base.ACTIVE_STATE_VIEWPORTS = (1920, 1440, 390, 320)

_EXTENDED_LAYOUT: list[dict] = []
_ORIGINAL_SCAN = base.scan_route


def _rgba(value: str | None) -> tuple[int, int, int, float] | None:
    match = re.search(r"rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)(?:[, /]+([0-9.]+))?\)", value or "", re.I)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), float(match.group(4) or 1)


def _luminance(value: str | None) -> float:
    color = _rgba(value)
    if not color:
        return 255.0
    r, g, b, _ = color
    return .2126 * r + .7152 * g + .0722 * b


def _is_gold(value: str | None) -> bool:
    color = _rgba(value)
    if not color:
        return False
    r, g, b, _ = color
    return abs(r - 212) <= 12 and abs(g - 175) <= 12 and abs(b - 55) <= 16


def _is_white(value: str | None) -> bool:
    color = _rgba(value)
    return bool(color and min(color[:3]) >= 238)


def _extended_scan(driver) -> dict:
    data = _ORIGINAL_SCAN(driver)
    extra = driver.execute_script(r"""
      const main=document.querySelector('.crm-main');
      const ws=document.querySelector('.crm-workspace,.crm-ref-workspace,.crm-agenda-workspace');
      const rect=e=>e?e.getBoundingClientRect():null;
      const style=e=>e?getComputedStyle(e):null;
      const mr=rect(main),wr=rect(ws),ms=style(main),wsStyle=style(ws);
      const root=document.documentElement;
      const body=document.body;
      const mainScrollable=!!main && ['auto','scroll'].includes(ms.overflowY) && main.scrollHeight>main.clientHeight+1;
      const documentScrollable=Math.max(root.scrollHeight,body?.scrollHeight||0)>root.clientHeight+1;
      return {
        viewportWidth:innerWidth,
        viewportHeight:innerHeight,
        main:{left:mr?.left??null,right:mr?.right??null,width:mr?.width??null,maxWidth:ms?.maxWidth??null,minWidth:ms?.minWidth??null,overflowY:ms?.overflowY??null,clientHeight:main?.clientHeight??null,scrollHeight:main?.scrollHeight??null},
        workspace:ws?{left:wr.left,right:wr.right,width:wr.width,maxWidth:wsStyle.maxWidth,minWidth:wsStyle.minWidth}:null,
        document:{clientWidth:root.clientWidth,scrollWidth:root.scrollWidth,clientHeight:root.clientHeight,scrollHeight:root.scrollHeight},
        doubleVerticalScroll:!!(mainScrollable&&documentScrollable)
      };
    """)
    extra["route"] = data.get("route")
    extra["width"] = data.get("width")
    _EXTENDED_LAYOUT.append(extra)
    return data


base.scan_route = _extended_scan


def _account_contract(base_url: str, output_dir: Path) -> tuple[list[dict], list[str], list[str]]:
    failures: list[str] = []
    rows: list[dict] = []
    screenshots: list[str] = []
    driver = base.driver_factory()
    try:
        for width in FULL_VIEWPORTS:
            base.set_viewport(driver, width)
            driver.get(base.normalize_url(base_url, "#/crm/dashboard"))
            base.wait_ready(driver)
            closed = driver.execute_script(r"""
              const menu=document.querySelector('.crm-account-menu');
              const summary=menu?.querySelector(':scope>summary');
              const copy=menu?.querySelector('.crm-account-copy');
              const strong=menu?.querySelector('.crm-account-copy strong');
              const small=menu?.querySelector('.crm-account-copy small');
              const icon=menu?.querySelector('.crm-account-icon');
              const chev=menu?.querySelector('.crm-account-chevron');
              const s=summary?getComputedStyle(summary):null;
              const r=summary?.getBoundingClientRect();
              return {
                found:!!menu&&!!summary,
                backgroundColor:s?.backgroundColor||null,
                borderColor:s?.borderColor||null,
                titleColor:strong?getComputedStyle(strong).color:null,
                secondaryColor:small?getComputedStyle(small).color:null,
                iconColor:icon?getComputedStyle(icon).color:null,
                chevronColor:chev?getComputedStyle(chev).color:null,
                copyVisible:copy?getComputedStyle(copy).display!=='none':false,
                rect:r?{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}:null,
                docWidth:document.documentElement.scrollWidth,
                clientWidth:document.documentElement.clientWidth
              };
            """)
            if not closed.get("found"):
                failures.append(f"Account Menu @{width}: trigger ausente")
                continue
            bg = _rgba(closed.get("backgroundColor"))
            if not bg or bg[3] > .15:
                failures.append(f"Account Menu @{width}: trigger fechado não é transparente ({closed.get('backgroundColor')})")
            if not _is_gold(closed.get("borderColor")):
                failures.append(f"Account Menu @{width}: borda do trigger não é dourada ({closed.get('borderColor')})")
            if not _is_gold(closed.get("iconColor")) or not _is_gold(closed.get("chevronColor")):
                failures.append(f"Account Menu @{width}: ícone/chevron fora do dourado canônico")
            if closed.get("copyVisible"):
                if not _is_white(closed.get("titleColor")):
                    failures.append(f"Account Menu @{width}: Conta não está branca ({closed.get('titleColor')})")
                if not _is_gold(closed.get("secondaryColor")):
                    failures.append(f"Account Menu @{width}: secondary não está dourado ({closed.get('secondaryColor')})")
            if closed.get("docWidth", 0) > closed.get("clientWidth", 0) + 1:
                failures.append(f"Account Menu @{width}: overflow horizontal fechado")

            summary = driver.find_element(By.CSS_SELECTOR, ".crm-account-menu>summary")
            driver.execute_script("arguments[0].click()", summary)
            opened = driver.execute_script(r"""
              const menu=document.querySelector('.crm-account-menu');
              const summary=menu?.querySelector(':scope>summary');
              const pop=menu?.querySelector('.crm-account-popover');
              const strong=pop?.querySelector(':scope>strong');
              const para=pop?.querySelector('p');
              const action=pop?.querySelector('a');
              const ps=pop?getComputedStyle(pop):null;
              const ss=summary?getComputedStyle(summary):null;
              const r=pop?.getBoundingClientRect();
              return {
                open:!!menu?.open,
                triggerBackground:ss?.backgroundColor||null,
                popoverBackground:ps?.backgroundColor||null,
                popoverColor:ps?.color||null,
                strongColor:strong?getComputedStyle(strong).color:null,
                paragraphColor:para?getComputedStyle(para).color:null,
                actionColor:action?getComputedStyle(action).color:null,
                rect:r?{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}:null,
                docWidth:document.documentElement.scrollWidth,
                clientWidth:document.documentElement.clientWidth,
                innerWidth:innerWidth,
                innerHeight:innerHeight
              };
            """)
            if not opened.get("open"):
                failures.append(f"Account Menu @{width}: popover não abriu")
            if _luminance(opened.get("popoverBackground")) < 180:
                failures.append(f"Account Menu @{width}: popover aberto não é light ({opened.get('popoverBackground')})")
            for key in ("strongColor", "paragraphColor", "actionColor"):
                if _luminance(opened.get(key)) > 185:
                    failures.append(f"Account Menu @{width}: {key} tem contraste insuficiente sobre surface clara ({opened.get(key)})")
            rect = opened.get("rect") or {}
            if rect and (rect.get("left", 0) < -1 or rect.get("right", 0) > width + 1):
                failures.append(f"Account Menu @{width}: popover fora do viewport {rect}")
            if opened.get("docWidth", 0) > opened.get("clientWidth", 0) + 1:
                failures.append(f"Account Menu @{width}: overflow horizontal aberto")
            name = f"account-menu-open-{width}.png"
            driver.save_screenshot(str(output_dir / name))
            screenshots.append(name)
            rows.append({"width": width, "closed": closed, "opened": opened, "screenshot": name})
    finally:
        driver.quit()
    return rows, failures, screenshots


def main() -> int:
    # Existing certifier remains authoritative for dark surfaces, dashboard states,
    # contract modal and runtime errors; this wrapper makes its coverage complete.
    base_result = base.main()
    parser_report = Path(".")
    # Resolve output-dir from the same CLI without changing the base parser contract.
    import sys
    try:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1])
        base_url = sys.argv[sys.argv.index("--base-url") + 1]
    except (ValueError, IndexError):
        return 2
    report_path = output_dir / "light-surface-certification-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    failures = list(report.get("failures") or [])

    layout_failures: list[str] = []
    for row in _EXTENDED_LAYOUT:
        main = row.get("main") or {}
        workspace = row.get("workspace") or {}
        width = row.get("width")
        route = row.get("route")
        if main.get("maxWidth") not in ("none", None):
            layout_failures.append(f"{route}@{width}: crm-main max-width={main.get('maxWidth')}")
        if workspace and workspace.get("maxWidth") not in ("none", None):
            layout_failures.append(f"{route}@{width}: workspace max-width={workspace.get('maxWidth')}")
        viewport = float(row.get("viewportWidth") or 0)
        if main.get("right") is not None and abs(float(main["right"]) - viewport) > 1.5:
            layout_failures.append(f"{route}@{width}: crm-main não alcança a borda direita ({main.get('right')} vs {viewport})")
        if workspace and main.get("right") is not None and abs(float(workspace.get("right", 0)) - float(main["right"])) > 1.5:
            layout_failures.append(f"{route}@{width}: workspace não ocupa 100% do crm-main")
        if row.get("doubleVerticalScroll"):
            layout_failures.append(f"{route}@{width}: double vertical scroll detectado")

    account_rows, account_failures, account_screenshots = _account_contract(base_url, output_dir)
    failures.extend(layout_failures)
    failures.extend(account_failures)
    report["extended_viewports"] = FULL_VIEWPORTS
    report["extended_route_count"] = len(FULL_ROUTES)
    report["extended_layout"] = _EXTENDED_LAYOUT
    report["layout_contract_failures"] = layout_failures
    report["account_menu_contract"] = account_rows
    report["account_menu_contract_failures"] = account_failures
    report["screenshots"] = list(report.get("screenshots") or []) + account_screenshots
    report["failures"] = failures
    report["status"] = "PASS" if not failures and base_result == 0 else "FAIL"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "mode": report.get("mode"),
        "route_scenarios": report.get("route_scenarios"),
        "extended_viewports": FULL_VIEWPORTS,
        "layout_failures": layout_failures,
        "account_menu_failures": account_failures,
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
