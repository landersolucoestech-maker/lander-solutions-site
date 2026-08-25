from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-reference-fidelity-v1"


def _parts(prefix: str) -> str:
    files = sorted(HERE.glob(prefix))
    if not files:
        raise RuntimeError(f"Partes ausentes: {prefix}")
    return "".join(path.read_text(encoding="utf-8") for path in files)


def _write_cache_version() -> None:
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")


def apply_crm_reference_fidelity_fix() -> int:
    app = APP.read_text(encoding="utf-8")
    js_block = _parts("crm_reference_fidelity_fix.js.part*")
    css_block = _parts("crm_reference_fidelity_fix.css.part*")

    app = re.sub(
        r"\n?  // VALTREN CRM REFERENCE FIDELITY FIX START\n.*?  // VALTREN CRM REFERENCE FIDELITY FIX END\n",
        "\n",
        app,
        flags=re.S,
    )

    # AI Criativa was explicitly removed from the final Marketing module.
    # The legacy URL remains only as an invisible redirect to Marketing.
    app = app.replace(",[\'ai\',\'IA Criativa\']", "")
    app = app.replace(',["ai","IA Criativa"]', "")
    app = app.replace('<a href="#/crm/marketing/ai">IA Criativa</a>', '')
    app = re.sub(r"\n  function crmRefAIPage\(\)\{[^\n]*\}\n", "\n", app)
    app = app.replace("IA Criativa e análise avançada", "Análise avançada")

    # The visible support module is ValtrenChat. Remove the old generic page and
    # the unrelated New Conversation action that is not rendered by the source page.
    app = re.sub(r"\n  function crmRefMusicChatPage\(\)\{[^\n]*\}\n", "\n", app)
    app = re.sub(r"\n  function crmRefConversationModal\(\)\{[^\n]*\}\n", "\n", app)

    app = app.replace(
        "path === '/crm/musicchat' || path === '/crm/relatorios'",
        "(path === '/crm/musicchat' || path === '/crm/valtrenchat') || path === '/crm/relatorios'",
    )

    anchor = "  function contactPage(query)"
    if anchor not in app:
        raise RuntimeError("Âncora contactPage ausente para aplicar fidelidade dos módulos")
    app = app.replace(anchor, js_block.rstrip() + "\n\n" + anchor, 1)

    # Reports is backend-driven and the attached ImportDialog accepts XLSX only.
    app = app.replace("Arraste ou clique para escolher XLSX/CSV", "XLSX")
    app = app.replace('accept=".xlsx,.csv"', 'accept=".xlsx"')
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM REFERENCE FIDELITY FIX \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + css_block.strip() + "\n", encoding="utf-8")
    _write_cache_version()
    print("Fidelidade dos módulos anexados aplicada; IA Criativa removida e ValtrenChat ativado.")
    return 1


if __name__ == "__main__":
    apply_crm_reference_fidelity_fix()
