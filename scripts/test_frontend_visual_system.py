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
    "crm_financial_transactions.py": "src/modules/finance/transactions/consistency.css",
    "crm_accounting.py": "src/modules/finance/accounting/consistency.css",
    "crm_fiscal_documents.py": "src/modules/finance/fiscal/consistency.css",
    "crm_economic_participations.py": "src/modules/finance/participations/consistency.css",
    "crm_payouts.py": "src/modules/finance/payouts/consistency.css",
    "crm_reference_modules.py": "scripts/crm_reference_modules_consistency.css",
    "crm_legal_matters.py": "src/modules/legal/matters/consistency.css",
    "crm_compliance.py": "src/modules/legal/compliance/consistency.css",
    "crm_intellectual_property.py": "src/modules/legal/intellectual-property/consistency.css",
    "crm_corporate_governance.py": "src/modules/legal/corporate/consistency.css",
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
    for owner_name, css_relative in OWNERS.items():
        owner = SCRIPTS / owner_name
        patch = ROOT / css_relative
        if not owner.exists() or not patch.exists():
            fail(f"visual owner pair missing: {owner_name} -> {css_relative}")
        owner_text = owner.read_text(encoding="utf-8")
        patch_text = patch.read_text(encoding="utf-8")
        css_name = Path(css_relative).name
        if css_relative.startswith("src/"):
            if "MODULE_DIR = ROOT / \"src\"" not in owner_text or "consistency.css" not in owner_text:
                fail(f"{owner_name} does not consume canonical consistency source {css_relative}")
        elif css_name not in owner_text:
            fail(f"{owner_name} does not materialize {css_name}")
        leaked = [selector for selector in FORBIDDEN_SIDEBAR if selector in patch_text]
        if leaked:
            fail(f"{css_relative} illegally styles Sidebar: {', '.join(leaked)}")
        tiny = sorted({int(x) for x in re.findall(r"font-size\s*:\s*(\d+)px", patch_text) if int(x) < 10})
        if tiny:
            fail(f"{css_relative} introduces sub-10px font sizes: {tiny}")
        tiny_shorthand = sorted({int(x) for x in re.findall(r"font\s*:[^;}]*?\b(\d+)px(?:/|\s)", patch_text) if int(x) < 10})
        if tiny_shorthand:
            fail(f"{css_relative} introduces sub-10px font shorthand: {tiny_shorthand}")

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
    harness_files = (SCRIPTS / "certify_visual.py", SCRIPTS / "certify_visual_base.py")
    if not all(path.exists() for path in harness_files):
        fail("split visual certification harness is incomplete")
    harness = "\n".join(path.read_text(encoding="utf-8") for path in harness_files)
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
