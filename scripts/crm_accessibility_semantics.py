from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_START = "/* VALTREN ACCESSIBILITY SEMANTICS START */"
CSS_END = "/* VALTREN ACCESSIBILITY SEMANTICS END */"

STATIC_LABELS = {
    "crm-rel-search": "Pesquisar relacionamentos",
    "crm-rel-select-all": "Selecionar todos os registros",
    "crm-agenda-search": "Pesquisar eventos",
    "crm-full-search": "Pesquisar contatos, empresas e leads",
    "crm-fin-search": "Pesquisar transações",
    "crm-fin-from": "Data inicial",
    "crm-fin-to": "Data final",
    "crm-fin-period": "Período",
    "crm-fin-type": "Tipo de transação",
    "crm-fin-dimension": "Produto ou sistema",
    "crm-fin-account-filter": "Conta financeira",
    "crm-fin-category": "Categoria financeira",
    "crm-fin-recon": "Status de conciliação",
    "crm-fin-bulk-category": "Categoria financeira em massa",
    "crm-fin-bulk-business": "Produto ou sistema em massa",
    "crm-fin-bulk-counterparty": "Origem ou destino em massa",
    "crm-acct-from": "Data inicial",
    "crm-acct-to": "Data final",
    "crm-acct-period": "Período contábil",
    "crm-acct-dimension": "Produto ou sistema",
    "crm-acct-service": "Serviço",
    "crm-acct-unit": "Unidade de negócio",
    "crm-acct-category": "Categoria financeira",
    "crm-acct-classification": "Classificação contábil",
    "crm-fiscal-search": "Pesquisar notas fiscais",
    "crm-fiscal-status": "Status fiscal",
    "crm-fiscal-financial": "Status financeiro",
    "crm-fiscal-party": "Cliente ou fornecedor",
    "crm-fiscal-product": "Produto",
    "crm-fiscal-service": "Serviço",
    "crm-fiscal-unit": "Unidade de negócio",
    "crm-fiscal-linked": "Vínculo financeiro",
    "crm-alloc-search": "Pesquisar rateios",
    "crm-alloc-from": "Data inicial",
    "crm-alloc-to": "Data final",
    "crm-alloc-period": "Período",
    "crm-alloc-method": "Método de rateio",
    "crm-alloc-account": "Conta financeira",
    "crm-alloc-category": "Categoria financeira",
    "crm-alloc-product": "Produto",
    "crm-alloc-service": "Serviço",
    "crm-alloc-unit": "Unidade de negócio",
    "crm-alloc-responsible": "Responsável",
    "crm-legal-search": "Pesquisar contratos",
    "crm-legal-responsible": "Responsável",
    "crm-legal-type": "Tipo de contrato",
    "crm-legal-status": "Status do contrato",
    "crm-legal-party": "Parte contratual",
    "crm-legal-category": "Categoria do contrato",
    "crm-legal-customer": "Cliente",
    "crm-legal-product": "Produto",
    "crm-legal-service": "Serviço",
    "crm-legal-unit": "Unidade de negócio",
    "crm-legal-template-search": "Pesquisar templates",
    "crm-legal-template-category": "Categoria do template",
    "crm-legal-template-type": "Tipo de template",
    "crm-legal-template-status": "Status do template",
    "crm-legal-variable-search": "Pesquisar variáveis",
    "crm-legal-variable-scope": "Escopo da variável",
    "crm-legal-variable-status": "Status da variável",
    "crm-part-search": "Pesquisar participações econômicas",
    "crm-part-calc-from": "Data inicial do cálculo",
    "crm-part-calc-to": "Data final do cálculo",
    "crm-part-period": "Período",
    "crm-part-contract": "Contrato",
    "crm-part-participant": "Participante econômico",
    "crm-part-status": "Status da participação",
    "crm-part-consistency": "Consistência",
    "crm-part-product": "Produto",
    "crm-part-service": "Serviço",
    "crm-part-unit": "Unidade de negócio",
    "crm-part-basis": "Base de cálculo",
    "crm-part-rule": "Regra econômica",
    "crm-part-calc-contract": "Contrato para cálculo",
    "crm-payout-search": "Pesquisar repasses",
    "crm-payout-period": "Período",
    "crm-payout-participant": "Participante econômico",
    "crm-payout-status": "Status do repasse",
    "crm-payout-product": "Produto",
    "crm-payout-contract": "Contrato",
    "crm-payout-service": "Serviço",
    "crm-payout-unit": "Unidade de negócio",
    "crm-payout-due": "Vencimento",
    "crm-payout-recon": "Status de conciliação",
    "crm-matter-search": "Pesquisar assuntos jurídicos",
    "crm-matter-responsible": "Responsável",
    "crm-matter-type": "Tipo de assunto jurídico",
    "crm-matter-status": "Status do assunto jurídico",
    "crm-matter-risk": "Risco jurídico",
    "crm-matter-priority": "Prioridade",
    "crm-matter-product": "Produto",
    "crm-matter-service": "Serviço",
    "crm-matter-unit": "Unidade de negócio",
    "crm-compliance-search": "Pesquisar compliance e políticas",
    "crm-compliance-responsible": "Responsável",
    "crm-compliance-category": "Categoria",
    "crm-compliance-status": "Status de compliance",
    "crm-compliance-risk": "Risco",
    "crm-compliance-type": "Tipo",
    "crm-ip-search": "Pesquisar propriedade intelectual",
    "crm-ip-responsible": "Responsável",
    "crm-ip-type": "Tipo de ativo de propriedade intelectual",
    "crm-ip-status": "Status do ativo",
    "crm-ip-owner": "Titular",
    "crm-corporate-date": "Data societária",
    "crm-corporate-entity": "Entidade societária",
    "crm-business-product-search": "Pesquisar produtos",
    "crm-business-product-owner": "Responsável pelo produto",
    "crm-business-product-status": "Status do produto",
    "crm-business-product-category": "Categoria do produto",
    "crm-business-product-unit": "Unidade de negócio do produto",
    "crm-business-service-search": "Pesquisar serviços",
    "crm-business-service-owner": "Responsável pelo serviço",
    "crm-business-service-status": "Status do serviço",
    "crm-business-service-category": "Categoria do serviço",
    "crm-business-service-unit": "Unidade de negócio do serviço",
    "crm-business-unit-search": "Pesquisar unidades de negócio",
    "crm-business-unit-owner": "Responsável pela unidade de negócio",
    "crm-business-unit-status": "Status da unidade de negócio",
}

