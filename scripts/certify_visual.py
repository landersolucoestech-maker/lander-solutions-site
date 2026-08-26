#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

PRESENT = [
    "Dashboard", "CRM", "Agenda", "Financeiro", "Jurídico",
    "Marketing", "Negócios", "Relatórios", "Configurações",
]
ABSENT = ["ValtrenChat", "MusicChat", "RH", "Administração"]

MAIN_ROUTES = {
    "dashboard": "#/crm/dashboard",
    "crm": "#/crm/relationships",
    "business": "#/crm/negocios",
    "finance": "#/crm/financeiro",
    "legal": "#/crm/juridico",
    "settings": "#/crm/configuracoes",
}

EXTRA_ROUTES = {
    "marketing": "#/crm/marketing",
    "reports": "#/crm/relatorios",
}

MOBILE_EXTENDED = {
    "business-services": "#/crm/negocios/servicos",
    "business-units": "#/crm/negocios/unidades",
    "legal-contracts": "#/crm/juridico/contratos",
    "legal-templates": "#/crm/juridico/contratos/templates",
    "legal-variables": "#/crm/juridico/contratos/variaveis",
    "legal-compliance": "#/crm/juridico/compliance",
    "legal-ip": "#/crm/juridico/propriedade-intelectual",
    "legal-corporate": "#/crm/juridico/societario",
    "settings-company": "#/crm/configuracoes?tab=empresa",
    "settings-notifications": "#/crm/configuracoes?tab=notificacoes",
    "settings-security": "#/crm/configuracoes?tab=seguranca",
    "settings-integrations": "#/crm/configuracoes?tab=integracoes",
    "settings-audit": "#/crm/configuracoes?tab=auditoria",
    "settings-users": "#/crm/configuracoes?tab=usuarios",
}

EXPECTED_ACTIVE = {
    "#/crm/dashboard": "Dashboard",
    "#/crm/relationships": "CRM",
    "#/crm/financeiro": "Transações",
    "#/crm/negocios": "Produtos",
    "#/crm/negocios/servicos": "Serviços",
    "#/crm/negocios/unidades": "Unidades de Negócio",
    "#/crm/juridico": "Assuntos Jurídicos",
    "#/crm/juridico/contratos": "Contratos",
    "#/crm/juridico/contratos/templates": "Templates",
    "#/crm/juridico/contratos/variaveis": "Variáveis",
    "#/crm/juridico/compliance": "Compliance e Políticas",
    "#/crm/juridico/propriedade-intelectual": "Propriedade Intelectual",
    "#/crm/juridico/societario": "Societário",
    "#/crm/marketing": "Marketing",
    "#/crm/relatorios": "Relatórios",
    "#/crm/configuracoes": "Configurações",
    "#/crm/configuracoes?tab=empresa": "Configurações",
    "#/crm/configuracoes?tab=notificacoes": "Configurações",
    "#/crm/configuracoes?tab=seguranca": "Configurações",
    "#/crm/configuracoes?tab=integracoes": "Configurações",
    "#/crm/configuracoes?tab=auditoria": "Configurações",
    "#/crm/configuracoes?tab=usuarios": "Configurações",
}

