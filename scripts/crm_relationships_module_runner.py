from __future__ import annotations

import re
from pathlib import Path

import crm_relationships_module as legacy

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"


def _materialize_relationship_route(app: str) -> str:
    canonical = "    else if (path === '/crm/relationships') app.innerHTML = crmRelationshipsPage(query);"
    if canonical in app or "path==='/crm/relationships'" in app or "path === '/crm/relationships'" in app:
        return app

    lines = app.splitlines(keepends=True)
    route_indexes = [
        index for index, line in enumerate(lines)
        if "/crm/dashboard" in line and "crmDashboardPage(" in line and "path" in line
    ]
    if not route_indexes:
        raise RuntimeError("Rota do Dashboard não localizada para registrar CRM Relacionamentos")

    offset = 0
    for index in route_indexes:
        at = index + 1 + offset
        dashboard_line = lines[index + offset]
        indent = re.match(r"^\s*", dashboard_line).group(0)
        if "return crmDashboardPage" in dashboard_line:
            route = f"{indent}if(path==='/crm/relationships')return crmRelationshipsPage(query);\n"
        else:
            route = f"{indent}else if (path === '/crm/relationships') app.innerHTML = crmRelationshipsPage(query);\n"
        lines.insert(at, route)
        offset += 1
    return "".join(lines)


def apply_crm_relationships() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CSS.exists():
        raise FileNotFoundError(CSS)

    app = APP.read_text(encoding="utf-8")

    # Navegação não pertence ao módulo Relacionamentos. O owner exclusivo da
    # sidebar é crm_sidebar_architecture.py e será materializado posteriormente.
    if "function crmRelationshipsPage(query)" not in app:
        anchor = "  function contactPage(query)"
        if app.count(anchor) != 1:
            raise RuntimeError(f"Âncora para o módulo CRM divergente: {app.count(anchor)}")
        app = app.replace(anchor, legacy.JS_BLOCK + "\n" + anchor, 1)

    app = _materialize_relationship_route(app)
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM RELATIONSHIPS \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + legacy.CSS_BLOCK.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={legacy.CSS_VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Módulo CRM Relacionamentos aplicado sem assumir ownership da Sidebar ou depender do conteúdo do Dashboard.")
    return 1


if __name__ == "__main__":
    apply_crm_relationships()
