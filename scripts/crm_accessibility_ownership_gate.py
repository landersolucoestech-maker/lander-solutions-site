from __future__ import annotations

import ast
from pathlib import Path

import crm_accessibility_semantics as accessibility

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

OWNER_SPECS = {
    "business": ("scripts/crm_business.py", "web/src/modules/business/browser.js", "VALTREN BUSINESS CATALOG"),
    "legal_matters": ("scripts/crm_legal_matters.py", "web/src/modules/legal/matters/browser.js", "VALTREN LEGAL MATTERS"),
    "compliance": ("scripts/crm_compliance.py", "web/src/modules/legal/compliance/browser.js", "VALTREN COMPLIANCE"),
    "intellectual_property": ("scripts/crm_intellectual_property.py", "web/src/modules/legal/intellectual-property/browser.js", "VALTREN INTELLECTUAL PROPERTY"),
    "corporate_governance": ("scripts/crm_corporate_governance.py", "web/src/modules/legal/corporate/browser.js", "VALTREN CORPORATE GOVERNANCE"),
}

REMOVED_TRANSACTION_DYNAMIC_CONTROLS = frozenset({
    "crm-fin-counterparty",
    "crm-fin-category",
})
REMOVED_TRANSACTION_STATIC_CONTROLS = frozenset({
    "crm-fin-category",
    "crm-fin-recon",
})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _imported_names(tree: ast.AST, module: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def _owner_call_keys(tree: ast.AST) -> list[str]:
    keys: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "apply_accessible_names":
            continue
        if len(node.args) < 2:
            continue
        arg = node.args[1]
        if not isinstance(arg, ast.Subscript) or not isinstance(arg.value, ast.Name) or arg.value.id != "OWNER_STATIC_LABELS":
            continue
        key_node = arg.slice
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            keys.append(key_node.value)
    return keys


def assert_accessibility_ownership() -> int:
    all_owned: set[str] = set()
    counts: dict[str, int] = {}

    for owner, (materializer_name, browser_name, marker) in OWNER_SPECS.items():
        labels = accessibility.OWNER_STATIC_LABELS.get(owner)
        _require(bool(labels), f"Accessibility ownership: allowlist ausente para {owner}")
        owner_ids = set(labels)
        _require(not (all_owned & owner_ids), f"Accessibility ownership: IDs duplicados entre owners: {sorted(all_owned & owner_ids)}")
        all_owned.update(owner_ids)
        counts[owner] = len(owner_ids)

        materializer_path = ROOT / materializer_name
        browser_path = ROOT / browser_name
        _require(materializer_path.exists(), f"Accessibility ownership: materializer ausente: {materializer_name}")
        _require(browser_path.exists(), f"Accessibility ownership: browser source ausente: {browser_name}")

        materializer = materializer_path.read_text(encoding="utf-8")
        browser = browser_path.read_text(encoding="utf-8")
        tree = ast.parse(materializer, filename=materializer_name)
        imported = _imported_names(tree, "crm_accessibility_semantics")
        _require({"OWNER_STATIC_LABELS", "apply_accessible_names"} <= imported, f"Accessibility ownership: {owner} não importa o primitive compartilhado")
        _require(_owner_call_keys(tree) == [owner], f"Accessibility ownership: {owner} não aplica exclusivamente sua allowlist")
        _require("BROWSER.read_text" in materializer, f"Accessibility ownership: {owner} não reconstrói a partir do browser source")
        _require(marker in materializer, f"Accessibility ownership: marker reconstrutivo ausente em {owner}")
        if owner == "business":
            _require("JS_START" in materializer and "JS_END" in materializer and "re.sub" in materializer, "Accessibility ownership: Business perdeu contrato reconstrutivo")
        else:
            _require("replace_marked_block" in materializer, f"Accessibility ownership: {owner} perdeu replace_marked_block")

        for control_id in labels:
            _require(browser.count(f'id="{control_id}"') == 1, f"Accessibility ownership: {owner}/{control_id} não é emitido exatamente uma vez pelo browser source")

        transformed = accessibility.apply_accessible_names(browser, labels)
        transformed_twice = accessibility.apply_accessible_names(transformed, labels)
        _require(transformed == transformed_twice, f"Accessibility ownership: primitive não é idempotente em {owner}")
        for control_id, label in labels.items():
            _require(accessibility.has_accessible_name_for_id(transformed, control_id, label), f"Accessibility ownership: accessible name ausente após owner {owner}: {control_id}")

    _require(all_owned == set(accessibility.OWNED_STATIC_IDS), "Accessibility ownership: union das allowlists diverge de OWNED_STATIC_IDS")
    _require(not (all_owned & set(accessibility.GLOBAL_STATIC_LABELS)), "Accessibility ownership: passe transversal ainda contém IDs owned")
    _require(len(accessibility.STATIC_LABELS) == 117, f"Accessibility ownership: política estática mudou de 117 para {len(accessibility.STATIC_LABELS)}")
    leaked_static = REMOVED_TRANSACTION_STATIC_CONTROLS & set(accessibility.STATIC_LABELS)
    _require(not leaked_static, f"Accessibility ownership: filtros removidos de Transações voltaram à política estática: {sorted(leaked_static)}")
    _require(len(accessibility.ACTION_LABELS) == 5, f"Accessibility ownership: política dinâmica mudou de 5 para {len(accessibility.ACTION_LABELS)}")
    leaked_transaction_controls = REMOVED_TRANSACTION_DYNAMIC_CONTROLS & set(accessibility.ACTION_LABELS)
    _require(not leaked_transaction_controls, f"Accessibility ownership: controles removidos de Transações voltaram à política dinâmica: {sorted(leaked_transaction_controls)}")

    post_owner = (SCRIPTS / "crm_product_system_review.py").read_text(encoding="utf-8")
    leaked = sorted(control_id for control_id in all_owned if control_id in post_owner)
    _require(not leaked, f"Accessibility ownership: Global Review contém patch direto de IDs owned: {leaked}")

    materialize = (SCRIPTS / "materialize.py").read_text(encoding="utf-8")
    _require(materialize.find("assert_accessibility_ownership()") < materialize.find("apply_branding()"), "Accessibility ownership gate precisa executar antes dos materializadores")
    global_at = materialize.find("apply_crm_accessibility_semantics()")
    _require(global_at > 0, "Accessibility ownership: passe transversal ausente da cadeia")
    calls = {
        "business": "apply_crm_business()",
        "legal_matters": "apply_crm_legal_matters()",
        "compliance": "apply_crm_compliance()",
        "intellectual_property": "apply_crm_intellectual_property()",
        "corporate_governance": "apply_crm_corporate_governance()",
    }
    for owner, call_name in calls.items():
        _require(0 <= materialize.find(call_name) < global_at, f"Accessibility ownership: ordem inválida para {owner}")

    print("Accessibility ownership gate: PASS " + ", ".join(f"{owner}={count}" for owner, count in counts.items()) + f"; global={len(accessibility.GLOBAL_STATIC_LABELS)}; total={len(accessibility.STATIC_LABELS)}")
    return 1


if __name__ == "__main__":
    assert_accessibility_ownership()
