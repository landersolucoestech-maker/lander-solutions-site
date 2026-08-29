from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ROOT_DIRS = {
    ".bootstrap",
    ".github",
    "assets",
    "docs",
    "mockups",
    "scripts",
    "src",
}

ALLOWED_ROOT_FILES = {
    ".gitignore",
    "CONFIGURAR-PROJETO.bat",
    "README.md",
}

CANONICAL_MODULES = {
    "dashboard",
    "agenda",
    "crm",
    "finance",
    "legal",
    "business",
    "marketing",
    "communications",
    "integrations",
    "settings",
    "notifications",
}

FINANCE_SOURCE_FILES = {
    "transactions": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "accounting": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "fiscal": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "allocations": ("core.js", "browser.js", "styles.css"),
    "participations": ("core.js", "browser.js", "styles.css", "consistency.css"),
    "payouts": ("core.js", "browser.js", "styles.css", "consistency.css"),
}

FORBIDDEN_GENERATED_ROOT_FILES = {
    "app.js",
    "index.html",
}

FORBIDDEN_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".nyc_output",
    "node_modules",
    "dist",
    "coverage",
    "playwright-report",
    "test-results",
    "_site",
}

FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".bak",
}


def fail(message: str) -> None:
    print(f"STRUCTURE GATE: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    unexpected_root = sorted(
        entry.name
        for entry in ROOT.iterdir()
        if entry.name != ".git"
        and (
            (entry.is_dir() and entry.name not in ALLOWED_ROOT_DIRS)
            or (entry.is_file() and entry.name not in ALLOWED_ROOT_FILES)
        )
    )
    if unexpected_root:
        fail("entradas inesperadas na raiz: " + ", ".join(unexpected_root))

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

    finance_dir = modules_dir / "finance"
    for subdomain, filenames in FINANCE_SOURCE_FILES.items():
        owner_dir = finance_dir / subdomain
        if not owner_dir.is_dir():
            fail(f"owner financeiro ausente: {owner_dir.relative_to(ROOT)}")
        missing = [name for name in filenames if not (owner_dir / name).is_file()]
        if missing:
            fail(f"fontes financeiras ausentes em {owner_dir.relative_to(ROOT)}: {', '.join(missing)}")

    committed_generated = sorted(
        name for name in FORBIDDEN_GENERATED_ROOT_FILES if (ROOT / name).exists()
    )
    if committed_generated:
        fail(
            "saída materializada presente no checkout limpo: "
            + ", ".join(committed_generated)
        )

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
        sample = ", ".join(sorted(forbidden_paths)[:20])
        fail("artefatos locais/gerados versionados ou presentes no checkout: " + sample)

    scripts_dir = ROOT / "scripts"
    stray_parts = sorted(
        path.name
        for path in scripts_dir.iterdir()
        if path.is_file() and ".part" in path.name
    )
    if stray_parts:
        fail(
            "fragmentos .part* não podem ficar diretamente em scripts/: "
            + ", ".join(stray_parts[:20])
        )

    materializer = scripts_dir / "materialize.py"
    if not materializer.is_file():
        fail("scripts/materialize.py ausente")

    bootstrap_chunks = sorted((ROOT / ".bootstrap").glob("chunk-*"))
    if not bootstrap_chunks:
        fail("payload .bootstrap/chunk-* ausente")

    print("STRUCTURE GATE: src/app + src/modules + src/shared, ownership funcional e fontes financeiras validados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
