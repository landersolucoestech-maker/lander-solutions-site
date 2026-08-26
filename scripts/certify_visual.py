#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

PRESENT_SIDEBAR = [
    "Dashboard", "CRM", "Agenda", "Financeiro", "Jurídico",
    "Marketing", "Negócios", "Relatórios", "Configurações",
]
ABSENT_SIDEBAR = ["ValtrenChat", "MusicChat", "RH", "Administração"]
BREAKPOINTS = [1440, 1280, 1024, 768, 390]

# Representative templates receive the complete breakpoint matrix. Every other
# valid route is still rendered at desktop + mobile below.
TEMPLATE_MATRIX: dict[str, str] = {
    "dashboard": "#/crm/dashboard",
    "crm-contacts": "#/crm/relationships?tab=contacts",
    "agenda": "#/crm/agenda",
    "finance-transactions": "#/crm/financeiro",
    "legal-matters": "#/crm/juridico",
    "marketing": "#/crm/marketing",
    "business-products": "#/crm/negocios",
    "reports": "#/crm/relatorios",
    "settings-company": "#/crm/configuracoes?tab=empresa",
}

CANONICAL_ROUTES: dict[str, str] = {
    "dashboard": "#/crm/dashboard",
    "crm-contacts": "#/crm/relationships?tab=contacts",
    "crm-leads": "#/crm/relationships?tab=leads",
    "agenda": "#/crm/agenda",
    "finance-transactions": "#/crm/financeiro",
    "finance-accounting": "#/crm/financeiro/accounting",
    "finance-invoices": "#/crm/financeiro/invoices",
    "finance-rules": "#/crm/financeiro/rules",
    "finance-categories": "#/crm/financeiro/categories",
    "finance-rateios": "#/crm/financeiro/rateios",
    "finance-participations": "#/crm/financeiro/participacoes",
    "finance-payouts": "#/crm/financeiro/repasses",
    "legal-matters": "#/crm/juridico",
    "legal-contracts": "#/crm/juridico/contratos",
    "legal-templates": "#/crm/juridico/contratos/templates",
    "legal-variables": "#/crm/juridico/contratos/variaveis",
    "legal-compliance": "#/crm/juridico/compliance",
    "legal-ip": "#/crm/juridico/propriedade-intelectual",
    "legal-corporate": "#/crm/juridico/societario",
    "marketing": "#/crm/marketing",
    "business-products": "#/crm/negocios",
    "business-services": "#/crm/negocios/servicos",
    "business-units": "#/crm/negocios/unidades",
    "reports": "#/crm/relatorios",
    "settings-company": "#/crm/configuracoes?tab=empresa",
    "settings-notifications": "#/crm/configuracoes?tab=notificacoes",
    "settings-security": "#/crm/configuracoes?tab=seguranca",
    "settings-integrations": "#/crm/configuracoes?tab=integracoes",
    "settings-audit": "#/crm/configuracoes?tab=auditoria",
    "settings-users": "#/crm/configuracoes?tab=usuarios",
    "account-profile": "#/crm/meu-perfil",
}

COMPATIBILITY_ROUTES: dict[str, tuple[str, str | None, tuple[str, ...]]] = {
    "compat-valtrenchat": (
        "#/crm/valtrenchat",
        "#/crm/configuracoes?tab=integracoes",
        ("Integrações", "Não configurado"),
    ),
    "compat-musicchat": (
        "#/crm/musicchat",
        "#/crm/configuracoes?tab=integracoes",
        ("Integrações", "Não configurado"),
    ),
    "compat-rh": (
        "#/crm/rh",
        None,
        ("RH", "Domínio de RH ainda não implementado"),
    ),
    "compat-admin": (
        "#/crm/administracao",
        None,
        ("Administração", "Área administrativa ainda não implementada"),
    ),
    "compat-admin-assets": (
        "#/crm/administracao/patrimonio-licencas",
        None,
        ("Administração", "Área administrativa ainda não implementada"),
    ),
    "compat-profile": (
        "#/crm/configuracoes/profile",
        "#/crm/meu-perfil",
        ("Autenticação desativada",),
    ),
    "compat-users": (
        "#/crm/configuracoes/users",
        "#/crm/configuracoes?tab=usuarios",
        ("Usuários", "Autenticação desativada"),
    ),
    "compat-audit": (
        "#/crm/configuracoes/audit",
        "#/crm/configuracoes?tab=auditoria",
        ("Auditoria",),
    ),
    "compat-integrations": (
        "#/crm/configuracoes/integracoes",
        "#/crm/configuracoes?tab=integracoes",
        ("Integrações", "Não configurado"),
    ),
    "compat-billing": (
        "#/crm/configuracoes/billing",
        "#/crm/configuracoes?tab=empresa",
        ("Empresa",),
    ),
    "compat-admin-access": (
        "#/crm/administracao/acessos-permissoes",
        "#/crm/configuracoes?tab=usuarios",
        ("Usuários", "Autenticação desativada"),
    ),
    "compat-admin-audit": (
        "#/crm/administracao/auditoria",
        "#/crm/configuracoes?tab=auditoria",
        ("Auditoria",),
    ),
    "compat-admin-integrations": (
        "#/crm/administracao/integracoes",
        "#/crm/configuracoes?tab=integracoes",
        ("Integrações", "Não configurado"),
    ),
}