ACTION_LABELS = {
    "crm-acct-recognition": "Data de reconhecimento contábil",
    "crm-acct-classification-override": "Classificação contábil",
    "crm-acct-service-meta": "Serviço contábil",
    "crm-acct-unit-meta": "Unidade de negócio contábil",
    "crm-acct-mapping": "Mapeamento contábil",
}

OWNER_STATIC_LABELS = {
    "business": {key: STATIC_LABELS[key] for key in (
        "crm-business-product-search", "crm-business-product-owner", "crm-business-product-status",
        "crm-business-product-category", "crm-business-product-unit", "crm-business-service-search",
        "crm-business-service-owner", "crm-business-service-status", "crm-business-service-category",
        "crm-business-service-unit", "crm-business-unit-search", "crm-business-unit-owner",
        "crm-business-unit-status",
    )},
    "legal_matters": {key: STATIC_LABELS[key] for key in (
        "crm-matter-search", "crm-matter-responsible", "crm-matter-type", "crm-matter-status",
        "crm-matter-risk", "crm-matter-priority", "crm-matter-product", "crm-matter-service",
        "crm-matter-unit",
    )},
    "compliance": {key: STATIC_LABELS[key] for key in (
        "crm-compliance-search", "crm-compliance-responsible", "crm-compliance-category",
        "crm-compliance-status", "crm-compliance-risk", "crm-compliance-type",
    )},
    "intellectual_property": {key: STATIC_LABELS[key] for key in (
        "crm-ip-search", "crm-ip-responsible", "crm-ip-type", "crm-ip-status", "crm-ip-owner",
    )},
    "corporate_governance": {key: STATIC_LABELS[key] for key in (
        "crm-corporate-date", "crm-corporate-entity",
    )},
}

OWNED_STATIC_IDS = frozenset(
    control_id
    for owner_labels in OWNER_STATIC_LABELS.values()
    for control_id in owner_labels
)
GLOBAL_STATIC_LABELS = {
    control_id: label
    for control_id, label in STATIC_LABELS.items()
    if control_id not in OWNED_STATIC_IDS
}

if len(OWNED_STATIC_IDS) != sum(len(labels) for labels in OWNER_STATIC_LABELS.values()):
    raise RuntimeError("Accessible-name owner allowlists possuem IDs duplicados")
