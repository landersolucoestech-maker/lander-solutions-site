from __future__ import annotations

import base64
import io
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / ".bootstrap"


def _apply_valtren_brand() -> bool:
    try:
        from apply_valtren_brand import apply_branding

        apply_branding()
        return True
    except Exception as error:
        print(f"Falha ao aplicar a identidade visual da Valtren: {error}", file=sys.stderr)
        return False


def _read_packaged_archive(chunks: list[Path]) -> bytes:
    parts = [path.read_text(encoding="utf-8").strip() for path in chunks]
    encoded = "".join(parts)

    # The historical bootstrap payload in this repository is missing the final
    # three Base64 characters immediately before chunk-10. chunk-10 begins on
    # a valid Base64 quantum and its decoded bytes continue the ZIP central
    # directory. Restoring "AAA" recreates the three zero bytes that were
    # truncated at that boundary and returns the payload to a valid length.
    if len(encoded) % 4 == 1 and len(parts) >= 2 and len(parts[-1]) % 4 == 0:
        encoded = "".join(parts[:-1]) + "AAA" + parts[-1]

    return base64.b64decode(encoded, validate=True)


def main() -> int:
    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))

    if chunks:
        try:
            archive = _read_packaged_archive(chunks)
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                package.testzip()
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
