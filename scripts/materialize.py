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
APP_COMPRESSED_START = 36124
APP_COMPRESSED_SIZE = 22964
APP_UNCOMPRESSED_SIZE = 93252
APP_TARGET_CRC = 0xC2991650


def _apply_valtren_brand() -> bool:
    try:
        from apply_valtren_brand import apply_branding
        apply_branding()
        return True
    except Exception as error:
        print(f"Falha ao aplicar a identidade visual da Valtren: {error}", file=sys.stderr)
        return False


def _inflate_app(archive: bytes) -> tuple[bool, int, int]:
    compressed = archive[APP_COMPRESSED_START:APP_COMPRESSED_START + APP_COMPRESSED_SIZE]
    dec = zlib.decompressobj(-15)
    try:
        data = dec.decompress(compressed) + dec.flush()
    except zlib.error:
        return False, 0, 0
    return dec.eof, len(data), zlib.crc32(data) & 0xFFFFFFFF


def _valid_zip(archive: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            return package.testzip() is None and "index.html" in package.namelist()
    except (zipfile.BadZipFile, zlib.error, EOFError, RuntimeError, OSError):
        return False


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)

    # The original bootstrap payload lost exactly one Base64 sextet inside
    # app.js. Diagnostics narrowed the missing character to the neighborhood
    # of offset 72405. Recover it deterministically using the original app.js
    # uncompressed size and CRC stored in the ZIP central directory.
    for position in range(72350, 72461):
        for char in BASE64_ALPHABET:
            candidate = encoded[:position] + char + encoded[position:]
            try:
                archive = base64.b64decode(candidate, validate=True)
            except (ValueError, base64.binascii.Error):
                continue
            eof, size, crc = _inflate_app(archive)
            if not eof or size != APP_UNCOMPRESSED_SIZE or crc != APP_TARGET_CRC:
                continue
            if _valid_zip(archive):
                print(f"Bootstrap payload recuperado no offset {position} ({char}).")
                return archive

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