if len(GLOBAL_STATIC_LABELS) + len(OWNED_STATIC_IDS) != len(STATIC_LABELS):
    raise RuntimeError("Accessible-name owner partition não cobre a política estática integral")

RULE_FILTER_SOURCE = """<label class="crm-ref-search">${icon('search',14)}<input placeholder="Buscar por palavra-chave ou categoria"></label><select><option>Todos os tipos</option><option>Receita</option><option>Despesa</option></select><select><option>Todas as origens</option><option>Sistema</option><option>Personalizada</option></select><select><option>Todos</option><option>Ativas</option><option>Inativas</option></select>"""
RULE_FILTER_ACCESSIBLE = """<label class="crm-ref-search">${icon('search',14)}<input aria-label="Pesquisar regras de categorização" placeholder="Buscar por palavra-chave ou categoria"></label><select aria-label="Tipo de transação"><option>Todos os tipos</option><option>Receita</option><option>Despesa</option></select><select aria-label="Origem da regra"><option>Todas as origens</option><option>Sistema</option><option>Personalizada</option></select><select aria-label="Status da regra"><option>Todos</option><option>Ativas</option><option>Inativas</option></select>"""

PAGINATION_REPLACEMENTS = {
    """data-action="crm-fin-page" data-page="${filters.page-1}" ${filters.page<=1?'disabled':''}>‹</button>""":
        """data-action="crm-fin-page" data-page="${filters.page-1}" aria-label="Página anterior" ${filters.page<=1?'disabled':''}>‹</button>""",
    """data-action="crm-fin-page" data-page="${filters.page+1}" ${filters.page>=pages?'disabled':''}>›</button>""":
        """data-action="crm-fin-page" data-page="${filters.page+1}" aria-label="Próxima página" ${filters.page>=pages?'disabled':''}>›</button>""",
    """data-action="crm-payout-page" data-page="${prev}" ${result.page===1?'disabled':''}>‹</button>""":
        """data-action="crm-payout-page" data-page="${prev}" aria-label="Página anterior" ${result.page===1?'disabled':''}>‹</button>""",
    """data-action="crm-payout-page" data-page="${next}" ${result.page===result.pages?'disabled':''}>›</button>""":
        """data-action="crm-payout-page" data-page="${next}" aria-label="Próxima página" ${result.page===result.pages?'disabled':''}>›</button>""",
}

CSS_PATCH = f"""
{CSS_START}
@media(max-width:760px){{
  .crm-full-breadcrumb a,.crm-architecture-breadcrumb a{{
    display:inline-flex;align-items:center;justify-content:center;min-width:30px;min-height:30px;
    padding:8px 4px;box-sizing:border-box;
  }}
  .crm-rel-pagination button,.crm-fin-pagination button,.crm-fiscal-pagination button,
  .crm-alloc-pagination button,.crm-legal-pagination button,.crm-part-pagination button,
  .crm-payout-pagination button,.crm-legal-matter-pagination button,.crm-compliance-pagination button,
  .crm-ip-pagination button,.crm-business-pagination button{{
    min-width:30px;min-height:30px;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;
  }}
}}
{CSS_END}
""".strip()


def _visible_wrapping_label(source: str, control_start: int) -> bool:
    before = source[:control_start]
    label_open = before.rfind("<label")
    label_close = before.rfind("</label>")
    if label_open < 0 or label_close > label_open:
        return False
    open_end = source.find(">", label_open, control_start)
    if open_end < 0:
        return False
    prefix = source[open_end + 1:control_start]
    prefix = re.sub(r"\$\{.*?\}", "", prefix, flags=re.S)
    prefix = re.sub(r"<[^>]+>", "", prefix)
    return bool(html.unescape(prefix).strip())


def _tag_matches(source: str, control_id: str) -> list[re.Match[str]]:
    pattern = re.compile(rf'<(?:input|select|textarea)\b(?=[^>]*\bid="{re.escape(control_id)}")[^>]*>', re.I)
    return list(pattern.finditer(source))


def has_accessible_name_for_id(source: str, control_id: str, expected_label: str) -> bool:
    matches = _tag_matches(source, control_id)
    if len(matches) != 1:
        return False
    match = matches[0]
    tag = match.group(0)
    aria = re.search(r'\baria-label="([^"]+)"', tag, re.I)
    if aria:
        return aria.group(1) == expected_label
    if re.search(r'\baria-labelledby="[^"]+"', tag, re.I):
        return True
    if re.search(r'\btitle="[^"]+"', tag, re.I):
        return True
    return _visible_wrapping_label(source, match.start())


