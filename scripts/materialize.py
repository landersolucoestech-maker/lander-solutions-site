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


def _diagnose_raw_app(encoded: str) -> None:
    # app.js local record starts at ZIP byte 36060 -> Base64 offset 48080.
    # The observed central-directory boundary is 78783 because one sextet is
    # missing. Decode the largest aligned prefix before that boundary so bytes
    # before the actual deletion remain untouched.
    segment = encoded[48080:78780]
    raw = base64.b64decode(segment, validate=True)
    print(f"RAW_APP segment_chars={len(segment)} decoded_bytes={len(raw)} header={raw[:4]!r}")
    # The local record overhead for app.js is 64 bytes; compressed DEFLATE data
    # begins immediately after it.
    compressed = raw[64:]
    dec = zlib.decompressobj(-15)
    produced = 0
    for index, byte in enumerate(compressed):
        try:
            out = dec.decompress(bytes([byte]))
            produced += len(out)
        except zlib.error as error:
            absolute_byte = 36124 + index
            approx_b64 = (absolute_byte * 4) // 3
            print(
                f"RAW_APP_ERROR compressed_index={index} absolute_zip_byte={absolute_byte} "
                f"approx_b64={approx_b64} produced={produced} error={error}"
            )
            return
    try:
        produced += len(dec.flush())
        print(f"RAW_APP_NO_ERROR produced={produced} eof={dec.eof} unused={len(dec.unused_data)}")
    except zlib.error as error:
        print(f"RAW_APP_FLUSH_ERROR produced={produced} error={error}")


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)
    _diagnose_raw_app(encoded)
    raise ValueError("diagnóstico do payload concluído")


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
