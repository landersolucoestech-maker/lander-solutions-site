#!/usr/bin/env python3
from __future__ import annotations

# Canonical visual-certification facade.
# The historical implementation remains byte-stable in
# certify_visual_base_legacy.py; only the Business naming contract changes here.
import certify_visual_base_legacy as _legacy


def _rename(mapping: dict[str, str], old: str, new: str) -> None:
    if old not in mapping:
        return
    items = list(mapping.items())
    mapping.clear()
    for key, value in items:
        mapping[new if key == old else key] = value


_rename(_legacy.TEMPLATE_MATRIX, "business-products", "business-units-primary")
_rename(_legacy.CANONICAL_ROUTES, "business-products", "business-units-primary")
_rename(_legacy.CANONICAL_ROUTES, "business-units", "business-units-compat")
_legacy.EXPECTED_ACTIVE["#/crm/negocios"] = "Unidades de Negócio"

# Re-export the complete historical harness, including private helpers used by
# sibling certification scripts, after applying the canonical Business contract.
globals().update({name: value for name, value in vars(_legacy).items() if name not in {"__name__", "__package__", "__loader__", "__spec__"}})