EXPECTED_ACTIVE: dict[str, str] = {
    "#/crm/dashboard": "Dashboard",
    "#/crm/relationships?tab=contacts": "CRM",
    "#/crm/relationships?tab=leads": "CRM",
    "#/crm/agenda": "Agenda",
    "#/crm/financeiro": "Transações",
    "#/crm/financeiro/accounting": "Contabilidade",
    "#/crm/financeiro/invoices": "Notas Fiscais",
    "#/crm/financeiro/rateios": "Rateios",
    "#/crm/financeiro/participacoes": "Participações",
    "#/crm/financeiro/repasses": "Repasses",
    "#/crm/juridico": "Assuntos Jurídicos",
    "#/crm/juridico/contratos": "Contratos",
    "#/crm/juridico/contratos/templates": "Templates",
    "#/crm/juridico/contratos/variaveis": "Variáveis",
    "#/crm/juridico/compliance": "Compliance e Políticas",
    "#/crm/juridico/propriedade-intelectual": "Propriedade Intelectual",
    "#/crm/juridico/societario": "Societário",
    "#/crm/marketing": "Marketing",
    "#/crm/negocios": "Produtos",
    "#/crm/negocios/servicos": "Serviços",
    "#/crm/negocios/unidades": "Unidades de Negócio",
    "#/crm/relatorios": "Relatórios",
    "#/crm/configuracoes?tab=empresa": "Configurações",
    "#/crm/configuracoes?tab=notificacoes": "Configurações",
    "#/crm/configuracoes?tab=seguranca": "Configurações",
    "#/crm/configuracoes?tab=integracoes": "Configurações",
    "#/crm/configuracoes?tab=auditoria": "Configurações",
    "#/crm/configuracoes?tab=usuarios": "Configurações",
}

ERROR_PATTERNS = re.compile(
    r"SyntaxError|ReferenceError|TypeError|Unhandled|Uncaught|handler exception|route exception|event handler exception",
    re.I,
)