JS_METRICS = r"""
const rect=(el)=>{
  if(!el)return null;
  const r=el.getBoundingClientRect();
  return {x:r.x,y:r.y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
};
const visible=(el)=>{
  if(!el)return false;
  const s=getComputedStyle(el),r=el.getBoundingClientRect();
  return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
};
const scrollAncestor=(el)=>{
  for(let p=el.parentElement;p&&p!==document.body;p=p.parentElement){
    const s=getComputedStyle(p);
    if(/auto|scroll/.test(s.overflowX))return true;
  }
  return false;
};
const sb=document.querySelector('.crm-sidebar');
const mainItems=[...document.querySelectorAll('.crm-nav > a,.crm-nav > .crm-nav-group > summary')];
const controls=[...document.querySelectorAll('input,select,textarea,button')]
  .filter(visible)
  .filter(el=>!el.closest('.crm-sidebar'))
  .filter(el=>!scrollAncestor(el))
  .map(el=>({tag:el.tagName,text:(el.innerText||el.getAttribute('aria-label')||el.name||'').trim().slice(0,80),rect:rect(el)}))
  .filter(x=>x.rect.left < -1 || x.rect.right > innerWidth+1);
return {
  innerWidth,
  innerHeight,
  docScrollWidth:document.documentElement.scrollWidth,
  docClientWidth:document.documentElement.clientWidth,
  bodyScrollWidth:document.body?document.body.scrollWidth:0,
  sidebar:rect(sb),
  sidebarScrollWidth:sb?sb.scrollWidth:null,
  sidebarClientWidth:sb?sb.clientWidth:null,
  sidebarClass:sb?sb.className:'',
  sidebarText:sb?(sb.innerText||''):'',
  sidebarTransform:sb?getComputedStyle(sb).transform:null,
  brand:rect(document.querySelector('.crm-brand img')),
  brandStrong:(document.querySelector('.crm-brand strong')?.textContent||'').trim(),
  brandSmall:(document.querySelector('.crm-brand small')?.textContent||'').trim(),
  mainItems:mainItems.map(el=>({text:(el.innerText||'').replace(/\s+/g,' ').trim(),rect:rect(el)})),
  active:[...document.querySelectorAll('.crm-nav a.active')].map(el=>({text:(el.innerText||'').trim(),href:el.getAttribute('href'),rect:rect(el),bg:getComputedStyle(el).backgroundColor,shadow:getComputedStyle(el).boxShadow})),
  topbar:rect(document.querySelector('.crm-topbar')),
  accountSummary:rect(document.querySelector('.crm-account-menu>summary')),
  accountText:(document.querySelector('.crm-account-menu')?.textContent||'').replace(/\s+/g,' ').trim(),
  mobileToggle:rect(document.querySelector('.crm-mobile-nav-toggle')),
  outOfBoundsControls:controls,
  htmlLocked:document.documentElement.classList.contains('crm-sidebar-lock'),
  bodyLocked:document.body?.classList.contains('crm-sidebar-lock')||false,
};
"""

ERROR_PATTERNS = re.compile(r"SyntaxError|ReferenceError|TypeError|Unhandled|Uncaught|handler exception|route exception", re.I)


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def set_viewport(driver: webdriver.Chrome, width: int, height: int = 1000) -> None:
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": False,
    })


def wait_ready(driver: webdriver.Chrome) -> None:
    WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 15).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".crm-sidebar"))
    time.sleep(0.12)


def normalize_url(base: str, route: str, cache_bust: str | None = None) -> str:
    base = base.rstrip("/") + "/"
    if cache_bust:
        return base + "?cert=" + cache_bust + route
    return base + route


def collect_console(driver: webdriver.Chrome) -> list[dict]:
    try:
        logs = driver.get_log("browser")
    except WebDriverException:
        return []
    return [{"level": x.get("level"), "message": x.get("message", "")} for x in logs]


def relevant_console_errors(logs: list[dict]) -> list[dict]:
    bad = []
    for item in logs:
        msg = item.get("message", "")
        level = item.get("level", "")
        if ERROR_PATTERNS.search(msg):
            bad.append(item)
        elif level == "SEVERE" and not re.search(r"favicon|404 \(Not Found\)|Failed to load resource", msg, re.I):
            bad.append(item)
    return bad


