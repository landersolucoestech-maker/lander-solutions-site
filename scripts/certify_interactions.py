#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

ACCOUNT_ROUTES = [
    "#/crm/dashboard",
    "#/crm/relationships?tab=contacts",
    "#/crm/financeiro",
    "#/crm/juridico",
    "#/crm/negocios",
    "#/crm/marketing",
    "#/crm/relatorios",
    "#/crm/configuracoes?tab=empresa",
]


def driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def viewport(d: webdriver.Chrome, width: int, height: int) -> None:
    d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False,
    })


def url(base: str, route: str) -> str:
    return base.rstrip("/") + "/" + route


def ready(d: webdriver.Chrome) -> None:
    WebDriverWait(d, 15).until(lambda x: x.execute_script("return document.readyState") == "complete")
    WebDriverWait(d, 15).until(lambda x: x.find_elements(By.CSS_SELECTOR, ".crm-sidebar"))
    time.sleep(0.08)


def ensure(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def account_menu_checks(d: webdriver.Chrome, base: str, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for route in ACCOUNT_ROUTES:
        viewport(d, 768, 900)
        d.get(url(base, route))
        ready(d)
        details = d.find_element(By.CSS_SELECTOR, ".crm-account-menu")
        summary = d.find_element(By.CSS_SELECTOR, ".crm-account-menu>summary")

        initial = d.execute_script(r"""
          const s=document.querySelector('.crm-account-menu>summary'),r=s.getBoundingClientRect();
          return {left:r.left,right:r.right,width:r.width,height:r.height,docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth,text:document.querySelector('.crm-account-menu').innerText};
        """)
        ensure(initial["right"] <= 769 and initial["left"] >= -1, f"account@768 {route}: summary fora do viewport {initial}", failures)
        ensure(initial["height"] >= 40, f"account@768 {route}: target do summary abaixo de 40px: {initial['height']}", failures)
        ensure(initial["docSW"] <= initial["docCW"] + 1, f"account@768 {route}: body overflow fechado", failures)
        ensure("Autenticação desativada" in initial["text"], f"account@768 {route}: cópia de autenticação ausente", failures)
        ensure("Sem sessão ativa" in initial["text"], f"account@768 {route}: cópia de sessão ausente", failures)

        summary.click(); time.sleep(0.06)
        opened = d.execute_script(r"""
          const m=document.querySelector('.crm-account-menu'),c=document.querySelector('.crm-account-chevron'),p=document.querySelector('.crm-account-popover'),r=p.getBoundingClientRect();
          return {open:m.hasAttribute('open'),chevron:getComputedStyle(c).transform,popover:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth};
        """)
        ensure(opened["open"], f"account@768 {route}: não abriu", failures)
        ensure(opened["chevron"] not in ("", "none"), f"account@768 {route}: chevron não acompanha estado aberto", failures)
        ensure(opened["popover"]["left"] >= -1 and opened["popover"]["right"] <= 769, f"account@768 {route}: popover fora do viewport {opened['popover']}", failures)
        ensure(opened["docSW"] <= opened["docCW"] + 1, f"account@768 {route}: body overflow aberto", failures)

        d.execute_script("document.querySelector('.crm-main')?.click();")
        time.sleep(0.05)
        outside_closed = details.get_attribute("open") is None
        ensure(outside_closed, f"account@768 {route}: clique externo não fechou", failures)

        summary.click(); time.sleep(0.04)
        d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.05)
        escape_closed = details.get_attribute("open") is None
        ensure(escape_closed, f"account@768 {route}: Escape não fechou", failures)

        summary.click(); time.sleep(0.04)
        summary.send_keys(Keys.TAB); time.sleep(0.04)
        focus = d.execute_script(r"""
          const e=document.activeElement,s=getComputedStyle(e),menu=document.querySelector('.crm-account-menu');
          return {tag:e.tagName,text:(e.innerText||e.getAttribute('aria-label')||'').trim(),inside:menu.contains(e),outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,boxShadow:s.boxShadow};
        """)
        visible_focus = focus["inside"] and ((focus["outlineStyle"] not in ("", "none") and focus["outlineWidth"] != "0px") or focus["boxShadow"] != "none")
        ensure(focus["inside"], f"account@768 {route}: Tab saiu do fluxo do menu {focus}", failures)
        ensure(visible_focus, f"account@768 {route}: foco via Tab não é visível {focus}", failures)
        d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.03)

        results.append({"route": route, "initial": initial, "opened": opened, "outside_closed": outside_closed, "escape_closed": escape_closed, "tab_focus": focus})
    return results


