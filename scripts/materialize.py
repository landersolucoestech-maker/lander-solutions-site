from __future__ import annotations

import base64
import io
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / ".bootstrap"


def main() -> int:
    chunks = sorted(PAYLOAD_DIR.glob("chunk-*"))
    if not chunks:
        print("Projeto já materializado ou payload ausente.")
        return 0

    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)

    try:
        archive = base64.b64decode(encoded, validate=True)
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            package.extractall(ROOT)
    except (ValueError, zipfile.BadZipFile) as error:
        print(f"Falha ao reconstruir o projeto: {error}", file=sys.stderr)
        return 1

    shutil.rmtree(PAYLOAD_DIR)
    print("Projeto da Lander Solutions materializado com sucesso.")
    print("Abra index.html ou execute: python -m http.server 4173")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
