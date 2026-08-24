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


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)

    # Obtain the authoritative app.js CRC from the intact central directory.
    probe = encoded[:78783] + "A" + encoded[78783:]
    probe_archive = base64.b64decode(probe, validate=True)
    with zipfile.ZipFile(io.BytesIO(probe_archive)) as package:
        target_crc = package.getinfo("app.js").CRC
    print(f"APP_TARGET crc={target_crc:08x} size={APP_UNCOMPRESSED_SIZE}")

    hits = 0
    for position in range(48080, 78784, 25):
        candidate = encoded[:position] + "A" + encoded[position:]
        try:
            archive = base64.b64decode(candidate, validate=True)
        except (ValueError, base64.binascii.Error):
            continue
        eof, size, crc = _inflate_app(archive)
        if eof and size == APP_UNCOMPRESSED_SIZE:
            hits += 1
            print(f"STRUCTURAL_HIT q={position} crc={crc:08x} target={target_crc:08x}")
    print(f"STRUCTURAL_HITS total={hits}")
    raise ValueError("diagnóstico estrutural concluído")


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
