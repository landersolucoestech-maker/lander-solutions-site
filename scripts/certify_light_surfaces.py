#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROUTES = {
    "dashboard": "#/crm/dashboard",
    "crm": "#/crm/relationships",
    "agenda": "#/crm/agenda",
    "financeiro": "#/crm/financeiro",
    "contabilidade": "#/crm/financeiro/accounting",
    "notas-fiscais": "#/crm/financeiro/notas-fiscais",
    "rateios": "#/crm/financeiro/rateios",
    "participacoes": "#/crm/financeiro/participacoes",
    "repasses": "#/crm/financeiro/repasses",
    "contratos": "#/crm/juridico/contratos",
    "marketing": "#/crm/marketing",
    "negocios": "#/crm/negocios",
    "relatorios": "#/crm/relatorios",
    "configuracoes": "#/crm/configuracoes",
}
VIEWPORTS = [1440, 1280, 1024, 768, 390]
SCREENSHOT_ROUTES = {"dashboard", "financeiro", "contratos", "marketing", "configuracoes"}
DASHBOARD_SECTIONS = [
    "Formação do Resultado",
    "Performance por Unidade de Negócio",
    "Produtos x Serviços",
    "Evolução Financeira",
    "Participações e Repasses",
    "Estrutura de Custos e Despesas",
]


def normalize_url(base: str, route: str) -> str:
    return base.rstrip("/") + "/" + route


def driver_factory():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--force-device-scale-factor=1")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=opts)


def wait_ready(driver):
    WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, 15).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".crm-app-shell"))
    time.sleep(0.08)


def set_viewport(driver, width: int, height: int | None = None):
    h = height or (900 if width >= 768 else 844)
    driver.set_window_rect(width=width, height=h)
    time.sleep(0.03)


def scan_route(driver) -> dict:
    return driver.execute_script(r"""
      const parse=(value)=>{const m=(value||'').match(/rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)(?:[, /]+([0-9.]+))?\)/i);return m?{r:+m[1],g:+m[2],b:+m[3],a:m[4]==null?1:+m[4]}:null};
      const lum=c=>c?(.2126*c.r+.7152*c.g+.0722*c.b):255;
      const visible=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
      const style=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),bg=parse(s.backgroundColor),fg=parse(s.color);return {tag:e.tagName,className:String(e.className||''),id:e.id||'',text:(e.textContent||'').trim().slice(0,100),backgroundColor:s.backgroundColor,color:s.color,backgroundLuminance:lum(bg),foregroundLuminance:lum(fg),area:Math.round(r.width*r.height),rect:{x:r.x,y:r.y,width:r.width,height:r.height}}};
      const shell=e=>!!e.closest('.crm-sidebar,.crm-topbar');
      const overlay=e=>/overlay|backdrop/i.test(String(e.className||''));
      const accent=e=>/badge|status|icon|avatar|legend|indicator|today|event/i.test(String(e.className||''));
      const structural=e=>{const c=String(e.className||'').toLowerCase(),t=e.tagName;return ['SECTION','ARTICLE','HEADER','FOOTER','FORM','DIALOG','TABLE','THEAD','TH'].includes(t)||/(panel|card|modal|drawer|toolbar|tabs?|empty|ranking|summary|breakdown|bulk|popover|dropdown)/.test(c)};
      const dark=[];
      for(const e of document.querySelectorAll('.crm-app-shell *, body>[id^="crm-"] *')){
        if(!visible(e)||shell(e)||overlay(e))continue;
        const x=style(e),bg=parse(x.backgroundColor);
        if(!bg||bg.a<.8||x.backgroundLuminance>=85)continue;
        if(accent(e)&&x.area<=2200)continue;
        if(structural(e)||x.area>3200)dark.push(x);
      }
      const topbar=document.querySelector('.crm-topbar'),sidebar=document.querySelector('.crm-sidebar'),main=document.querySelector('.crm-main');
      return {route:location.hash,width:innerWidth,docWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,topbar:topbar?style(topbar):null,sidebar:sidebar?style(sidebar):null,main:main?style(main):null,darkSurfaces:dark.slice(0,50),darkCount:dark.length};
    """)


def dashboard_section_styles(driver) -> list[dict]:
    return driver.execute_script(r"""
      const wanted=arguments[0];
      const parse=v=>{const m=(v||'').match(/rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)/i);return m?{r:+m[1],g:+m[2],b:+m[3]}:null};
      const lum=c=>c?(.2126*c.r+.7152*c.g+.0722*c.b):255;
      return wanted.map(title=>{const h=[...document.querySelectorAll('.crm-dashboard-panel h3')].find(n=>(n.textContent||'').trim()===title);const panel=h?.closest('.crm-dashboard-panel'),head=panel?.querySelector(':scope>header');const ps=panel?getComputedStyle(panel):null,hs=head?getComputedStyle(head):null;return {title,found:!!panel,panelBackground:ps?.backgroundColor||null,panelLuminance:lum(parse(ps?.backgroundColor)),headerBackground:hs?.backgroundColor||null,headerLuminance:lum(parse(hs?.backgroundColor)),titleColor:h?getComputedStyle(h).color:null}});
    """, DASHBOARD_SECTIONS)