DOM_AUDIT = r"""
const rect=(el)=>{
  if(!el)return null;
  const r=el.getBoundingClientRect();
  return {x:r.x,y:r.y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
};
const visible=(el)=>{
  if(!el)return false;
  const s=getComputedStyle(el),r=el.getBoundingClientRect();
  return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&r.width>0&&r.height>0;
};
const css=(el)=>el?getComputedStyle(el):null;
const scrollAncestor=(el)=>{
  for(let p=el.parentElement;p&&p!==document.body;p=p.parentElement){
    const s=getComputedStyle(p);
    if(/auto|scroll/.test(s.overflowX) && p.scrollWidth>p.clientWidth+1)return true;
  }
  return false;
};
const labelled=(el)=>{
  if(el.closest('label'))return true;
  if(el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`))return true;
  return Boolean(el.getAttribute('aria-label')||el.getAttribute('aria-labelledby')||el.getAttribute('title'));
};
const sb=document.querySelector('.crm-sidebar');
const shell=document.querySelector('.crm-app-shell');
const main=document.querySelector('.crm-main');
const workspace=document.querySelector('.crm-workspace,.crm-ref-workspace,.crm-fidelity-workspace');
const topbar=document.querySelector('.crm-topbar');
const account=document.querySelector('.crm-account-menu>summary');
const brand=document.querySelector('.crm-brand img');
const navItems=[...document.querySelectorAll('.crm-nav > a,.crm-nav > .crm-nav-group > summary')].filter(visible);
const active=[...document.querySelectorAll('.crm-nav a.active')].filter(visible).map(el=>({
  text:(el.textContent||'').replace(/\s+/g,' ').trim(),href:el.getAttribute('href'),rect:rect(el),
  bg:css(el).backgroundColor,shadow:css(el).boxShadow,color:css(el).color,fontSize:css(el).fontSize
}));
const controls=[...document.querySelectorAll('input,select,textarea,button')].filter(visible);
const outOfBoundsControls=controls.filter(el=>!el.closest('.crm-sidebar')&&!scrollAncestor(el)).map(el=>({
  tag:el.tagName,text:(el.innerText||el.getAttribute('aria-label')||el.name||'').trim().slice(0,80),rect:rect(el)
})).filter(x=>x.rect.left<-1||x.rect.right>innerWidth+1);
const unlabeled=[...document.querySelectorAll('input:not([type="hidden"]),select,textarea')].filter(visible).filter(el=>!labelled(el)).map(el=>({
  tag:el.tagName,id:el.id||'',name:el.name||'',type:el.type||'',placeholder:el.getAttribute('placeholder')||''
}));
const duplicateIds=Object.entries([...document.querySelectorAll('[id]')].reduce((a,e)=>(a[e.id]=(a[e.id]||0)+1,a),{})).filter(([,n])=>n>1);
const anchorsWithoutHref=[...document.querySelectorAll('a:not([href])')].filter(visible).map(el=>(el.textContent||'').trim().slice(0,80));
const mobileTargets=[...document.querySelectorAll('button,a[href],summary,input,select')].filter(visible).filter(el=>!el.closest('.crm-sidebar')||sb?.classList.contains('is-open')).map(el=>({
  tag:el.tagName,text:(el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,60),rect:rect(el)
})).filter(x=>x.rect.width<30||x.rect.height<30);
const images=[...document.images].filter(visible).map(el=>({src:(el.getAttribute('src')||'').split('/').pop(),alt:el.getAttribute('alt'),rect:rect(el),naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight}));
const largeScrollers=[...document.querySelectorAll('.crm-main,.crm-workspace,.crm-ref-workspace,.crm-fidelity-workspace')].filter(visible).filter(el=>{
  const s=css(el); return /auto|scroll/.test(s.overflowY)&&el.scrollHeight>el.clientHeight+2&&el.clientHeight>innerHeight*.45;
}).map(el=>({className:el.className,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight,overflowY:css(el).overflowY}));
const styleSamples={
  pageTitles:[...document.querySelectorAll('.crm-topbar h1,.crm-page-header h1,.crm-page-header h2')].filter(visible).slice(0,3).map(el=>({fontFamily:css(el).fontFamily,fontSize:css(el).fontSize,lineHeight:css(el).lineHeight,fontWeight:css(el).fontWeight,letterSpacing:css(el).letterSpacing})),
  buttons:controls.filter(el=>el.tagName==='BUTTON').slice(0,20).map(el=>({height:rect(el).height,fontSize:css(el).fontSize,fontFamily:css(el).fontFamily,borderRadius:css(el).borderRadius,padding:css(el).padding})),
  fields:controls.filter(el=>['INPUT','SELECT','TEXTAREA'].includes(el.tagName)).slice(0,20).map(el=>({tag:el.tagName,height:rect(el).height,fontSize:css(el).fontSize,fontFamily:css(el).fontFamily,borderRadius:css(el).borderRadius})),
  tableHeaders:[...document.querySelectorAll('th')].filter(visible).slice(0,12).map(el=>({fontSize:css(el).fontSize,fontWeight:css(el).fontWeight,textTransform:css(el).textTransform,padding:css(el).padding})),
  cards:[...document.querySelectorAll('.crm-panel,.crm-ref-panel,.crm-rel-table-card,.crm-ref-table-card,.crm-kpi,.crm-ref-kpi')].filter(visible).slice(0,12).map(el=>({padding:css(el).padding,borderRadius:css(el).borderRadius,boxShadow:css(el).boxShadow,border:css(el).border})),
};
const internalLinks=[...document.querySelectorAll('a[href^="#/crm/"]')].map(a=>a.getAttribute('href')).filter(Boolean);
return {
  viewport:{width:innerWidth,height:innerHeight},
  doc:{scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,scrollHeight:document.documentElement.scrollHeight,clientHeight:document.documentElement.clientHeight},
  body:{scrollWidth:document.body?.scrollWidth||0,scrollHeight:document.body?.scrollHeight||0,bg:css(document.body)?.backgroundColor||''},
  shell:rect(shell),main:rect(main),workspace:rect(workspace),topbar:rect(topbar),accountSummary:rect(account),
  sidebar:rect(sb),sidebarScrollWidth:sb?.scrollWidth??null,sidebarClientWidth:sb?.clientWidth??null,sidebarClass:sb?.className||'',sidebarTransform:css(sb)?.transform||'',
  sidebarText:(sb?.innerText||'').replace(/\s+/g,' ').trim(),
  brand:rect(brand),brandStrong:(document.querySelector('.crm-brand strong')?.textContent||'').trim(),brandSmall:(document.querySelector('.crm-brand small')?.textContent||'').trim(),
  navItems:navItems.map(el=>({text:(el.textContent||'').replace(/\s+/g,' ').trim(),rect:rect(el)})),active,
  accountText:(document.querySelector('.crm-account-menu')?.textContent||'').replace(/\s+/g,' ').trim(),
  outOfBoundsControls,unlabeled,duplicateIds,anchorsWithoutHref,mobileTargets,images,largeScrollers,styleSamples,internalLinks,
  htmlLocked:document.documentElement.classList.contains('crm-sidebar-lock'),bodyLocked:document.body?.classList.contains('crm-sidebar-lock')||false,
};
"""


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--window-size=1440,1000")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def set_viewport(driver: webdriver.Chrome, width: int, height: int | None = None) -> None:
    if height is None:
        height = 1000 if width >= 768 else 844
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False,
    })


