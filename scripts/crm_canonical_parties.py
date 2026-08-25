from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CORE_JS = ROOT / "scripts" / "crm_canonical_parties_core.js"
ADAPTER_JS = ROOT / "scripts" / "crm_canonical_parties_adapter.js"
CACHE_VERSION = "20260825-crm-canonical-parties-v1"
START = "  // VALTREN CANONICAL PARTIES START\n"
END = "  // VALTREN CANONICAL PARTIES END\n"


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 alvo, encontrado {count}")
    return text.replace(old, new, 1)


def apply_crm_canonical_parties() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    if not CORE_JS.exists():
        raise FileNotFoundError(CORE_JS)
    if not ADAPTER_JS.exists():
        raise FileNotFoundError(ADAPTER_JS)

    app = APP.read_text(encoding="utf-8")
    party_js = CORE_JS.read_text(encoding="utf-8").strip() + "\n\n" + ADAPTER_JS.read_text(encoding="utf-8").strip()

    app = re.sub(
        r"\n?  // VALTREN CANONICAL PARTIES START\n.*?  // VALTREN CANONICAL PARTIES END\n",
        "\n",
        app,
        flags=re.S,
    )

    anchor = "  function crmRelEnsureState(){"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Âncora crmRelEnsureState inválida: {app.count(anchor)} ocorrência(s)")
    injected = START + party_js + "\n" + END + "\n" + anchor
    app = app.replace(anchor, injected, 1)

    ensure_match = re.search(r"  function crmRelEnsureState\(\)\{.*?\n  \}\n\n  function crmRelSidebar", app, flags=re.S)
    if not ensure_match:
        raise RuntimeError("Função crmRelEnsureState não localizada após injeção")
    ensure_src = ensure_match.group(0)
    if "crmCanonicalEnsureFromLegacy();" not in ensure_src:
        ensure_new = ensure_src.replace("\n  }\n\n  function crmRelSidebar", "\n    crmCanonicalEnsureFromLegacy();\n  }\n\n  function crmRelSidebar", 1)
        app = app[: ensure_match.start()] + ensure_new + app[ensure_match.end() :]

    app = _replace_once(
        app,
        "      const index = state.crmRelContacts.findIndex((row) => row.id === id);\n      if (mode === 'edit' && index >= 0) state.crmRelContacts[index] = {...state.crmRelContacts[index],...item}; else state.crmRelContacts.unshift(item);",
        "      if(!crmCanonicalUpsertLegacyRecord('contacts',item,mode)) return;",
        "Persistência de contatos CRM",
    )
    app = _replace_once(
        app,
        "      const index = state.crmRelLeads.findIndex((row) => row.id === id);\n      if (mode === 'edit' && index >= 0) state.crmRelLeads[index] = {...state.crmRelLeads[index],...item}; else state.crmRelLeads.unshift(item);",
        "      if(!crmCanonicalUpsertLegacyRecord('leads',item,mode)) return;",
        "Persistência de leads CRM",
    )

    app = _replace_once(
        app,
        "          if (kind === 'contacts') state.crmRelContacts = state.crmRelContacts.filter((row) => row.id !== id); else state.crmRelLeads = state.crmRelLeads.filter((row) => row.id !== id);",
        "          crmCanonicalRemoveLegacyRecord(kind,id);",
        "Exclusão unitária CRM",
    )
    app = _replace_once(
        app,
        "          if (kind === 'contacts') state.crmRelContacts = state.crmRelContacts.filter((row) => !ids.includes(row.id)); else state.crmRelLeads = state.crmRelLeads.filter((row) => !ids.includes(row.id));",
        "          crmCanonicalRemoveLegacyRecords(kind,ids);",
        "Exclusão em massa CRM",
    )

    required = [
        "function crmCanonicalPartyService()",
        "crmCanonicalEnsureFromLegacy();",
        "crmCanonicalUpsertLegacyRecord('contacts',item,mode)",
        "crmCanonicalUpsertLegacyRecord('leads',item,mode)",
        "crmCanonicalRemoveLegacyRecord(kind,id)",
        "crmCanonicalRemoveLegacyRecords(kind,ids)",
        "state.crmCanonicalParties",
        "canonicalEntityId",
    ]
    missing = [item for item in required if item not in app]
    if missing:
        raise RuntimeError(f"Infraestrutura canônica incompleta no bundle: {missing}")

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Infraestrutura canônica de Pessoas e Organizações aplicada; CRM legado adaptado sem alterar layout ou navegação.")
    return 1


if __name__ == "__main__":
    apply_crm_canonical_parties()
