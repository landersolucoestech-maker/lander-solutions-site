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


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)
    hits: list[tuple[int, int]] = []
    for position in range(48080, 78784):
        candidate = encoded[:position] + "A" + encoded[position:]
        try:
            archive = base64.b64decode(candidate, validate=True)
        except (ValueError, base64.binascii.Error):
            continue
        eof, size, crc = _inflate_app(archive)
        if eof and size == APP_UNCOMPRESSED_SIZE:
            hits.append((position, crc))
    print(f"EXHAUSTIVE_HITS total={len(hits)}")
    for position, crc in hits:
        print(f"EXHAUSTIVE_HIT q={position} crc={crc:08x} target={APP_TARGET_CRC:08x}")
    raise ValueError("diagnóstico exaustivo concluído")


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
