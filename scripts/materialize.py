from __future__ import annotations

import base64
import io
import shutil
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / ".bootstrap"
BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def _apply_valtren_brand() -> bool:
    try:
        from apply_valtren_brand import apply_branding
        apply_branding()
        return True
    except Exception as error:
        print(f"Falha ao aplicar a identidade visual da Valtren: {error}", file=sys.stderr)
        return False


def _valid_zip(archive: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            return package.testzip() is None and "index.html" in package.namelist()
    except (zipfile.BadZipFile, zlib.error, EOFError, RuntimeError, OSError):
        return False


def _decode_candidate(encoded: str) -> bytes | None:
    if len(encoded) % 4:
        return None
    try:
        archive = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None
    return archive if _valid_zip(archive) else None


def _diagnose(encoded: str) -> None:
    probes = [0, 20000, 40000, 60000, 70000, 76000, 78000, 78783]
    for q in probes:
        if q > len(encoded):
            continue
        candidate = encoded[:q] + "A" + encoded[q:]
        if len(candidate) % 4:
            continue
        try:
            archive = base64.b64decode(candidate, validate=True)
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                ok = []
                failed = []
                for info in sorted(package.infolist(), key=lambda item: item.header_offset):
                    try:
                        package.read(info)
                        ok.append(info.filename)
                    except Exception:
                        failed.append(info.filename)
                print(f"BOOTSTRAP_PROBE q={q} ok={','.join(ok)} fail={','.join(failed)}")
        except Exception as error:
            print(f"BOOTSTRAP_PROBE q={q} OPEN_FAIL {type(error).__name__}:{error}")


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    parts = [path.read_text(encoding="utf-8").strip() for path in chunks]
    encoded = "".join(parts)

    archive = _decode_candidate(encoded)
    if archive is not None:
        return archive

    boundaries = [0]
    running = 0
    for part in parts:
        running += len(part)
        boundaries.append(running)

    for boundary in boundaries:
        for char in BASE64_ALPHABET:
            candidate = encoded[:boundary] + char + encoded[boundary:]
            archive = _decode_candidate(candidate)
            if archive is not None:
                print(f"Bootstrap payload recuperado automaticamente no offset {boundary} ({char}).")
                return archive

    _diagnose(encoded)
    raise ValueError("não foi possível recuperar o payload Base64 do site nas fronteiras dos chunks")


def main() -> int:
    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))
    if chunks:
        try:
            archive = _read_packaged_archive(chunks)
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                package.extractall(ROOT)
        except (ValueError, zipfile.BadZipFile, base64.binascii.Error, zlib.error) as error:
            print(f"Falha ao reconstruir o projeto: {error}", file=sys.stderr)
            return 1

    if not _apply_valtren_brand():
        return 1

    if chunks and PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)

    print("Projeto da Valtren Solutions materializado e atualizado com sucesso.")
    print("Abra index.html ou execute: python -m http.server 4173")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
