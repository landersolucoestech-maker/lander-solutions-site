from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WEB_SRC = ROOT / "web" / "src"
SELF = Path(__file__).resolve()
WORKFLOW = ROOT / ".github" / "workflows" / "finish-product-source-dedupe.yml"
TEXT_SUFFIXES = {".js", ".py", ".md", ".yml", ".yaml"}
PRODUCT_SUFFIXES = {".js", ".css"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_args(canonical: Path, quote: str = "'") -> str:
    parts = ("..", *canonical.relative_to(ROOT).parts)
    return ",".join(f"{quote}{part}{quote}" for part in parts)


def migrate_common(text: str, old: Path, canonical: Path) -> str:
    name = old.name
    rel = canonical.relative_to(ROOT).as_posix()
    req = "../" + rel
    text = text.replace(f"require('./{name}')", f"require('{req}')")
    text = text.replace(f'require("./{name}")', f'require("{req}")')
    text = text.replace(f"path.resolve(__dirname,'{name}')", f"path.resolve(__dirname,{canonical_args(canonical)})")
    text = text.replace(f"path.resolve(__dirname, '{name}')", f"path.resolve(__dirname, {canonical_args(canonical).replace(',', ', ')})")
    text = text.replace(f"path.join(__dirname,'{name}')", f"path.join(__dirname,{canonical_args(canonical)})")
    text = text.replace(f"path.join(__dirname, '{name}')", f"path.join(__dirname, {canonical_args(canonical).replace(',', ', ')})")
    text = text.replace(f"scripts/{name}", rel)
    text = text.replace(f'SCRIPTS / "{name}"', 'ROOT / ' + ' / '.join(f'"{p}"' for p in canonical.relative_to(ROOT).parts))
    text = text.replace(f"SCRIPTS / '{name}'", "ROOT / " + " / ".join(repr(p) for p in canonical.relative_to(ROOT).parts))
    return text


def update_accessibility_gate() -> None:
    path = SCRIPTS / "crm_accessibility_ownership_gate.py"
    text = path.read_text(encoding="utf-8")
    specs = {
        '("crm_business.py", "crm_business_browser.js",': '("scripts/crm_business.py", "web/src/modules/business/browser.js",',
        '("crm_legal_matters.py", "crm_legal_matters_browser.js",': '("scripts/crm_legal_matters.py", "web/src/modules/legal/matters/browser.js",',
        '("crm_compliance.py", "crm_compliance_browser.js",': '("scripts/crm_compliance.py", "web/src/modules/legal/compliance/browser.js",',
        '("crm_intellectual_property.py", "crm_intellectual_property_browser.js",': '("scripts/crm_intellectual_property.py", "web/src/modules/legal/intellectual-property/browser.js",',
        '("crm_corporate_governance.py", "crm_corporate_governance_browser.js",': '("scripts/crm_corporate_governance.py", "web/src/modules/legal/corporate/browser.js",',
    }
    for old, new in specs.items():
        text = text.replace(old, new)
    text = text.replace('materializer_path = SCRIPTS / materializer_name', 'materializer_path = ROOT / materializer_name')
    text = text.replace('browser_path = SCRIPTS / browser_name', 'browser_path = ROOT / browser_name')
    path.write_text(text, encoding="utf-8")


def main() -> int:
    update_accessibility_gate()

    canonical_by_digest: dict[str, list[Path]] = {}
    for path in WEB_SRC.rglob("*"):
        if path.is_file() and path.suffix in PRODUCT_SUFFIXES:
            canonical_by_digest.setdefault(digest(path), []).append(path)

    candidates: dict[Path, Path] = {}
    for path in SCRIPTS.iterdir():
        if path.is_file() and path.suffix in PRODUCT_SUFFIXES:
            matches = canonical_by_digest.get(digest(path), [])
            if len(matches) == 1:
                candidates[path] = matches[0]

    changed: set[str] = set()
    for old, canonical in candidates.items():
        for base in (SCRIPTS, ROOT / ".github" / "workflows", ROOT / "docs"):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path in {old, SELF, WORKFLOW}:
                    continue
                original = path.read_text(encoding="utf-8")
                updated = migrate_common(original, old, canonical)
                if updated != original:
                    path.write_text(updated, encoding="utf-8")
                    changed.add(str(path.relative_to(ROOT)))

    # Only executable/path-like references block deletion. Test filenames containing
    # the source basename are not dependencies.
    blockers: dict[str, list[str]] = {}
    needles = lambda name: (
        f"require('./{name}')", f'require("./{name}")', f"scripts/{name}",
        f"path.resolve(__dirname,'{name}')", f"path.resolve(__dirname, '{name}')",
        f"path.join(__dirname,'{name}')", f"path.join(__dirname, '{name}')",
        f'SCRIPTS / "{name}"', f"SCRIPTS / '{name}'",
    )
    removed: list[str] = []
    for old, canonical in candidates.items():
        refs: list[str] = []
        for base in (SCRIPTS, ROOT / ".github" / "workflows", ROOT / "docs"):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path in {old, SELF, WORKFLOW}:
                    continue
                text = path.read_text(encoding="utf-8")
                if any(needle in text for needle in needles(old.name)):
                    refs.append(str(path.relative_to(ROOT)))
        if refs:
            blockers[str(old.relative_to(ROOT))] = sorted(set(refs))
        else:
            old.unlink()
            removed.append(str(old.relative_to(ROOT)))

    WORKFLOW.unlink(missing_ok=True)
    SELF.unlink(missing_ok=True)

    print(f"final-product-source-dedupe: candidates={len(candidates)} removed={len(removed)} blockers={len(blockers)} refs_changed={len(changed)}")
    for path in removed:
        print("REMOVED", path)
    for path, refs in blockers.items():
        print("BLOCKED", path, refs)
    if blockers:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