def normalize_url(base: str, route: str, cache_bust: str | None = None) -> str:
    base = base.rstrip("/") + "/"
    return base + (("?cert=" + cache_bust) if cache_bust else "") + route


def wait_ready(driver: webdriver.Chrome) -> None:
    WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 15).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".crm-sidebar"))
    time.sleep(0.10)


def collect_console(driver: webdriver.Chrome) -> list[dict[str, str]]:
    try:
        logs = driver.get_log("browser")
    except WebDriverException:
        return []
    return [{"level": x.get("level", ""), "message": x.get("message", "")} for x in logs]


def relevant_console_errors(logs: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in logs:
        msg = item.get("message", "")
        level = item.get("level", "")
        if ERROR_PATTERNS.search(msg):
            out.append(item)
        elif level == "SEVERE" and not re.search(r"favicon|404 \(Not Found\)|Failed to load resource", msg, re.I):
            out.append(item)
    return out


def fail_if(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        failures.append(message)


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")


def audit_scenario(
    driver: webdriver.Chrome,
    base: str,
    route: str,
    name: str,
    width: int,
    outdir: Path,
    failures: list[str],
    *,
    cache_bust: str | None = None,
    screenshot: bool = True,
) -> dict[str, Any]:
    set_viewport(driver, width)
    driver.get(normalize_url(base, route, cache_bust))
    wait_ready(driver)
    metrics = driver.execute_script(DOM_AUDIT)
    logs = collect_console(driver)
    errors = relevant_console_errors(logs)
    prefix = f"{name}@{width}"

    fail_if(metrics["doc"]["scrollWidth"] > metrics["doc"]["clientWidth"] + 1,
            f"{prefix}: BODY horizontal overflow {metrics['doc']['scrollWidth']}>{metrics['doc']['clientWidth']}", failures)
    if metrics["sidebarClientWidth"] is not None:
        fail_if(metrics["sidebarScrollWidth"] > metrics["sidebarClientWidth"] + 1,
                f"{prefix}: Sidebar horizontal overflow {metrics['sidebarScrollWidth']}>{metrics['sidebarClientWidth']}", failures)

    sidebar_text = metrics["sidebarText"]
    for label in PRESENT_SIDEBAR:
        fail_if(label not in sidebar_text, f"{prefix}: Sidebar missing {label}", failures)
    for label in ABSENT_SIDEBAR:
        fail_if(label in sidebar_text, f"{prefix}: removed Sidebar module leaked: {label}", failures)

    fail_if(metrics["brandStrong"] != "VALTREN", f"{prefix}: brand title={metrics['brandStrong']!r}", failures)
    fail_if(metrics["brandSmall"] != "Sistema Interno", f"{prefix}: brand subtitle={metrics['brandSmall']!r}", failures)
    fail_if("Autenticação desativada" not in metrics["accountText"], f"{prefix}: Account Menu does not expose auth-disabled state", failures)

    shell = metrics.get("shell") or {}
    fail_if(shell and shell.get("bottom", 0) < metrics["viewport"]["height"] - 1,
            f"{prefix}: app shell ends before viewport (possible white footer gap): {shell}", failures)
    fail_if(bool(metrics["largeScrollers"]) and metrics["doc"]["scrollHeight"] > metrics["doc"]["clientHeight"] + 2,
            f"{prefix}: double-scroll candidate {metrics['largeScrollers']}", failures)
    fail_if(bool(metrics["duplicateIds"]), f"{prefix}: duplicate DOM ids {metrics['duplicateIds'][:5]}", failures)
    fail_if(bool(metrics["anchorsWithoutHref"]), f"{prefix}: visible anchors without href {metrics['anchorsWithoutHref'][:5]}", failures)

    if width > 980:
        sb = metrics.get("sidebar") or {}
        fail_if(not (248 <= sb.get("width", 0) <= 252), f"{prefix}: desktop Sidebar width={sb.get('width')}", failures)
        brand = metrics.get("brand") or {}
        fail_if(not (32 <= brand.get("width", 0) <= 36 and 32 <= brand.get("height", 0) <= 36),
                f"{prefix}: brand image bounds={brand}", failures)
        previous_bottom = -1.0
        for item in metrics["navItems"]:
            r = item["rect"]
            fail_if(r["right"] > sb.get("right", 0) + 1, f"{prefix}: nav item exceeds Sidebar: {item['text']}", failures)
            fail_if(r["top"] < previous_bottom - 0.5, f"{prefix}: nav overlap near {item['text']}", failures)
            previous_bottom = r["bottom"]
    elif 761 <= width <= 980:
        sb = metrics.get("sidebar") or {}
        fail_if(not (230 <= sb.get("width", 0) <= 234), f"{prefix}: tablet Sidebar width={sb.get('width')}", failures)
        if metrics.get("accountSummary"):
            fail_if(metrics["accountSummary"]["right"] > width + 1, f"{prefix}: Account Menu summary exceeds viewport", failures)
    else:
        sb = metrics.get("sidebar") or {}
        fail_if(sb.get("left", 0) >= -1, f"{prefix}: mobile Sidebar is not off-canvas while closed: {sb}", failures)
        fail_if(metrics["htmlLocked"] or metrics["bodyLocked"], f"{prefix}: body lock remains after drawer closed", failures)
        topbar = metrics.get("topbar") or {}
        fail_if(topbar and topbar.get("right", 0) > width + 1, f"{prefix}: Header exceeds mobile viewport", failures)
        fail_if(bool(metrics["outOfBoundsControls"]), f"{prefix}: controls outside mobile viewport {metrics['outOfBoundsControls'][:5]}", failures)
        # Targets below 30px are recorded as an accessibility finding only for
        # icon/summary/button/link controls, not form inputs that may be compact.
        tiny = [x for x in metrics["mobileTargets"] if x["tag"] in ("BUTTON", "A", "SUMMARY")]
        fail_if(bool(tiny), f"{prefix}: interactive mobile targets below 30px {tiny[:5]}", failures)

    expected = EXPECTED_ACTIVE.get(route)
    if expected:
        matching = [x for x in metrics["active"] if x["text"] == expected]
        fail_if(not matching, f"{prefix}: active state expected {expected!r}, found {[x['text'] for x in metrics['active']]}", failures)
        if matching:
            fail_if(all(x["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and x["shadow"] == "none" for x in matching),
                    f"{prefix}: active state has no visible treatment", failures)

    # Placeholder is not a label. Missing labels are a real accessibility issue.
    fail_if(bool(metrics["unlabeled"]), f"{prefix}: unlabeled visible form controls {metrics['unlabeled'][:6]}", failures)
    fail_if(bool(errors), f"{prefix}: relevant console errors {errors[:3]}", failures)

    shot_name = None
    if screenshot:
        shot_name = f"{safe_name(name)}-{width}.png"
        driver.save_screenshot(str(outdir / shot_name))
    return {
        "name": name, "route": route, "width": width, "url": driver.current_url,
        "metrics": metrics, "console": logs, "relevant_console_errors": errors,
        "screenshot": shot_name,
    }


def check_details(driver: webdriver.Chrome, base: str, outdir: Path, failures: list[str]) -> dict[str, Any]:
    set_viewport(driver, 1440)
    driver.get(normalize_url(base, "#/crm/dashboard"))
    wait_ready(driver)
    result: dict[str, Any] = {}
    for label in ["Financeiro", "Jurídico", "Negócios"]:
        summary = driver.find_element(By.XPATH, f"//nav[contains(@class,'crm-nav')]/details/summary[.//span[normalize-space()='{label}']]")
        details = summary.find_element(By.XPATH, "..")
        if details.get_attribute("open") is not None:
            driver.execute_script("arguments[0].click()", summary)
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.05)
        opened = details.get_attribute("open") is not None
        transform = driver.execute_script("const b=arguments[0].querySelector('b');return b?getComputedStyle(b).transform:'';", summary)
        fail_if(not opened, f"details {label}: failed to open", failures)
        fail_if(transform in ("", "none"), f"details {label}: chevron did not change", failures)
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.04)
        fail_if(details.get_attribute("open") is not None, f"details {label}: failed to close", failures)
        result[label] = {"opened": opened, "chevron_open_transform": transform}

    legal = driver.find_element(By.XPATH, "//nav[contains(@class,'crm-nav')]/details/summary[.//span[normalize-space()='Jurídico']]")
    driver.execute_script("arguments[0].click()", legal)
    nested = driver.find_element(By.CSS_SELECTOR, ".crm-nav-legal .crm-nav-subgroup > summary")
    driver.execute_script("arguments[0].click()", nested)
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
    fail_if(hierarchy["contract"]["left"] <= hierarchy["subgroup"]["left"] + 5, f"Contracts hierarchy not nested: {hierarchy}", failures)
    fail_if(abs(hierarchy["templates"]["left"] - hierarchy["contract"]["left"]) > 1 or abs(hierarchy["variables"]["left"] - hierarchy["contract"]["left"]) > 1,
            f"Contracts children misaligned: {hierarchy}", failures)
    fail_if(hierarchy["bodyOverflow"] > 1, f"Contracts hierarchy causes body overflow: {hierarchy['bodyOverflow']}", failures)
    shot = "dashboard-1440-details-contracts.png"
    driver.save_screenshot(str(outdir / shot))
    result["contracts_hierarchy"] = hierarchy
    result["screenshot"] = shot
    return result


def check_account_menu(driver: webdriver.Chrome, base: str, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    routes = [
        "#/crm/dashboard", "#/crm/relationships?tab=contacts", "#/crm/financeiro",
        "#/crm/juridico", "#/crm/negocios", "#/crm/marketing", "#/crm/relatorios", "#/crm/configuracoes?tab=empresa",
    ]
    for route in routes:
        set_viewport(driver, 768)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        summary = driver.find_element(By.CSS_SELECTOR, ".crm-account-menu>summary")
        driver.execute_script("arguments[0].click()", summary)
        time.sleep(0.05)
        data = driver.execute_script(r"""
          const r=e=>{const x=e.getBoundingClientRect();return {left:x.left,right:x.right,top:x.top,bottom:x.bottom,width:x.width,height:x.height}};
          const p=document.querySelector('.crm-account-popover');
          return {popover:p?r(p):null,summary:r(document.querySelector('.crm-account-menu>summary')),docSW:document.documentElement.scrollWidth,docCW:document.documentElement.clientWidth,text:(p?.innerText||'').trim()};
        """)
        fail_if(not data["popover"], f"Account Menu@768 {route}: popover missing", failures)
        if data["popover"]:
            fail_if(data["popover"]["right"] > 769 or data["popover"]["left"] < -1, f"Account Menu@768 {route}: popover outside viewport {data['popover']}", failures)
        fail_if(data["docSW"] > data["docCW"] + 1, f"Account Menu@768 {route}: body overflow", failures)
        fail_if("Autenticação desativada" not in data["text"], f"Account Menu@768 {route}: auth-disabled copy missing", failures)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.03)
        results.append({"route": route, **data})
    return results


def check_drawer(driver: webdriver.Chrome, base: str, outdir: Path, failures: list[str]) -> dict[str, Any]:
    set_viewport(driver, 390, 844)
    driver.get(normalize_url(base, "#/crm/dashboard"))
    wait_ready(driver)
    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click()
    time.sleep(0.08)
    opened = driver.execute_script("return {sidebar:document.querySelector('.crm-sidebar').classList.contains('is-open'),overlay:document.querySelector('.crm-sidebar-overlay').classList.contains('is-open'),html:document.documentElement.classList.contains('crm-sidebar-lock'),body:document.body.classList.contains('crm-sidebar-lock'),expanded:document.querySelector('.crm-mobile-nav-toggle').getAttribute('aria-expanded'),sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth};")
    for key in ("sidebar", "overlay", "html", "body"):
        fail_if(not opened[key], f"drawer: open state missing {key}", failures)
    fail_if(opened["expanded"] != "true", f"drawer: aria-expanded={opened['expanded']}", failures)
    fail_if(opened["sw"] > opened["cw"] + 1, "drawer: BODY overflow while open", failures)
    shot = "dashboard-390-drawer-open.png"
    driver.save_screenshot(str(outdir / shot))

    driver.find_element(By.CSS_SELECTOR, ".crm-sidebar-overlay").click()
    time.sleep(0.05)
    overlay_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock');")
    fail_if(not overlay_close, "drawer: overlay did not close/unlock", failures)

    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.04)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.05)
    escape_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock');")
    fail_if(not escape_close, "drawer: Escape did not close/unlock", failures)

    toggle = driver.find_element(By.CSS_SELECTOR, ".crm-mobile-nav-toggle")
    toggle.click(); time.sleep(0.04)
    driver.find_element(By.CSS_SELECTOR, ".crm-sidebar a[href='#/crm/relationships']").click()
    WebDriverWait(driver, 10).until(lambda d: "#/crm/relationships" in d.current_url)
    time.sleep(0.05)
    route_close = driver.execute_script("return !document.querySelector('.crm-sidebar').classList.contains('is-open')&&!document.documentElement.classList.contains('crm-sidebar-lock')&&!document.body.classList.contains('crm-sidebar-lock')&&document.documentElement.scrollWidth<=document.documentElement.clientWidth+1;")
    fail_if(not route_close, "drawer: route selection did not close/unlock", failures)
    fail_if(bool(relevant_console_errors(collect_console(driver))), "drawer: console error during interaction", failures)
    return {"open": opened, "overlay_close": overlay_close, "escape_close": escape_close, "route_close": route_close, "screenshot": shot}


