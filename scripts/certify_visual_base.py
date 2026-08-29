#!/usr/bin/env python3
from __future__ import annotations

# Canonical visual-certification facade.
# Execute the byte-stable historical implementation in THIS module namespace so
# certify_visual.py can continue monkeypatching wait_ready and the other shared
# hooks exactly as before. Only the Business naming contract changes below.
from pathlib import Path as _Path

_legacy_path = _Path(__file__).with_name("certify_visual_base_legacy.py")
exec(compile(_legacy_path.read_text(encoding="utf-8"), str(_legacy_path), "exec"), globals(), globals())


def _rename(mapping: dict[str, str], old: str, new: str) -> None:
    if old not in mapping:
        return
    items = list(mapping.items())
    mapping.clear()
    for key, value in items:
        mapping[new if key == old else key] = value


_rename(TEMPLATE_MATRIX, "business-products", "business-units-primary")
_rename(CANONICAL_ROUTES, "business-products", "business-units-primary")
_rename(CANONICAL_ROUTES, "business-units", "business-units-compat")
EXPECTED_ACTIVE["#/crm/negocios"] = "Unidades de Negócio"
