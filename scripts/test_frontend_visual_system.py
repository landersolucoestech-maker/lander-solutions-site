#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ASSET_CSS = ROOT / "assets" / "valtren-brand.css"
APP = ROOT / "app.js"

OWNERS = {
    "crm_financial_transactions.py": "crm_financial_transactions_consistency.css",
    "crm_accounting.py": "crm_accounting_consistency.css",
    "crm_fiscal_documents.py": "crm_fiscal_documents_consistency.css",
    "crm_economic_participations.py": "crm_economic_participations_consistency.css",
    "crm_payouts.py": "crm_payouts_consistency.css",
    "crm_reference_modules.py": "crm_reference_modules_consistency.css",
    "crm_legal_matters.py": "crm_legal_matters_consistency.css",
    "crm_compliance.py": "crm_compliance_consistency.css",
    "crm_intellectual_property.py": "crm_intellectual_property_consistency.css",
    "crm_corporate_governance.py": "crm_corporate_governance_consistency.css",
}

FORBIDDEN_SIDEBAR = (
    ".crm-sidebar", ".crm-sidebar-head", ".crm-brand", ".crm-nav{",
    ".crm-nav>", ".crm-nav-group", ".crm-nav-subgroup", ".crm-sidebar-overlay",
)

REQUIRED_MATERIALIZED = (
    ".crm-fin-status{font-size:11px",
    ".crm-acct-tabs button{height:40px;font-size:12px",
    ".crm-fiscal-table-wrap th{font-size:11px",
    ".crm-part-table-card th{font-size:11px",
    ".crm-payout-status,.crm-payout-recon{font-size:11px",
    ".crm-ref-table-wrap th{padding:11px 12px;font-size:11px",
    ".crm-legal-matter-table-card th{font-size:11px",
    ".crm-compliance-table-card th{font-size:11px",
    ".crm-ip-table-card th{font-size:11px",
    ".crm-corporate-panel th{font-size:11px",
)


def fail(message: str) -> None:
    raise SystemExit("FAIL " + message)


def source_checks() -> None:
    for owner_name, css_name in OWNERS.items():
        owner = SCRIPTS / owner_name
        patch = SCRIPTS / css_name
        if not owner.exists() or not patch.exists():
            fail(f"visual owner pair missing: {owner_name} -> {css_name}")
        owner_text = owner.read_text(encoding="utf-8")
        patch_text = patch.read_text(encoding="utf-8")
        if css_name not in owner_text:
            fail(f"{owner_name} does not materialize {css_name}")
        leaked = [selector for selector in FORBIDDEN_SIDEBAR if selector in patch_text]
        if leaked:
            fail(f"{css_name} illegally styles Sidebar: {', '.join(leaked)}")
        tiny = sorted({int(x) for x in re.findall(r"font-size\s*:\s*(\d+)px", patch_text) if int(x) < 10})
        if tiny:
            fail(f"{css_name} introduces sub-10px font sizes: {tiny}")
        tiny_shorthand = sorted({int(x) for x in re.findall(r"font\s*:[^;}]*?\b(\d+)px(?:/|\s)", patch_text) if int(x) < 10})
        if tiny_shorthand:
            fail(f"{css_name} introduces sub-10px font shorthand: {tiny_shorthand}")

    reference = (SCRIPTS / "crm_reference_modules.py").read_text(encoding="utf-8")
    if "_assert_no_sidebar_css" not in reference:
        fail("Reference Modules no longer rejects Sidebar structural CSS")
    sidebar_owner = (SCRIPTS / "crm_sidebar_architecture.py").read_text(encoding="utf-8")
    if sidebar_owner.count("function crmRelSidebar(active='relationships',sub='')") != 1:
        fail("Sidebar owner declaration drifted")
    header = (SCRIPTS / "crm_global_header.py").read_text(encoding="utf-8")
    for token in ("Autenticação desativada", "Nenhuma identidade é simulada"):
        if token not in header:
            fail(f"transparent auth state missing from header: {token}")
    harness = (SCRIPTS / "certify_visual.py").read_text(encoding="utf-8")
    if '("Integrações", "Não configurado")' not in harness:
        fail("ValtrenChat compatibility harness is not aligned to 'Não configurado'")
    if "BREAKPOINTS = [1440, 1280, 1024, 768, 390]" not in harness:
        fail("visual harness breakpoint matrix drifted")
    print("frontend-visual-system source: PASS")


def materialized_checks() -> None:
    if not APP.exists() or not ASSET_CSS.exists():
        fail("materialized app.js/assets CSS missing")
    app = APP.read_text(encoding="utf-8")
    css = ASSET_CSS.read_text(encoding="utf-8")
    if len(re.findall(r"\bfunction\s+crmRelSidebar\s*\(", app)) != 1:
        fail("materialized crmRelSidebar declaration count != 1")
    missing = [token for token in REQUIRED_MATERIALIZED if token not in css]
    if missing:
        fail("materialized consistency tokens missing: " + ", ".join(missing))
    for fake in ("Protótipo · dados ilustrativos", "Usuário logado", "23 novas vendas", "Receita Consolidada"):
        if fake in app:
            fail(f"fake operational UI survived materialization: {fake}")
    if "Autenticação desativada" not in app:
        fail("materialized auth-disabled state missing")
    print("frontend-visual-system materialized: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialized", action="store_true")
    args = parser.parse_args()
    source_checks()
    if args.materialized:
        materialized_checks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
