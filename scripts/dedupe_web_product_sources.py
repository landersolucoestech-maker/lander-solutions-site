from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WEB_SRC = ROOT / "web" / "src"
SELF = Path(__file__).resolve()
WORKFLOW = ROOT / ".github" / "workflows" / "dedupe-web-product-sources.yml"
TEXT_SUFFIXES = {".js", ".py", ".md", ".yml", ".yaml"}
PRODUCT_SUFFIXES = {".js", ".css"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js_require_path(canonical: Path) -> str:
    return "../" + canonical.relative_to(ROOT).as_posix()


def migrate_reference(text: str, old_name: str, canonical: Path) -> str:
    rel = canonical.relative_to(ROOT)
    rel_posix = rel.as_posix()
    parts = list(rel.parts)
    joined_single = ",".join(repr(part) for part in ("..", *parts))
    joined_single_spaced = ", ".join(repr(part) for part in ("..", *parts))

    text = text.replace(f"require('./{old_name}')", f"require('{js_require_path(canonical)}')")
    text = text.replace(f'require("./{old_name}")', f'require("{js_require_path(canonical)}")')
    text = text.replace(f"path.join(__dirname,'{old_name}')", f"path.join(__dirname,{joined_single})")
    text = text.replace(f"path.join(__dirname, '{old_name}')", f"path.join(__dirname, {joined_single_spaced})")
    text = text.replace(f'path.join(__dirname,"{old_name}")', 'path.join(__dirname,' + ','.join('"'+p+'"' for p in ("..", *parts)) + ')')
    text = text.replace(f'path.join(__dirname, "{old_name}")', 'path.join(__dirname, ' + ', '.join('"'+p+'"' for p in ("..", *parts)) + ')')
    text = text.replace(f"scripts/{old_name}", rel_posix)
    return text


def main() -> int:
    canonical_by_digest: dict[str, list[Path]] = {}
    for path in WEB_SRC.rglob("*"):
        if path.is_file() and path.suffix in PRODUCT_SUFFIXES:
            canonical_by_digest.setdefault(digest(path), []).append(path)

    candidates: dict[Path, Path] = {}
    for path in SCRIPTS.iterdir():
        if not path.is_file() or path.suffix not in PRODUCT_SUFFIXES:
            continue
        matches = canonical_by_digest.get(digest(path), [])
        if len(matches) == 1:
            candidates[path] = matches[0]

    changed_refs: set[Path] = set()
    for old, canonical in candidates.items():
        for base in (SCRIPTS, ROOT / ".github" / "workflows", ROOT / "docs"):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path in {old, SELF, WORKFLOW}:
                    continue
                original = path.read_text(encoding="utf-8")
                updated = migrate_reference(original, old.name, canonical)
                if updated != original:
                    path.write_text(updated, encoding="utf-8")
                    changed_refs.add(path)

    removed: list[tuple[Path, Path]] = []
    blocked: list[tuple[Path, Path, list[str]]] = []
    for old, canonical in candidates.items():
        refs: list[str] = []
        for base in (SCRIPTS, ROOT / ".github" / "workflows", ROOT / "docs"):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path in {old, SELF, WORKFLOW}:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if old.name in text:
                    refs.append(str(path.relative_to(ROOT)))
        if refs:
            blocked.append((old, canonical, sorted(set(refs))))
            continue
        old.unlink()
        removed.append((old, canonical))

    WORKFLOW.unlink(missing_ok=True)
    SELF.unlink(missing_ok=True)

    print(f"product-source-dedupe: candidates={len(candidates)} removed={len(removed)} blocked={len(blocked)} refs_changed={len(changed_refs)}")
    for old, canonical in removed:
        print(f"REMOVED {old.relative_to(ROOT)} -> {canonical.relative_to(ROOT)}")
    for old, canonical, refs in blocked:
        print(f"BLOCKED {old.relative_to(ROOT)} -> {canonical.relative_to(ROOT)} refs={refs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
