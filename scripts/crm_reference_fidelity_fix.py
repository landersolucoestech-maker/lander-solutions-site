from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-reference-fidelity-v2"


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

    # Normalize the published fidelity source before it is injected into app.js.
    # Financeiro remains the parent menu; the first child is named Transações.
    js_block = js_block.replace("[['finance','Financeiro']", "[['finance','Transações']")

    # Regras de Categorização: Transações must appear immediately to the left of Nova Regra.
    rules_old = "const actions=`<button class=\"primary\" data-action=\"crm-ref-open\" data-kind=\"categorization-rule\">${crmRefIcon('plus')} Nova Regra</button>`;"
    rules_new = "const actions=`<a class=\"secondary crm-ref-transactions-button\" href=\"#/crm/financeiro\">${crmRefIcon('database')} Transações</a><button class=\"primary\" data-action=\"crm-ref-open\" data-kind=\"categorization-rule\">${crmRefIcon('plus')} Nova Regra</button>`;"
    js_block = js_block.replace(rules_old, rules_new)

    # Categorias Financeiras: replace the old back button with a Transactions button,
    # including a left-side icon so it follows the same visual pattern as Criar.
    categories_old = '<a class="secondary" href="#/crm/financeiro">← Voltar ao Financeiro</a><button class="primary" data-action="crm-ref-open" data-kind="category">${crmRefIcon(\'plus\')} Criar</button>'
    categories_new = '<a class="secondary crm-ref-transactions-button" href="#/crm/financeiro">${crmRefIcon(\'database\')} Transações</a><button class="primary" data-action="crm-ref-open" data-kind="category">${crmRefIcon(\'plus\')} Criar</button>'
    js_block = js_block.replace(categories_old, categories_new)

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
    print("Fidelidade dos módulos aplicada com botões financeiros normalizados.")
    return 1


if __name__ == "__main__":
    apply_crm_reference_fidelity_fix()