def drawer_x_checks(d: webdriver.Chrome, base: str, failures: list[str]) -> dict[str, Any]:
    viewport(d, 390, 844)
    d.get(url(base, "#/crm/dashboard"))
    ready(d)
    toggle = d.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.08)
    opened = d.execute_script(r"""
      const sb=document.querySelector('.crm-sidebar'),x=document.querySelector('.crm-sidebar-close'),r=x.getBoundingClientRect();
      return {open:sb.classList.contains('is-open'),htmlLock:document.documentElement.classList.contains('crm-sidebar-lock'),bodyLock:document.body.classList.contains('crm-sidebar-lock'),focused:document.activeElement===x,closeRect:{left:r.left,right:r.right,width:r.width,height:r.height},docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth};
    """)
    ensure(opened["open"] and opened["htmlLock"] and opened["bodyLock"], f"drawer-x: estado/lock de abertura inválido {opened}", failures)
    ensure(opened["focused"], "drawer-x: foco inicial não foi para o botão Fechar navegação", failures)
    ensure(opened["closeRect"]["width"] >= 30 and opened["closeRect"]["height"] >= 30, f"drawer-x: target X abaixo de 30px {opened['closeRect']}", failures)
    ensure(opened["closeRect"]["left"] >= -1 and opened["closeRect"]["right"] <= 391, f"drawer-x: X fora do viewport {opened['closeRect']}", failures)
    ensure(opened["docSW"] <= opened["docCW"] + 1, "drawer-x: body overflow com drawer aberto", failures)

    d.find_element(By.CSS_SELECTOR, ".crm-sidebar-close").click(); time.sleep(0.06)
    closed = d.execute_script(r"""
      return {open:document.querySelector('.crm-sidebar').classList.contains('is-open'),htmlLock:document.documentElement.classList.contains('crm-sidebar-lock'),bodyLock:document.body.classList.contains('crm-sidebar-lock'),toggleFocused:document.activeElement===document.querySelector('.crm-mobile-nav-toggle'),expanded:document.querySelector('.crm-mobile-nav-toggle').getAttribute('aria-expanded'),docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth};
    """)
    ensure(not closed["open"] and not closed["htmlLock"] and not closed["bodyLock"], f"drawer-x: X não fechou/restaurou lock {closed}", failures)
    ensure(closed["expanded"] == "false", f"drawer-x: aria-expanded não voltou a false {closed}", failures)
    ensure(closed["toggleFocused"], "drawer-x: foco não retornou ao botão Menu", failures)
    ensure(closed["docSW"] <= closed["docCW"] + 1, "drawer-x: body overflow após fechar", failures)
    return {"opened": opened, "closed": closed}


def console_errors(d: webdriver.Chrome) -> list[dict[str, str]]:
    try:
        logs = d.get_log("browser")
    except WebDriverException:
        return []
    return [x for x in logs if x.get("level") == "SEVERE" and "favicon" not in x.get("message", "").lower() and "404" not in x.get("message", "")]


def run(args: argparse.Namespace) -> int:
    failures: list[str] = []
    d = driver()
    report: dict[str, Any] = {"mode": args.mode, "base_url": args.base_url, "failures": failures}
    try:
        report["account_menu_768"] = account_menu_checks(d, args.base_url, failures)
        report["drawer_x_390"] = drawer_x_checks(d, args.base_url, failures)
        errors = console_errors(d)
        ensure(not errors, f"console relevante durante interações: {errors[:3]}", failures)
        report["console_errors"] = errors
    finally:
        d.quit()
    report["status"] = "PASS" if not failures else "FAIL"
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "interaction-certification-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "mode": args.mode, "failures": failures}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Certificação complementar de Account Menu e drawer móvel.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["artifact", "public"], required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
