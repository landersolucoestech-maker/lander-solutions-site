#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import certify_visual_base as base
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

_ORIGINAL_WAIT_READY = base.wait_ready
CATEGORIES = ("VISUAL REGRESSION", "LAYOUT", "ACCESSIBILITY", "INTERACTION", "RUNTIME", "HARNESS")


def normalize_interactive_state(driver) -> None:
    driver.execute_script(r"""
      const sidebar=document.querySelector('.crm-sidebar');
      const overlay=document.querySelector('.crm-sidebar-overlay');
      const toggle=document.querySelector('.crm-mobile-nav-toggle');
      sidebar?.classList.remove('is-open');
      overlay?.classList.remove('is-open');
      if(toggle) toggle.setAttribute('aria-expanded','false');
      document.documentElement.classList.remove('crm-sidebar-lock');
      document.body?.classList.remove('crm-sidebar-lock');
      document.querySelectorAll('.crm-account-menu[open]').forEach((node)=>node.removeAttribute('open'));
      document.querySelectorAll('dialog[open]').forEach((node)=>node.removeAttribute('open'));
      document.getElementById('crm-ref-modal-root')?.remove();
      document.getElementById('crm-rel-modal-root')?.remove();
    """)
    time.sleep(0.03)


def wait_ready(driver) -> None:
    _ORIGINAL_WAIT_READY(driver)
    normalize_interactive_state(driver)
    WebDriverWait(driver, 5).until(
        lambda d: d.execute_script(
            "return !document.querySelector('.crm-sidebar')?.classList.contains('is-open')"
            " && !document.documentElement.classList.contains('crm-sidebar-lock')"
            " && !document.body?.classList.contains('crm-sidebar-lock');"
        )
    )


def check_account_menu(driver, url_base: str, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    routes = [
        "#/crm/dashboard", "#/crm/relationships?tab=contacts", "#/crm/financeiro",
        "#/crm/juridico", "#/crm/negocios", "#/crm/marketing", "#/crm/relatorios",
        "#/crm/configuracoes?tab=empresa",
    ]
    for route in routes:
        base.set_viewport(driver, 768)
        driver.get(base.normalize_url(url_base, route))
        wait_ready(driver)
        summary = driver.find_element(By.CSS_SELECTOR, ".crm-account-menu>summary")
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.05)
        data = driver.execute_script(r"""
          const r=e=>{const x=e.getBoundingClientRect();return {left:x.left,right:x.right,top:x.top,bottom:x.bottom,width:x.width,height:x.height}};
          const menu=document.querySelector('.crm-account-menu');
          const summary=document.querySelector('.crm-account-menu>summary');
          const p=document.querySelector('.crm-account-popover');
          return {popover:p?r(p):null,summary:r(summary),docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth,summaryText:(summary?.textContent||'').trim(),popoverText:(p?.textContent||'').trim(),menuText:(menu?.textContent||'').trim()};
        """)
        base.fail_if(not data["popover"], f"Account Menu@768 {route}: popover missing", failures)
        if data["popover"]:
            base.fail_if(data["popover"]["right"] > 769 or data["popover"]["left"] < -1, f"Account Menu@768 {route}: popover outside viewport {data['popover']}", failures)
        base.fail_if(data["docSW"] > data["docCW"] + 1, f"Account Menu@768 {route}: body overflow", failures)
        base.fail_if("Autenticação desativada" not in data["summaryText"], f"Account Menu@768 {route}: auth-disabled copy missing from canonical summary", failures)
        base.fail_if("Sem sessão ativa" not in data["popoverText"], f"Account Menu@768 {route}: no-session copy missing from canonical popover", failures)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.03)
        results.append({"route": route, **data})
    return results


def _exposed_overlay_point(driver) -> dict[str, Any]:
    return driver.execute_script(r"""
      const sidebar=document.querySelector('.crm-sidebar'),overlay=document.querySelector('.crm-sidebar-overlay');
      if(!sidebar||!overlay)return {ok:false,reason:'missing sidebar or overlay'};
      const s=sidebar.getBoundingClientRect(),o=overlay.getBoundingClientRect();
      const left=Math.max(s.right+8,o.left+8),right=Math.min(innerWidth-8,o.right-8);
      if(!(right>left))return {ok:false,reason:'no exposed horizontal overlay area',sidebar:{left:s.left,right:s.right},overlay:{left:o.left,right:o.right},viewport:innerWidth};
      const x=left+(right-left)/2,top=Math.max(o.top+8,8),bottom=Math.min(o.bottom-8,innerHeight-8),y=top+(bottom-top)/2;
      const hit=document.elementFromPoint(x,y);
      return {ok:hit===overlay||overlay.contains(hit),x,y,hit:hit?{tag:hit.tagName,className:hit.className||'',id:hit.id||''}:null,sidebar:{left:s.left,right:s.right},overlay:{left:o.left,right:o.right},viewport:innerWidth};
    """)


