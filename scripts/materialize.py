from __future__ import annotations

import base64
import io
import shutil
import sys
import zipfile
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
    except zipfile.BadZipFile:
        return False


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    parts = [path.read_text(encoding="utf-8").strip() for path in chunks]
    encoded = "".join(parts)

    try:
        archive = base64.b64decode(encoded, validate=True)
        if _valid_zip(archive):
            return archive
    except (ValueError, base64.binascii.Error):
        pass

    # Historical bootstrap payload: one Base64 character was truncated at the
    # boundary immediately before the final chunk. The last chunk is intact and
    # contains the ZIP central directory tail. Recover the missing character by
    # trying the 64 legal Base64 symbols and accepting the candidate whose ZIP
    # CRC/structure validates completely.
    if len(parts) >= 2:
        prefix = "".join(parts[:-1])
        suffix = parts[-1]
        for char in BASE64_ALPHABET:
            candidate = prefix + char + suffix
            if len(candidate) % 4:
                continue
            try:
                archive = base64.b64decode(candidate, validate=True)
            except (ValueError, base64.binascii.Error):
                continue
            if _valid_zip(archive):
                print(f"Bootstrap payload recuperado automaticamente na fronteira final ({char}).")
                return archive

    raise ValueError("não foi possível recuperar o payload Base64 do site")


def main() -> int:
    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))

    if chunks:
        try:
            archive = _read_packaged_archive(chunks)
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                package.extractall(ROOT)
        except (ValueError, zipfile.BadZipFile, base64.binascii.Error) as error:
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
