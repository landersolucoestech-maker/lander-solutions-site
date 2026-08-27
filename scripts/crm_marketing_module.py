from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
JS = ROOT / "scripts" / "crm_marketing_module.js"
MODULE_CSS = ROOT / "scripts" / "crm_marketing_module.css"
START = "  // VALTREN MARKETING MODULE START\n"
END = "  // VALTREN MARKETING MODULE END\n"


def apply_crm_marketing_module() -> int:
    for path in (APP, CSS, JS, MODULE_CSS):
        if not path.exists():
            raise FileNotFoundError(path)
    app = APP.read_text(encoding="utf-8")
    app = re.sub(r"\n?  // VALTREN MARKETING MODULE START\n.*?  // VALTREN MARKETING MODULE END\n", "\n", app, flags=re.S)
    # Stable boundary after Business: unlike contactPage, this anchor is not reused by
    # earlier domain materializers, so rerunning Business cannot reorder Marketing.
    anchor = "  // VALTREN LEGAL MATTERS START\n"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora inválida para Marketing: {app.count(anchor)}")
    block = START + JS.read_text(encoding="utf-8").strip() + "\n" + END
    app = app.replace(anchor, block + "\n" + anchor, 1)
    old = "if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();"
    new = "if(path.startsWith('/crm/marketing'))return crmMarketingPage(path);"
    if app.count(old) == 1 and app.count(new) == 0:
        app = app.replace(old, new, 1)
    elif app.count(old) != 0 or app.count(new) != 1:
        raise RuntimeError(f"Rota de Marketing ambígua: indisponível={app.count(old)}, canônica={app.count(new)}")
    APP.write_text(app, encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN MARKETING MODULE \*/.*?(?=\n/\*|\Z)", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + MODULE_CSS.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
    print("Marketing materializado com Visão Geral, Campanhas, Calendário, Métricas, Briefings e Tarefas, sem métricas ou integrações simuladas.")
    return 1


if __name__ == "__main__":
    apply_crm_marketing_module()