def check_compatibility(driver: webdriver.Chrome, base: str, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, (route, expected_hash, texts) in COMPATIBILITY_ROUTES.items():
        set_viewport(driver, 1440)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        body = driver.find_element(By.TAG_NAME, "body").text
        sidebar = driver.find_element(By.CSS_SELECTOR, ".crm-sidebar").text
        if expected_hash:
            fail_if(expected_hash not in driver.current_url, f"{name}: expected redirect {expected_hash}, got {driver.current_url}", failures)
        for text in texts:
            fail_if(text not in body, f"{name}: missing honest compatibility text {text!r}", failures)
        for removed in ABSENT_SIDEBAR:
            fail_if(removed in sidebar, f"{name}: removed module leaked back into Sidebar: {removed}", failures)
        if "integracoes" in (expected_hash or route):
            fail_if("Conectado" in body or "Sincronizado" in body, f"{name}: integration state falsely appears connected/synchronized", failures)
        errors = relevant_console_errors(collect_console(driver))
        fail_if(bool(errors), f"{name}: console errors {errors[:3]}", failures)
        results.append({"name": name, "route": route, "url": driver.current_url, "expected_texts": texts, "console_errors": errors})
    return results


def check_keyboard_focus(driver: webdriver.Chrome, base: str, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for width, route in [(1440, "#/crm/dashboard"), (768, "#/crm/configuracoes?tab=integracoes"), (390, "#/crm/dashboard")]:
        set_viewport(driver, width)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        driver.execute_script("document.body.focus();")
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)
        time.sleep(0.03)
        sample = driver.execute_script(r"""
          const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();
          return {tag:e.tagName,text:(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,80),outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,boxShadow:s.boxShadow,borderColor:s.borderColor,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
        """)
        visible_focus = sample["outlineStyle"] not in ("none", "") and sample["outlineWidth"] != "0px"
        visible_focus = visible_focus or sample["boxShadow"] != "none"
        fail_if(sample["tag"] in ("BODY", "HTML"), f"keyboard@{width}: Tab did not reach an interactive element", failures)
        fail_if(not visible_focus, f"keyboard@{width}: first keyboard focus lacks visible indicator {sample}", failures)
        results.append({"width": width, "route": route, "first_focus": sample})
    return results


def attempt_modal_audit(driver: webdriver.Chrome, base: str, outdir: Path, failures: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    routes = ["#/crm/relationships?tab=contacts", "#/crm/agenda", "#/crm/financeiro", "#/crm/negocios", "#/crm/juridico/contratos"]
    for route in routes:
        set_viewport(driver, 390, 844)
        driver.get(normalize_url(base, route))
        wait_ready(driver)
        opened = driver.execute_script(r"""
          const candidates=[...document.querySelectorAll('button')].filter(b=>{
            const r=b.getBoundingClientRect(),s=getComputedStyle(b),t=(b.innerText||b.getAttribute('aria-label')||'').trim();
            return r.width>0&&r.height>0&&s.display!=='none'&&/^(Novo|Nova|Adicionar|Criar)\b/i.test(t);
          });
          if(!candidates.length)return null;
          candidates[0].click();
          return (candidates[0].innerText||candidates[0].getAttribute('aria-label')||'').trim();
        """)
        if not opened:
            results.append({"route": route, "status": "not-applicable", "reason": "no visible create/open modal action"})
            continue
        time.sleep(0.10)
        modal = driver.execute_script(r"""
          const sels=['.crm-ref-modal-root .crm-ref-modal','.crm-rel-modal-root .crm-rel-modal','.crm-modal-root .crm-modal','.modal[role="dialog"]','[role="dialog"]'];
          let el=null; for(const s of sels){el=document.querySelector(s); if(el)break;}
          if(!el)return null;
          const r=el.getBoundingClientRect(),cs=getComputedStyle(el);
          return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,maxHeight:cs.maxHeight,overflowY:cs.overflowY,role:el.getAttribute('role'),ariaModal:el.getAttribute('aria-modal')};
        """)
        if not modal:
            results.append({"route": route, "status": "not-applicable", "opener": opened, "reason": "action did not open a detectable modal"})
            continue
        fail_if(modal["left"] < -1 or modal["right"] > 391 or modal["top"] < -1 or modal["bottom"] > 845,
                f"modal@390 {route}: modal exceeds viewport {modal}", failures)
        shot = f"modal-{safe_name(route)}-390.png"
        driver.save_screenshot(str(outdir / shot))
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.05)
        results.append({"route": route, "status": "audited", "opener": opened, "modal": modal, "screenshot": shot})
    return results


def summarize_design_system(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    fonts: set[str] = set()
    title_sizes: set[str] = set()
    button_heights: set[float] = set()
    button_radii: set[str] = set()
    field_heights: set[float] = set()
    field_radii: set[str] = set()
    table_header_sizes: set[str] = set()
    card_radii: set[str] = set()
    for item in scenarios:
        samples = item.get("metrics", {}).get("styleSamples", {})
        for x in samples.get("pageTitles", []):
            fonts.add(x["fontFamily"]); title_sizes.add(x["fontSize"])
        for x in samples.get("buttons", []):
            fonts.add(x["fontFamily"]); button_heights.add(round(float(x["height"]), 2)); button_radii.add(x["borderRadius"])
        for x in samples.get("fields", []):
            fonts.add(x["fontFamily"]); field_heights.add(round(float(x["height"]), 2)); field_radii.add(x["borderRadius"])
        for x in samples.get("tableHeaders", []):
            table_header_sizes.add(x["fontSize"])
        for x in samples.get("cards", []):
            card_radii.add(x["borderRadius"])
    return {
        "font_families": sorted(fonts),
        "page_title_sizes": sorted(title_sizes),
        "button_heights": sorted(button_heights),
        "button_radii": sorted(button_radii),
        "field_heights": sorted(field_heights),
        "field_radii": sorted(field_radii),
        "table_header_font_sizes": sorted(table_header_sizes),
        "card_radii": sorted(card_radii),
    }


def run(args: argparse.Namespace) -> int:
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    scenarios: list[dict[str, Any]] = []
    discovered: set[str] = set()
    driver = build_driver()
    report: dict[str, Any] = {"mode": args.mode, "base_url": args.base_url, "failures": failures, "scenarios": scenarios}
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        if args.mode == "public":
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            scenarios.append(audit_scenario(driver, args.base_url, "#/crm/dashboard", "dashboard-hard-cache-bypass", 1440, outdir, failures, cache_bust=str(int(time.time()))))
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": False})
            scenarios.append(audit_scenario(driver, args.base_url, "#/crm/dashboard", "dashboard-normal-cache", 1440, outdir, failures))

        seen_pairs: set[tuple[str, int]] = set()
        for width in BREAKPOINTS:
            for name, route in TEMPLATE_MATRIX.items():
                key = (route, width)
                if key in seen_pairs:
                    continue
                item = audit_scenario(driver, args.base_url, route, name, width, outdir, failures)
                scenarios.append(item); seen_pairs.add(key); discovered.update(item["metrics"].get("internalLinks", []))

        for name, route in CANONICAL_ROUTES.items():
            for width in (1440, 390):
                key = (route, width)
                if key in seen_pairs:
                    continue
                item = audit_scenario(driver, args.base_url, route, name, width, outdir, failures)
                scenarios.append(item); seen_pairs.add(key); discovered.update(item["metrics"].get("internalLinks", []))

        # Crawl every additional internal route surfaced by the rendered product.
        known_routes = set(CANONICAL_ROUTES.values()) | {v[0] for v in COMPATIBILITY_ROUTES.values()}
        extra_links = sorted(x for x in discovered if x.startswith("#/crm/") and x not in known_routes)
        for index, route in enumerate(extra_links):
            for width in (1440, 390):
                key = (route, width)
                if key in seen_pairs:
                    continue
                item = audit_scenario(driver, args.base_url, route, f"discovered-{index+1}", width, outdir, failures)
                scenarios.append(item); seen_pairs.add(key)

        report["details"] = check_details(driver, args.base_url, outdir, failures)
        report["account_menu_768"] = check_account_menu(driver, args.base_url, failures)
        report["drawer_390"] = check_drawer(driver, args.base_url, outdir, failures)
        report["compatibility"] = check_compatibility(driver, args.base_url, failures)
        report["keyboard_focus"] = check_keyboard_focus(driver, args.base_url, failures)
        report["modals_390"] = attempt_modal_audit(driver, args.base_url, outdir, failures)
        report["discovered_internal_routes"] = extra_links
        report["design_system"] = summarize_design_system(scenarios)
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
    print(json.dumps({
        "status": report["status"], "mode": args.mode, "scenario_count": len(scenarios),
        "discovered_routes": report.get("discovered_internal_routes", []), "failures": failures,
        "design_system": report.get("design_system", {}),
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Certificação visual e estrutural integral do frontend Valtren.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["artifact", "public"], required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