def open_contract_modal(driver, base_url: str, output: Path) -> dict:
    driver.get(normalize_url(base_url, ROUTES["contratos"]))
    wait_ready(driver)
    set_viewport(driver, 390, 844)
    candidates = driver.find_elements(By.XPATH, "//*[self::button or self::a][contains(normalize-space(.),'Novo Contrato')]")
    target = next((e for e in candidates if e.is_displayed()), None)
    if target is None:
        return {"opened": False, "error": "Novo Contrato control not found"}
    driver.execute_script("arguments[0].click()", target)
    try:
        WebDriverWait(driver, 8).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".crm-legal-modal"))
    except Exception:
        return {"opened": False, "error": "crm-legal-modal not rendered"}
    data = driver.execute_script(r"""
      const one=s=>document.querySelector(s),sty=e=>e?{backgroundColor:getComputedStyle(e).backgroundColor,color:getComputedStyle(e).color}:null;const modal=one('.crm-legal-modal'),head=modal?.querySelector('header'),foot=modal?.querySelector('footer');return {opened:!!modal,modal:sty(modal),header:sty(head),footer:sty(foot),docWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth};
    """)
    shot = output / "contracts-modal-390-light-surface.png"
    driver.save_screenshot(str(shot))
    data["screenshot"] = shot.name
    return data


def relevant_console(driver) -> list[dict]:
    out=[]
    for row in driver.get_log("browser"):
        msg=(row.get("message") or "").lower()
        if row.get("level") in {"SEVERE", "ERROR"} and not any(x in msg for x in ("favicon", "googleapis", "fonts.gstatic")):
            out.append(row)
    return out


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", default="manual")
    args=parser.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    failures=[]; route_results=[]; screenshots=[]
    dashboard=[]; modal={}
    driver=driver_factory()
    try:
        for name,route in ROUTES.items():
            for width in VIEWPORTS:
                set_viewport(driver,width)
                driver.get(normalize_url(args.base_url,route)); wait_ready(driver)
                data=scan_route(driver); route_results.append({"name":name,**data})
                if not data.get("topbar") or data["topbar"]["backgroundLuminance"]>=85:
                    failures.append(f"{name}@{width}: Header global não está dark")
                if not data.get("sidebar") or data["sidebar"]["backgroundLuminance"]>=85:
                    failures.append(f"{name}@{width}: Sidebar não está dark")
                if data.get("main") and data["main"]["backgroundLuminance"]<180:
                    failures.append(f"{name}@{width}: main content não está clara ({data['main']['backgroundColor']})")
                if data["docWidth"]>data["clientWidth"]+1:
                    failures.append(f"{name}@{width}: body horizontal overflow {data['docWidth']}>{data['clientWidth']}")
                if data["darkCount"]:
                    failures.append(f"{name}@{width}: DARK SURFACES OUTSIDE HEADER/SIDEBAR={data['darkCount']} {data['darkSurfaces'][:5]}")
                if name in SCREENSHOT_ROUTES and width in (1440,390):
                    filename=f"{name}-{width}-light-workspace.png"
                    driver.save_screenshot(str(out/filename)); screenshots.append(filename)
        set_viewport(driver,1440)
        driver.get(normalize_url(args.base_url,ROUTES["dashboard"])); wait_ready(driver)
        dashboard=dashboard_section_styles(driver)
        for item in dashboard:
            if not item["found"]:
                failures.append(f"Dashboard section missing: {item['title']}")
            elif item["panelLuminance"]<180 or item["headerLuminance"]<180:
                failures.append(f"Dashboard section dark: {item}")
        modal=open_contract_modal(driver,args.base_url,out)
        if not modal.get("opened"):
            failures.append(f"Contracts modal: {modal.get('error')}")
        else:
            for key in ("modal","header","footer"):
                bg=modal.get(key,{}).get("backgroundColor","")
                rgb=[int(x) for x in re.findall(r'\d+',bg)[:3]]
                if len(rgb)==3 and (.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2])<180:
                    failures.append(f"Contracts modal {key} dark: {bg}")
            if modal["docWidth"]>modal["clientWidth"]+1:
                failures.append("Contracts modal creates horizontal overflow")
        console=relevant_console(driver)
        if console: failures.append(f"Runtime console errors: {console[:5]}")
    finally:
        driver.quit()
    report={"status":"PASS" if not failures else "FAIL","mode":args.mode,"dark_surfaces_outside_header_sidebar":sum(r.get('darkCount',0) for r in route_results),"route_scenarios":len(route_results),"dashboard_sections":dashboard,"contract_modal":modal,"screenshots":screenshots,"failures":failures}
    (out/"light-surface-certification-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
