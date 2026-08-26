from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
INDEX = ROOT / "index.html"
ANCHOR = "  // VALTREN BUSINESS CATALOG START\n"
FINAL_CACHE_VERSION = "20260826-legal-complete-v1"

LEGAL_SIDEBAR_REQUIRED = [
    "Assuntos Jurídicos", "Contratos", "Templates", "Variáveis",
    "Compliance e Políticas", "Propriedade Intelectual", "Societário",
]
LEGAL_SIDEBAR_FORBIDDEN_LINK_LABELS = [
    "Processos", "Litígios", "Marcas", "Patentes", "Sócios", "Atos", "Políticas", "Obrigações",
]
PREVIOUS_OWNER_HANDLERS = [
    "if(path==='/crm/financeiro')return crmTransactionsPage();",
    "if(path==='/crm/financeiro/accounting')return crmAccountingPage();",
    "if(path==='/crm/financeiro/notas-fiscais')return crmFiscalDocumentsPage();",
    "if(path==='/crm/financeiro/participacoes')return crmEconomicParticipationsPage();",
    "if(path==='/crm/financeiro/repasses')return crmPayoutsPage();",
    "if(path==='/crm/juridico/contratos')return crmLegalContractsPage();",
    "if(path==='/crm/juridico/contratos/templates')return crmLegalTemplatesPage();",
    "if(path==='/crm/juridico/contratos/variaveis')return crmLegalVariablesPage();",
    "if(path==='/crm/negocios')return crmBusinessProductsPage();",
    "if(path==='/crm/negocios/servicos')return crmBusinessServicesPage();",
    "if(path==='/crm/negocios/unidades')return crmBusinessUnitsPage();",
]

def replace_marked_block(text: str, start: str, end: str, body: str, anchor: str = ANCHOR) -> str:
    block = start + body.rstrip() + "\n" + end
    start_count, end_count = text.count(start), text.count(end)
    if start_count == 1 and end_count == 1:
        a = text.index(start)
        b = text.index(end, a) + len(end)
        current = text[a:b]
        if current == block:
            return text
        return text[:a] + block + text[b:]
    if start_count or end_count:
        raise RuntimeError(f"Marcadores divergentes: {start.strip()} ({start_count}/{end_count})")
    if text.count(anchor) != 1:
        raise RuntimeError(f"Âncora de materialização inválida: {text.count(anchor)} ocorrência(s)")
    at = text.index(anchor)
    return text[:at].rstrip("\n") + "\n\n" + block + "\n" + text[at:]

def replace_route(app: str, old: str, new: str, label: str) -> str:
    old_count, new_count = app.count(old), app.count(new)
    if old_count == 1 and new_count == 0:
        return app.replace(old, new, 1)
    if old_count == 0 and new_count == 1:
        return app
    raise RuntimeError(f"Rota {label} ambígua: placeholder={old_count}, handler={new_count}")

def replace_css(css: str, marker: str, body: str) -> str:
    start = f"/* {marker} */"
    pattern = rf"{re.escape(start)}.*?(?=\n/\*|\Z)"
    matches = list(re.finditer(pattern, css, flags=re.S))
    block = body.strip()
    if len(matches) == 1:
        current = matches[0].group(0)
        if current.strip() == block:
            return css
        return css[:matches[0].start()] + block + css[matches[0].end():]
    if len(matches) > 1:
        raise RuntimeError(f"CSS {marker} duplicado: {len(matches)}")
    return css.rstrip() + "\n" + block

def validate_legal_sidebar(app: str) -> None:
    start_marker = "// VALTREN SIDEBAR ARCHITECTURE START"
    end_marker = "// VALTREN SIDEBAR ARCHITECTURE END"
    sidebar_start = app.find(start_marker)
    sidebar_end = app.find(end_marker, sidebar_start + len(start_marker)) if sidebar_start >= 0 else -1
    if sidebar_start < 0 or sidebar_end <= sidebar_start:
        raise RuntimeError("Markers canônicos da Sidebar não localizados")
    sidebar = app[sidebar_start:sidebar_end]
    missing = [x for x in LEGAL_SIDEBAR_REQUIRED if x not in sidebar]
    if missing:
        raise RuntimeError(f"Sidebar Jurídico incompleto: {missing}")
    for label in LEGAL_SIDEBAR_FORBIDDEN_LINK_LABELS:
        if re.search(rf">\s*{re.escape(label)}\s*</a>", sidebar):
            raise RuntimeError(f"Subitem jurídico indevido no sidebar: {label}")

def validate_previous_owners(app: str) -> None:
    missing = [x for x in PREVIOUS_OWNER_HANDLERS if x not in app]
    if missing:
        raise RuntimeError(f"Owner canônico anterior sofreu regressão: {missing}")
    if "state.crmCanonicalParties" not in app or "ValtrenPartyCore" not in app:
        raise RuntimeError("Infraestrutura canônica de Pessoas/Organizações ausente")
    if "state.crmBusinessCatalog" not in app or "ValtrenBusinessCore" not in app:
        raise RuntimeError("Catálogo canônico de Negócios ausente")

def update_cache_version() -> None:
    if not INDEX.exists():
        raise FileNotFoundError(INDEX)
    if CSS.exists() and "/* VALTREN PRODUCT SYSTEM REVIEW */" in CSS.read_text(encoding="utf-8"):
        return
    html = INDEX.read_text(encoding="utf-8")
    html, count = re.subn(r"assets/valtren-brand\.css\?v=[^\"']+", f"assets/valtren-brand.css?v={FINAL_CACHE_VERSION}", html)
    if count != 1:
        raise RuntimeError(f"Link CSS Valtren divergente no index: {count}")
    INDEX.write_text(html, encoding="utf-8")
