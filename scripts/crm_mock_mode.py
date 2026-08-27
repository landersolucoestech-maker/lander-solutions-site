from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
MOCK = ROOT / "mockups"
START = "  // VALTREN MOCK MODE START\n"
END = "  // VALTREN MOCK MODE END\n"

PARTS = ["manifest.js","factories/ids.js","factories/dates.js","business.js","crm.js","agenda.js","finance.js","fiscal.js","allocations.js","contracts.js","participations.js","payouts.js","legal.js","compliance.js","intellectual-property.js","corporate.js","marketing.js","notifications.js","adapter.js","loader.js"]

MOCK_CSS = r'''
/* VALTREN MOCK MODE */
.crm-mock-mode-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:7px 24px;background:#FFF7D6;border-bottom:1px solid rgba(212,175,55,.55);color:#0B1D3A;font-size:12px;font-weight:700;letter-spacing:.01em;box-sizing:border-box}
.crm-mock-mode-bar button{min-height:32px;border:1px solid rgba(11,29,58,.18);border-radius:9px;background:#fff;color:#0B1D3A;padding:5px 10px;font:inherit;cursor:pointer}
.crm-mock-mode-bar button:focus-visible{outline:2px solid #D4AF37;outline-offset:2px}
@media(max-width:560px){.crm-mock-mode-bar{padding:6px 12px;align-items:flex-start;flex-direction:column}.crm-mock-mode-bar button{width:100%}}
'''

def _bundle() -> str:
    missing=[part for part in PARTS if not (MOCK/part).exists()]
    if missing: raise RuntimeError(f"Mock Mode incompleto: {missing}")
    return "\n\n".join((MOCK/part).read_text(encoding="utf-8").rstrip() for part in PARTS)+"\n"

def _check_js(source:str)->None:
    with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False) as handle:
        handle.write(source);path=Path(handle.name)
    try:
        result=subprocess.run(["node","--check",str(path)],capture_output=True,text=True)
        if result.returncode: raise RuntimeError((result.stderr or result.stdout).strip())
    finally: path.unlink(missing_ok=True)

def apply_crm_mock_mode()->int:
    app=APP.read_text(encoding="utf-8")
    app=re.sub(re.escape(START)+r".*?"+re.escape(END),"",app,flags=re.S)
    anchor="  window.addEventListener('hashchange', render);"
    if app.count(anchor)!=1: raise RuntimeError(f"Âncora única de bootstrap do Mock Mode divergente: {app.count(anchor)}")
    block=START+_bundle()+"  crmMockBootstrap();\n"+END
    app=app.replace(anchor,block+anchor,1);_check_js(app);APP.write_text(app,encoding="utf-8")
    css=CSS.read_text(encoding="utf-8")
    css=re.sub(r"\n?/\* VALTREN MOCK MODE \*/.*\Z","",css,flags=re.S)
    CSS.write_text(css.rstrip()+"\n\n"+MOCK_CSS.strip()+"\n",encoding="utf-8")
    source=APP.read_text(encoding="utf-8")
    required=["new URLSearchParams(location.search).get('mock')==='1'","valtren:mock:","crmMockBootstrap()","crmMockAssertReconciliation()","Resetar dados de demonstração"]
    missing=[token for token in required if token not in source]
    if missing: raise RuntimeError(f"Contrato do Mock Mode ausente no materializado: {missing}")
    print("Mock Mode materializado por hook único, fixtures isoladas em /mockups e namespace valtren:mock:*.")
    return 1

if __name__=="__main__": apply_crm_mock_mode()