def fail_if(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        failures.append(message)


def scenario_check(driver: webdriver.Chrome, base: str, route: str, name: str, width: int, outdir: Path, failures: list[str], *, cache_bust: str | None = None) -> dict:
    set_viewport(driver, width)
    url = normalize_url(base, route, cache_bust)
    driver.get(url)
    wait_ready(driver)
    metrics = driver.execute_script(JS_METRICS)
    logs = collect_console(driver)
    errors = relevant_console_errors(logs)
    prefix = f"{name}@{width}"

    fail_if(metrics["docScrollWidth"] > metrics["docClientWidth"] + 1, f"{prefix}: body horizontal overflow {metrics['docScrollWidth']}>{metrics['docClientWidth']}", failures)
    if metrics["sidebarClientWidth"] is not None:
        fail_if(metrics["sidebarScrollWidth"] > metrics["sidebarClientWidth"] + 1, f"{prefix}: sidebar horizontal overflow {metrics['sidebarScrollWidth']}>{metrics['sidebarClientWidth']}", failures)

    sidebar_text = metrics["sidebarText"]
    for label in PRESENT:
        fail_if(label not in sidebar_text, f"{prefix}: sidebar missing {label}", failures)
    for label in ABSENT:
        fail_if(label in sidebar_text, f"{prefix}: sidebar contains removed module {label}", failures)

    fail_if(metrics["brandStrong"] != "VALTREN", f"{prefix}: brand strong is {metrics['brandStrong']!r}", failures)
    fail_if(metrics["brandSmall"] != "Sistema Interno", f"{prefix}: brand subtitle is {metrics['brandSmall']!r}", failures)
    fail_if("Autenticação desativada" not in metrics["accountText"], f"{prefix}: auth-disabled state missing from Account Menu", failures)

    if width > 980:
        sb = metrics["sidebar"] or {}
        fail_if(not (248 <= sb.get("width", 0) <= 252), f"{prefix}: desktop sidebar width={sb.get('width')}", failures)
        brand = metrics["brand"] or {}
        fail_if(not (32 <= brand.get("width", 0) <= 36 and 32 <= brand.get("height", 0) <= 36), f"{prefix}: desktop brand bounds={brand}", failures)
        last_bottom = -1
        for item in metrics["mainItems"]:
            r = item["rect"]
            fail_if(r["right"] > sb["right"] + 1, f"{prefix}: nav item exceeds sidebar: {item['text']}", failures)
            fail_if(r["width"] > sb["width"] + 1, f"{prefix}: nav item wider than sidebar: {item['text']}", failures)
            fail_if(r["top"] < last_bottom - 0.5, f"{prefix}: nav items overlap near {item['text']}", failures)
            last_bottom = r["bottom"]
    elif 761 <= width <= 980:
        sb = metrics["sidebar"] or {}
        fail_if(not (230 <= sb.get("width", 0) <= 234), f"{prefix}: tablet sidebar width={sb.get('width')}", failures)
        if metrics["accountSummary"]:
            fail_if(metrics["accountSummary"]["right"] > width + 1, f"{prefix}: Account Menu summary exceeds viewport", failures)
    else:
        sb = metrics["sidebar"] or {}
        fail_if(sb.get("left", 0) >= -1, f"{prefix}: mobile sidebar is not off-canvas when closed: {sb}", failures)
        fail_if(metrics["htmlLocked"] or metrics["bodyLocked"], f"{prefix}: body remains locked with drawer closed", failures)
        if metrics["topbar"]:
            fail_if(metrics["topbar"]["right"] > width + 1, f"{prefix}: header exceeds mobile viewport", failures)
        fail_if(bool(metrics["outOfBoundsControls"]), f"{prefix}: non-scrollable controls outside viewport: {metrics['outOfBoundsControls'][:4]}", failures)

    expected = EXPECTED_ACTIVE.get(route)
    if expected:
        active_texts = [x["text"] for x in metrics["active"]]
        fail_if(expected not in active_texts, f"{prefix}: active state expected {expected!r}, found {active_texts}", failures)
        matching = [x for x in metrics["active"] if x["text"] == expected]
        if matching:
            fail_if(all(x["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and x["shadow"] == "none" for x in matching), f"{prefix}: active state lacks structural visual treatment", failures)

    fail_if(bool(errors), f"{prefix}: relevant console errors: {errors[:3]}", failures)

    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
    shot = outdir / f"{safe}-{width}.png"
    driver.save_screenshot(str(shot))
    return {"name": name, "route": route, "width": width, "url": driver.current_url, "metrics": metrics, "console": logs, "relevant_console_errors": errors, "screenshot": shot.name}


def check_details_and_hierarchy(driver: webdriver.Chrome, base: str, outdir: Path, failures: list[str]) -> dict:
    set_viewport(driver, 1440)
    driver.get(normalize_url(base, "#/crm/dashboard"))
    wait_ready(driver)
    result = {}
    for label in ["Financeiro", "Jurídico", "Negócios"]:
        summary = driver.find_element(By.XPATH, f"//nav[contains(@class,'crm-nav')]/details/summary[.//span[normalize-space()='{label}']]")
        details = summary.find_element(By.XPATH, "..")
        if details.get_attribute("open"):
            driver.execute_script("arguments[0].click()", summary)
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.05)
        opened = details.get_attribute("open") is not None
        chevron = driver.execute_script("const b=arguments[0].querySelector('b');return b?getComputedStyle(b).transform:'';", summary)
        fail_if(not opened, f"details: {label} did not open", failures)
        fail_if(chevron in ("", "none"), f"details: {label} chevron did not rotate", failures)
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.03)
        fail_if(details.get_attribute("open") is not None, f"details: {label} did not close", failures)
        result[label] = {"opened": opened, "chevron_open_transform": chevron}

    legal_summary = driver.find_element(By.XPATH, "//nav[contains(@class,'crm-nav')]/details/summary[.//span[normalize-space()='Jurídico']]")
    driver.execute_script("arguments[0].click()", legal_summary)
    nested_summary = driver.find_element(By.CSS_SELECTOR, ".crm-nav-legal .crm-nav-subgroup > summary")
    driver.execute_script("arguments[0].click()", nested_summary)
    time.sleep(0.05)
    hierarchy = driver.execute_script(r"""
      const r=e=>{const x=e.getBoundingClientRect();return {left:x.left,right:x.right,top:x.top,width:x.width}};
      return {
        matters:r(document.querySelector('.crm-nav-legal a[href="#/crm/juridico"]')),
        subgroup:r(document.querySelector('.crm-nav-legal .crm-nav-subgroup > summary')),
        contract:r(document.querySelector('.crm-nav-legal a[href="#/crm/juridico/contratos"]')),
        templates:r(document.querySelector('.crm-nav-legal a[href="#/crm/juridico/contratos/templates"]')),
        variables:r(document.querySelector('.crm-nav-legal a[href="#/crm/juridico/contratos/variaveis"]')),
        bodyOverflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
      };
    """)
    fail_if(hierarchy["contract"]["left"] <= hierarchy["subgroup"]["left"] + 5, f"Contracts hierarchy not indented: {hierarchy}", failures)
    fail_if(hierarchy["templates"]["left"] != hierarchy["contract"]["left"] or hierarchy["variables"]["left"] != hierarchy["contract"]["left"], f"Contracts children are not aligned: {hierarchy}", failures)
    fail_if(hierarchy["bodyOverflow"] > 1, f"Contracts hierarchy causes body overflow: {hierarchy['bodyOverflow']}", failures)
    shot = outdir / "dashboard-1440-details-contracts.png"
    driver.save_screenshot(str(shot))
    result["contracts_hierarchy"] = hierarchy
    result["screenshot"] = shot.name
    return result


def check_account_menu_768(driver: webdriver.Chrome, base: str, failures: list[str]) -> list[dict]:
    routes = {k: MAIN_ROUTES[k] for k in ["dashboard", "crm", "finance", "business", "settings"]}
    results = []
    for name, route in routes.items():
        set_viewport(driver, 768)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        summary = driver.find_element(By.CSS_SELECTOR, ".crm-account-menu>summary")
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.04)
        data = driver.execute_script(r"""
          const r=e=>{const x=e.getBoundingClientRect();return {left:x.left,right:x.right,top:x.top,bottom:x.bottom,width:x.width,height:x.height}};
          const p=document.querySelector('.crm-account-popover');
          return {popover:r(p),docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth};
        """)
        fail_if(data["popover"]["right"] > 769 or data["popover"]["left"] < -1, f"account@768 {name}: popover out of viewport {data['popover']}", failures)
        fail_if(data["docSW"] > data["docCW"] + 1, f"account@768 {name}: body overflow", failures)
        driver.execute_script("arguments[0].click()", summary)
        results.append({"route": route, **data})
    return results


def check_drawer_cycle(driver: webdriver.Chrome, base: str, outdir: Path, failures: list[str]) -> dict:
    set_viewport(driver, 390, 844)
    driver.get(normalize_url(base, "#/crm/dashboard"))
    wait_ready(driver)
    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click()
    time.sleep(0.08)
    state_open = driver.execute_script("return {sidebar:document.querySelector('.crm-sidebar').classList.contains('is-open'),overlay:document.querySelector('.crm-sidebar-overlay').classList.contains('is-open'),html:document.documentElement.classList.contains('crm-sidebar-lock'),body:document.body.classList.contains('crm-sidebar-lock'),expanded:document.querySelector('.crm-mobile-nav-toggle').getAttribute('aria-expanded'),sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth};")
    for key in ["sidebar", "overlay", "html", "body"]:
        fail_if(not state_open[key], f"drawer: open state missing {key}", failures)
    fail_if(state_open["expanded"] != "true", f"drawer: aria-expanded is {state_open['expanded']}", failures)
    fail_if(state_open["sw"] > state_open["cw"] + 1, "drawer: body overflow while open", failures)
    shot = outdir / "dashboard-390-drawer-open.png"
    driver.save_screenshot(str(shot))

    driver.find_element(By.CSS_SELECTOR, ".crm-sidebar-overlay").click()
    time.sleep(0.06)
    closed_overlay = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock');")
    fail_if(not closed_overlay, "drawer: overlay did not close/unlock", failures)

    driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle").click()
    time.sleep(0.04)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(0.06)
    closed_escape = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.body.classList.contains('crm-sidebar-lock');")
    fail_if(not closed_escape, "drawer: Escape did not close/unlock", failures)

    driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle").click()
    time.sleep(0.04)
    crm_link = driver.find_element(By.CSS_SELECTOR, ".crm-sidebar a[href='#/crm/relationships']")
    crm_link.click()
    WebDriverWait(driver, 10).until(lambda d: "#/crm/relationships" in d.current_url)
    time.sleep(0.06)
    closed_route = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.body.classList.contains('crm-sidebar-lock')&&document.documentElement.scrollWidth<=document.documentElement.clientWidth+1;")
    fail_if(not closed_route, "drawer: route selection did not close/unlock cleanly", failures)
    errors = relevant_console_errors(collect_console(driver))
    fail_if(bool(errors), f"drawer: console errors {errors[:3]}", failures)
    return {"open": state_open, "overlay_close": closed_overlay, "escape_close": closed_escape, "route_close": closed_route, "screenshot": shot.name}


def check_compatibility(driver: webdriver.Chrome, base: str, failures: list[str]) -> list[dict]:
    checks = [
        ("valtrenchat", "#/crm/valtrenchat", "#/crm/configuracoes?tab=integracoes", ["Integrações", "Não conectado"]),
        ("rh", "#/crm/rh", None, ["RH", "Domínio de RH ainda não implementado"]),
        ("administracao", "#/crm/administracao", None, ["Administração", "Área administrativa ainda não implementada"]),
    ]
    results = []
    for name, route, expected_hash, texts in checks:
        set_viewport(driver, 1440)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        body = driver.find_element(By.TAG_NAME, "body").text
        sidebar = driver.find_element(By.CSS_SELECTOR, ".crm-sidebar").text
        if expected_hash:
            fail_if(expected_hash not in driver.current_url, f"compat {name}: expected redirect {expected_hash}, got {driver.current_url}", failures)
        for text in texts:
            fail_if(text not in body, f"compat {name}: missing honest compatibility text {text!r}", failures)
        for removed in ABSENT:
            fail_if(removed in sidebar, f"compat {name}: removed module leaked back into sidebar: {removed}", failures)
        errors = relevant_console_errors(collect_console(driver))
        fail_if(bool(errors), f"compat {name}: console errors {errors[:3]}", failures)
        results.append({"name": name, "route": route, "url": driver.current_url, "expected_texts": texts, "console_errors": errors})
    return results


def run(args: argparse.Namespace) -> int:
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    scenarios: list[dict] = []
    driver = build_driver()
    report: dict = {"mode": args.mode, "base_url": args.base_url, "failures": failures, "scenarios": scenarios}
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        if args.mode == "public":
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            scenarios.append(scenario_check(driver, args.base_url, "#/crm/dashboard", "dashboard-hard-cache-bypass", 1440, outdir, failures, cache_bust=str(int(time.time()))))
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": False})
            scenarios.append(scenario_check(driver, args.base_url, "#/crm/dashboard", "dashboard-normal-cache", 1440, outdir, failures))

        for width in [1440, 1280, 768, 390]:
            for name, route in MAIN_ROUTES.items():
                scenarios.append(scenario_check(driver, args.base_url, route, name, width, outdir, failures))
        for width in [1440, 390]:
            for name, route in EXTRA_ROUTES.items():
                scenarios.append(scenario_check(driver, args.base_url, route, name, width, outdir, failures))
        for name, route in MOBILE_EXTENDED.items():
            scenarios.append(scenario_check(driver, args.base_url, route, name, 390, outdir, failures))

        report["details"] = check_details_and_hierarchy(driver, args.base_url, outdir, failures)
        report["account_menu_768"] = check_account_menu_768(driver, args.base_url, failures)
        report["drawer_390"] = check_drawer_cycle(driver, args.base_url, outdir, failures)
        report["compatibility"] = check_compatibility(driver, args.base_url, failures)
    except (TimeoutException, JavascriptException, WebDriverException, AssertionError) as exc:
        failures.append(f"certification harness exception: {type(exc).__name__}: {exc}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    report["status"] = "PASS" if not failures else "FAIL"
    report["scenario_count"] = len(scenarios)
    (outdir / "visual-certification-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "mode": args.mode, "scenario_count": len(scenarios), "failures": failures}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Certifica visualmente o artifact ou deployment público do Sistema Interno Valtren.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["artifact", "public"], required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
