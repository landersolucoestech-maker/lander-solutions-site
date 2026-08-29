from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ROOT_DIRS = {".bootstrap", ".github", "api", "assets", "docs", "mockups", "scripts", "src", "web"}
ALLOWED_ROOT_FILES = {".gitignore", "CONFIGURAR-PROJETO.bat", "README.md"}

CANONICAL_MODULES = {
    "dashboard", "agenda", "crm", "finance", "legal", "business", "marketing",
    "communications", "integrations", "settings", "notifications",
}

SOURCE_OWNERS = {
    "dashboard": ("core.js", "participation-core.js", "browser.js", "styles.css"),
    "crm/parties": ("core.js", "adapter.js"),
    "crm/workspace": ("domain.js", "browser.js", "hardening.js", "styles.css"),
    "finance/transactions": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "finance/accounting": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "finance/fiscal": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "finance/allocations": ("core.js", "browser.js", "styles.css"),
    "finance/participations": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "finance/payouts": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "legal/contracts": ("core.js", "browser.js", "styles.css"),
    "legal/matters": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "legal/compliance": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "legal/intellectual-property": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "legal/corporate": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "business": ("core.js", "browser.js", "styles.css"),
    "marketing": ("module.js", "styles.css"),
}

MODULE_CONTRACTS = ("settings", "integrations", "notifications", "communications")

FORBIDDEN_GENERATED_ROOT_FILES = {"app.js", "index.html"}
FORBIDDEN_DIR_NAMES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".nyc_output",
    "node_modules", "dist", "coverage", "playwright-report", "test-results", "_site",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".bak"}


def fail(message: str) -> None:
    print(f"STRUCTURE GATE: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    unexpected_root = sorted(
        entry.name for entry in ROOT.iterdir()
        if entry.name != ".git" and (
            (entry.is_dir() and entry.name not in ALLOWED_ROOT_DIRS)
            or (entry.is_file() and entry.name not in ALLOWED_ROOT_FILES)
        )
    )
    if unexpected_root:
        fail("entradas inesperadas na raiz: " + ", ".join(unexpected_root))

    web_dir = ROOT / "web"
    api_dir = ROOT / "api"
    api_contracts_dir = api_dir / "contracts"
    for required in (web_dir, api_dir, api_contracts_dir):
        if not required.is_dir():
            fail(f"boundary arquitetural ausente: {required.relative_to(ROOT)}")
    for required_file in (web_dir / "README.md", api_dir / "README.md", api_contracts_dir / "README.md"):
        if not required_file.is_file():
            fail(f"contrato de boundary ausente: {required_file.relative_to(ROOT)}")

    src_dir = ROOT / "src"
    modules_dir = src_dir / "modules"
    shared_dir = src_dir / "shared"
    app_dir = src_dir / "app"
    for required in (src_dir, modules_dir, shared_dir, app_dir):
        if not required.is_dir():
            fail(f"estrutura fonte ausente: {required.relative_to(ROOT)}")

    missing_modules = sorted(name for name in CANONICAL_MODULES if not (modules_dir / name).is_dir())
    if missing_modules:
        fail("módulos canônicos ausentes em src/modules: " + ", ".join(missing_modules))

    for forbidden in (modules_dir / "crm" / "agenda", modules_dir / "crm" / "dashboard"):
        if forbidden.exists():
            fail(f"ownership inválido: {forbidden.relative_to(ROOT)}")

    agenda_source = modules_dir / "agenda" / "source"
    if not agenda_source.is_dir() or not list(agenda_source.glob("crm_agenda_module.js.part*")) or not list(agenda_source.glob("crm_agenda_module.css.part*")):
        fail("Agenda não possui source canônico completo em src/modules/agenda/source")

    for relative, filenames in SOURCE_OWNERS.items():
        owner_dir = modules_dir / relative
        if not owner_dir.is_dir():
            fail(f"owner canônico ausente: {owner_dir.relative_to(ROOT)}")
        missing = [name for name in filenames if not (owner_dir / name).is_file()]
        if missing:
            fail(f"fontes canônicas ausentes em {owner_dir.relative_to(ROOT)}: {', '.join(missing)}")

    for module in MODULE_CONTRACTS:
        contract = modules_dir / module / "module.json"
        if not contract.is_file():
            fail(f"contrato de boundary ausente: {contract.relative_to(ROOT)}")

    committed_generated = sorted(name for name in FORBIDDEN_GENERATED_ROOT_FILES if (ROOT / name).exists())
    if committed_generated:
        fail("saída materializada presente no checkout limpo: " + ", ".join(committed_generated))

    generated_css = ROOT / "assets" / "valtren-brand.css"
    if generated_css.exists():
        fail("assets/valtren-brand.css é saída materializada e não deve existir no checkout limpo")

    forbidden_paths: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if any(part in FORBIDDEN_DIR_NAMES for part in path.parts):
            forbidden_paths.append(str(path.relative_to(ROOT)))
            continue
        if path.is_file() and path.suffix in FORBIDDEN_SUFFIXES:
            forbidden_paths.append(str(path.relative_to(ROOT)))
    if forbidden_paths:
        fail("artefatos locais/gerados versionados ou presentes no checkout: " + ", ".join(sorted(forbidden_paths)[:20]))

    scripts_dir = ROOT / "scripts"
    stray_parts = sorted(path.name for path in scripts_dir.iterdir() if path.is_file() and ".part" in path.name)
    if stray_parts:
        fail("fragmentos .part* não podem ficar diretamente em scripts/: " + ", ".join(stray_parts[:20]))
    if not (scripts_dir / "materialize.py").is_file():
        fail("scripts/materialize.py ausente")
    if not sorted((ROOT / ".bootstrap").glob("chunk-*")):
        fail("payload .bootstrap/chunk-* ausente")

    print("STRUCTURE GATE: web/api boundaries, arquitetura funcional, owners canônicos e boundaries sem backend validados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
