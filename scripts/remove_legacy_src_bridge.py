from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "scripts" / "materialize.py"
workflow = root / ".github" / "workflows" / "remove-legacy-src-bridge.yml"
text = target.read_text(encoding="utf-8")
text = text.replace('WEB_SRC = WEB_ROOT / "src"\n', '')
text = text.replace('LEGACY_SRC = ROOT / "src"\n', '')
old_stage = '''def _stage_legacy_source_compatibility() -> None:\n    if not WEB_SRC.is_dir():\n        raise FileNotFoundError("web/src ausente")\n    if LEGACY_SRC.exists():\n        shutil.rmtree(LEGACY_SRC)\n    shutil.copytree(WEB_SRC, LEGACY_SRC)\n\n    MATERIALIZED_ASSETS.mkdir(parents=True, exist_ok=True)\n    if not WEB_PUBLIC_ASSETS.is_dir():\n        raise FileNotFoundError("web/public/assets ausente")\n    for source in WEB_PUBLIC_ASSETS.iterdir():\n        if source.is_file():\n            shutil.copy2(source, MATERIALIZED_ASSETS / source.name)\n\n\ndef _cleanup_legacy_source_compatibility() -> None:\n    if LEGACY_SRC.exists():\n        shutil.rmtree(LEGACY_SRC)\n\n\n'''
new_stage = '''def _stage_public_assets() -> None:\n    MATERIALIZED_ASSETS.mkdir(parents=True, exist_ok=True)\n    if not WEB_PUBLIC_ASSETS.is_dir():\n        raise FileNotFoundError("web/public/assets ausente")\n    for source in WEB_PUBLIC_ASSETS.iterdir():\n        if source.is_file():\n            shutil.copy2(source, MATERIALIZED_ASSETS / source.name)\n\n\n'''
if old_stage not in text:
    raise SystemExit("legacy source bridge block not found")
text = text.replace(old_stage, new_stage, 1)
old_main = '''def main() -> int:\n    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))\n    try:\n        if chunks:\n            try:\n                archive = _read_packaged_archive(chunks)\n                with zipfile.ZipFile(io.BytesIO(archive)) as package:\n                    package.extractall(ROOT)\n            except (ValueError, zipfile.BadZipFile, base64.binascii.Error, zlib.error) as error:\n                print(f"Falha ao reconstruir o projeto: {error}", file=sys.stderr)\n                return 1\n\n        _stage_legacy_source_compatibility()\n        if not _apply_valtren_brand():\n            return 1\n        if chunks and PAYLOAD_DIR.exists():\n            shutil.rmtree(PAYLOAD_DIR)\n        print("Projeto da Valtren Solutions materializado e atualizado com sucesso.")\n        return 0\n    finally:\n        _cleanup_legacy_source_compatibility()\n'''
new_main = '''def main() -> int:\n    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))\n    if chunks:\n        try:\n            archive = _read_packaged_archive(chunks)\n            with zipfile.ZipFile(io.BytesIO(archive)) as package:\n                package.extractall(ROOT)\n        except (ValueError, zipfile.BadZipFile, base64.binascii.Error, zlib.error) as error:\n            print(f"Falha ao reconstruir o projeto: {error}", file=sys.stderr)\n            return 1\n\n    _stage_public_assets()\n    if not _apply_valtren_brand():\n        return 1\n    if chunks and PAYLOAD_DIR.exists():\n        shutil.rmtree(PAYLOAD_DIR)\n    print("Projeto da Valtren Solutions materializado e atualizado com sucesso.")\n    return 0\n'''
if old_main not in text:
    raise SystemExit("legacy bridge main block not found")
text = text.replace(old_main, new_main, 1)
target.write_text(text, encoding="utf-8")
workflow.unlink(missing_ok=True)
Path(__file__).unlink(missing_ok=True)
print("legacy-src-bridge: removed")
