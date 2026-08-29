from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
WORKFLOW = ROOT / ".github" / "workflows" / "architecture-source-migration.yml"
EXCLUDED = {
    ROOT / "scripts" / "materialize.py",
    ROOT / "scripts" / "structure_gate.py",
    SELF,
}

TEXT_SUFFIXES = {".py", ".js", ".md", ".yml", ".yaml"}


def migrate_text(text: str) -> str:
    # Python/pathlib canonical source references.
    text = text.replace('ROOT / "src" / "modules"', 'ROOT / "web" / "src" / "modules"')
    text = text.replace("ROOT / 'src' / 'modules'", "ROOT / 'web' / 'src' / 'modules'")
    text = text.replace('ROOT / "src"', 'ROOT / "web" / "src"')
    text = text.replace("ROOT / 'src'", "ROOT / 'web' / 'src'")

    # Node/CommonJS and path helpers.
    text = text.replace("require('../src/modules/", "require('../web/src/modules/")
    text = text.replace('require("../src/modules/', 'require("../web/src/modules/')
    text = text.replace("'..','src','modules'", "'..','web','src','modules'")
    text = text.replace("'..', 'src', 'modules'", "'..', 'web', 'src', 'modules'")
    text = text.replace('"..", "src", "modules"', '"..", "web", "src", "modules"')

    # Documentation/test expectations that name the canonical committed tree.
    text = re.sub(r'(?<!web/)src/modules/', 'web/src/modules/', text)
    text = text.replace('css_relative.startswith("src/")', 'css_relative.startswith("web/src/")')
    text = text.replace('MODULE_DIR = ROOT / \\"src\\"', 'MODULE_DIR = ROOT / \\"web\\" / \\"src\\"')
    return text


def main() -> int:
    changed: list[str] = []
    roots = [ROOT / "scripts", ROOT / "docs", ROOT / ".github" / "workflows"]
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path in EXCLUDED or path == WORKFLOW:
                continue
            original = path.read_text(encoding="utf-8")
            updated = migrate_text(original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed.append(str(path.relative_to(ROOT)))

    # One-shot migration artifacts remove themselves from the resulting commit.
    if WORKFLOW.exists():
        WORKFLOW.unlink()
    if SELF.exists():
        SELF.unlink()

    print(f"web-source-path-migration: changed={len(changed)}")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
