#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNER = HERE / "crm_sidebar_architecture.py"

STRUCTURAL = (
    "crm-sidebar",
    "crm-sidebar-head",
    "crm-brand",
    "crm-nav",
    "crm-nav-group",
    "crm-nav-subgroup",
    "crm-sidebar-overlay",
)

# CSS declaration-like selectors only. Runtime querySelector/class references do
# not match because this expression requires a CSS opening brace.
SELECTOR_RE = re.compile(
    r"\.((?:crm-sidebar-head|crm-sidebar-overlay|crm-sidebar|crm-brand|crm-nav-subgroup|crm-nav-group|crm-nav))(?![-\w])[^{}\n]*\{"
)
DECL_RE = re.compile(r"^[ \t]*function[ \t]+crmRelSidebar[ \t]*\(", re.M)


def source_files() -> list[Path]:
    files: list[Path] = []
    for path in HERE.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith("test_"):
            continue
        if path.suffix == ".py" or ".css" in path.name or ".js" in path.name:
            files.append(path)
    return sorted(files)


def main() -> int:
    owner_text = OWNER.read_text(encoding="utf-8")
    owner_selectors = set(SELECTOR_RE.findall(owner_text))
    missing = [name for name in STRUCTURAL if name not in owner_selectors]
    if missing:
        raise SystemExit(f"FAIL owner Sidebar incompleto; seletores ausentes: {', '.join(missing)}")

    css_conflicts: list[str] = []
    declaration_conflicts: list[str] = []
    for path in source_files():
        text = path.read_text(encoding="utf-8")
        if path != OWNER:
            selectors = sorted(set(SELECTOR_RE.findall(text)))
            if selectors:
                css_conflicts.append(f"{path.name}: {', '.join(selectors)}")
            if DECL_RE.search(text):
                declaration_conflicts.append(path.name)

    if css_conflicts:
        raise SystemExit("FAIL CSS estrutural da Sidebar fora do owner:\n" + "\n".join(css_conflicts))
    if declaration_conflicts:
        raise SystemExit("FAIL declaração crmRelSidebar fora do owner: " + ", ".join(declaration_conflicts))

    owner_declarations = len(DECL_RE.findall(owner_text))
    if owner_declarations != 1:
        raise SystemExit(f"FAIL owner possui {owner_declarations} declarações crmRelSidebar; esperado 1")

    print("sidebar-source-ownership: PASS")
    print(f"owner: {OWNER.name}")
    print(f"crmRelSidebar declarations in owner: {owner_declarations}")
    print("structural selectors owned exclusively: " + ", ".join(STRUCTURAL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