def _click_viewport_point(driver, x: float, y: float) -> None:
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type":"mouseMoved","x":x,"y":y,"button":"none"})
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","buttons":1,"clickCount":1})
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","buttons":0,"clickCount":1})


def check_drawer(driver, url_base: str, outdir: Path, failures: list[str]) -> dict[str, Any]:
    base.set_viewport(driver, 390, 844)
    driver.get(base.normalize_url(url_base, "#/crm/dashboard"))
    wait_ready(driver)
    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.08)
    opened = driver.execute_script("return {sidebar:document.querySelector('.crm-sidebar').classList.contains('is-open'),overlay:document.querySelector('.crm-sidebar-overlay').classList.contains('is-open'),html:document.documentElement.classList.contains('crm-sidebar-lock'),body:document.body.classList.contains('crm-sidebar-lock'),expanded:document.querySelector('.crm-mobile-nav-toggle').getAttribute('aria-expanded'),sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth};")
    for key in ("sidebar", "overlay", "html", "body"):
        base.fail_if(not opened[key], f"drawer: open state missing {key}", failures)
    base.fail_if(opened["expanded"] != "true", f"drawer: aria-expanded={opened['expanded']}", failures)
    base.fail_if(opened["sw"] > opened["cw"] + 1, "drawer: BODY overflow while open", failures)
    shot = "dashboard-390-drawer-open.png"
    driver.save_screenshot(str(outdir / shot))

    point = _exposed_overlay_point(driver)
    base.fail_if(not point.get("ok"), f"HARNESS: no exposed overlay click point {point}", failures)
    if point.get("ok"):
        _click_viewport_point(driver, float(point["x"]), float(point["y"])); time.sleep(0.05)
    overlay_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock');")
    base.fail_if(not overlay_close, "drawer: overlay did not close/unlock", failures)

    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.04)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.05)
    escape_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock');")
    base.fail_if(not escape_close, "drawer: Escape did not close/unlock", failures)

    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.04)
    driver.find_element(By.CSS_SELECTOR, ".crm-sidebar a[href='#/crm/relationships']").click()
    WebDriverWait(driver, 10).until(lambda d: "#/crm/relationships" in d.current_url); time.sleep(0.05)
    route_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock')&&document.documentElement.scrollWidth<=document.documentElement.clientWidth+1;")
    base.fail_if(not route_close, "drawer: route selection did not close/unlock", failures)
    base.fail_if(bool(base.relevant_console_errors(base.collect_console(driver))), "drawer: console error during interaction", failures)
    return {"open":opened,"overlay_point":point,"overlay_close":overlay_close,"escape_close":escape_close,"route_close":route_close,"screenshot":shot}


def classify_failure(message: str) -> str:
    text = message.lower()
    if "certification harness exception" in text or "harness:" in text:
        return "HARNESS"
    if "console error" in text or "syntaxerror" in text or "referenceerror" in text or "typeerror" in text or "uncaught" in text:
        return "RUNTIME"
    if "unlabeled visible form controls" in text or "interactive mobile targets below 30px" in text or "keyboard@" in text or "focus lacks" in text:
        return "ACCESSIBILITY"
    if "horizontal overflow" in text or "outside viewport" in text or "exceeds viewport" in text or "double-scroll" in text or "white footer gap" in text or "ends before viewport" in text or "controls outside mobile viewport" in text or "off-canvas" in text or "hierarchy" in text or "width=" in text:
        return "LAYOUT"
    if text.startswith("drawer:") or "account menu@" in text or text.startswith("details ") or "failed to open" in text or "failed to close" in text or "modal" in text or "chevron" in text or "route selection" in text:
        return "INTERACTION"
    return "VISUAL REGRESSION"


def categorize_report(report_path: Path) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    grouped = {name: [] for name in CATEGORIES}
    for failure in report.get("failures", []):
        grouped[classify_failure(str(failure))].append(str(failure))
    report["failure_categories"] = {name:{"count":len(items),"failures":items} for name,items in grouped.items()}
    report["failure_category_counts"] = {name:len(items) for name,items in grouped.items()}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def run(args: argparse.Namespace) -> int:
    base.wait_ready = wait_ready
    base.check_account_menu = check_account_menu
    base.check_drawer = check_drawer
    code = base.run(args)
    report_path = Path(args.output_dir) / "visual-certification-report.json"
    if not report_path.exists():
        raise RuntimeError("HARNESS: visual certification report was not produced")
    report = categorize_report(report_path)
    print(json.dumps({"status":report.get("status"),"mode":args.mode,"scenario_count":report.get("scenario_count"),"failure_category_counts":report.get("failure_category_counts")}, ensure_ascii=False, indent=2))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Certificação visual categorizada e endurecida do frontend Valtren.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["artifact", "public"], required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
