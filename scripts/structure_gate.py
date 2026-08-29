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
}

ALLOWED_ROOT_FILES = {
    ".gitignore",
    "CONFIGURAR-PROJETO.bat",
    "README.md",
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

    materializer = ROOT / "scripts" / "materialize.py"
    if not materializer.is_file():
        fail("scripts/materialize.py ausente")

    bootstrap_chunks = sorted((ROOT / ".bootstrap").glob("chunk-*"))
    if not bootstrap_chunks:
        fail("payload .bootstrap/chunk-* ausente")

    print("STRUCTURE GATE: estrutura canônica do repositório validada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
