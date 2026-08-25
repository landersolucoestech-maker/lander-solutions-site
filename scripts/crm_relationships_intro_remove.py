from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CACHE_VERSION = "20260824-crm-no-intro-v1"


def apply_crm_relationships_intro_remove() -> int:
    app = APP.read_text(encoding="utf-8")

    pattern = re.compile(
        r'''\n\s*<div class="crm-rel-module-header">\s*<div>\s*<span>CRM relacionamentos</span>\s*<h2>\$\{title\}</h2>\s*<p>\$\{description\}</p>\s*</div>\s*</div>\s*''',
        re.S,
    )
    app, count = pattern.subn("\n", app, count=1)
    if count != 1:
        raise RuntimeError(f"Bloco introdutório do CRM não encontrado: {count}")

    app = re.sub(r"\n\s*const title = isContacts \? 'Contatos estratégicos' : 'Leads';", "", app, count=1)
    app = re.sub(
        r"\n\s*const description = isContacts\s*\? 'Clientes, parceiros, fornecedores, prestadores e contatos operacionais em uma lista central\.'\s*:\s*'Leads comerciais organizados em uma lista central para acompanhamento e evolução\.';",
        "",
        app,
        count=1,
        flags=re.S,
    )

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"app\.js(?:\?v=[A-Za-z0-9._-]+)?",
            f"app.js?v={CACHE_VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Bloco introdutório das abas Contatos e Leads removido.")
    return 1


if __name__ == "__main__":
    apply_crm_relationships_intro_remove()