def _inject_attr_by_id(source: str, control_id: str, label: str) -> str:
    matches = _tag_matches(source, control_id)
    if len(matches) != 1:
        raise RuntimeError(f"Controle {control_id} divergente: {len(matches)} ocorrência(s)")
    match = matches[0]
    tag = match.group(0)
    aria = re.search(r'\baria-label="([^"]+)"', tag, re.I)
    if aria:
        if aria.group(1) != label:
            raise RuntimeError(f"Controle {control_id} possui aria-label conflitante: {aria.group(1)!r}")
        return source
    if re.search(r'\baria-labelledby="[^"]+"', tag, re.I) or re.search(r'\btitle="[^"]+"', tag, re.I):
        return source
    if _visible_wrapping_label(source, match.start()):
        return source
    replacement = tag[:-1] + f' aria-label="{html.escape(label, quote=True)}">'
    return source[:match.start()] + replacement + source[match.end():]


def apply_accessible_names(source: str, labels: dict[str, str]) -> str:
    result = source
    for control_id, label in labels.items():
        result = _inject_attr_by_id(result, control_id, label)
    return result


def _inject_attr_by_action(source: str, action: str, label: str) -> str:
    pattern = re.compile(rf'<(?:input|select|textarea)\b(?=[^>]*\bdata-action="{re.escape(action)}")[^>]*>', re.I)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"Controle dinâmico {action} divergente: {len(matches)} ocorrência(s)")
    match = matches[0]
    tag = match.group(0)
    if re.search(r'\b(?:aria-label|aria-labelledby|title)=', tag, re.I):
        return source
    replacement = tag[:-1] + f' aria-label="{html.escape(label, quote=True)}">'
    return source[:match.start()] + replacement + source[match.end():]


def _replace_once_or_confirm(source: str, old: str, new: str, label: str) -> str:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        return source.replace(old, new, 1)
    if old_count == 0 and new_count == 1:
        return source
    raise RuntimeError(f"{label} divergente: old={old_count} new={new_count}")


def _replace_css_block(css: str) -> str:
    start_count = css.count(CSS_START)
    end_count = css.count(CSS_END)
    desired = CSS_PATCH
    if start_count == 0 and end_count == 0:
        return css.rstrip() + "\n\n" + desired + "\n"
    if start_count != 1 or end_count != 1:
        raise RuntimeError(f"Markers de acessibilidade divergentes: start={start_count} end={end_count}")
    start = css.index(CSS_START)
    end = css.index(CSS_END, start) + len(CSS_END)
    current = css[start:end].strip()
    if current == desired:
        return css
    return css[:start] + desired + css[end:]


def apply_crm_accessibility_semantics() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    for owner, labels in OWNER_STATIC_LABELS.items():
        for control_id, label in labels.items():
            if not has_accessible_name_for_id(app, control_id, label):
                raise RuntimeError(f"Owner {owner} não materializou accessible name para {control_id}")
    app = apply_accessible_names(app, GLOBAL_STATIC_LABELS)
    for action, label in ACTION_LABELS.items():
        app = _inject_attr_by_action(app, action, label)
    app = _replace_once_or_confirm(app, RULE_FILTER_SOURCE, RULE_FILTER_ACCESSIBLE, "filtros de Regras de Categorização")
    for old, new in PAGINATION_REPLACEMENTS.items():
        app = _replace_once_or_confirm(app, old, new, "paginação icon-only")
    APP.write_text(app, encoding="utf-8")
    syntax = subprocess.run(["node", "--check", str(APP)], capture_output=True, text=True)
    if syntax.returncode != 0:
        raise RuntimeError(f"Bundle inválido após acessibilidade semântica: {(syntax.stderr or syntax.stdout).strip()}")

    css = CSS.read_text(encoding="utf-8")
    updated = _replace_css_block(css)
    if updated != css:
        CSS.write_text(updated, encoding="utf-8")

    print(
        f"Acessibilidade semântica aplicada: {len(STATIC_LABELS)} controles estáticos, "
        f"{len(ACTION_LABELS)} controles dinâmicos e targets móveis compartilhados."
    )
    return 1


if __name__ == "__main__":
    apply_crm_accessibility_semantics()
