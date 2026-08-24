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


def _probe_app(encoded: str) -> None:
    for position in [48080, 50000, 52000, 54000, 56000, 58000, 60000, 62000, 64000, 66000, 68000, 70000, 72000, 74000, 76000, 78000, 78783]:
        if position > len(encoded):
            continue
        candidate = encoded[:position] + "A" + encoded[position:]
        if len(candidate) % 4:
            continue
        try:
            archive = base64.b64decode(candidate, validate=True)
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                total = 0
                try:
                    with package.open("app.js") as src:
                        while True:
                            block = src.read(1024)
                            if not block:
                                break
                            total += len(block)
                    status = "OK"
                except Exception as error:
                    status = f"FAIL:{type(error).__name__}:{str(error)[:80]}"
                print(f"APP_PROBE q={position} bytes={total} status={status}")
        except Exception as error:
            print(f"APP_PROBE q={position} bytes=0 status=OPEN_FAIL:{type(error).__name__}:{str(error)[:80]}")


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    parts = [path.read_text(encoding="utf-8").strip() for path in chunks]
    encoded = "".join(parts)

    archive = _decode_candidate(encoded)
    if archive is not None:
        return archive

    likely_positions = list(range(78770, min(len(encoded), 78790) + 1))
    for position in likely_positions:
        for char in BASE64_ALPHABET:
            candidate = encoded[:position] + char + encoded[position:]
            archive = _decode_candidate(candidate)
            if archive is not None:
                print(f"Bootstrap payload recuperado automaticamente no offset {position} ({char}).")
                return archive

    _probe_app(encoded)
    raise ValueError("não foi possível recuperar o payload Base64 do site")


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
