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
        from finalize_valtren_brand import finalize_branding
        from identity_lock import lock_identity
        from identity_sweep import sweep_identity
        from logo_site_fix import apply_logo_site_fix
        from site_architecture_refactor import refactor_site_architecture
        from header_menu_center_fix import center_header_menu
        from services_logo_refactor import main as apply_services_and_logo_refactor
        from crm_dashboard_module import apply_crm_dashboard
        from crm_dashboard_visual_fix import apply_crm_dashboard_visual_fix
        from crm_dashboard_kpi_fix import apply_crm_dashboard_kpi_fix
        from crm_relationships_module import apply_crm_relationships
        from crm_header_modal_fix import apply_crm_header_modal_fix
        from crm_global_header import apply_crm_global_header
        from crm_header_context_actions import apply_crm_header_context_actions
        from crm_lead_modal_fix import apply_crm_lead_modal_fix
        from crm_lead_origin_fix import apply_crm_lead_origin_fix
        from crm_relationships_field_color_fix import apply_crm_relationships_field_color_fix
        from crm_relationships_intro_remove import apply_crm_relationships_intro_remove
        from crm_relationships_kpi_tableview_fix import apply_crm_relationships_kpi_tableview_fix
        from crm_canonical_parties import apply_crm_canonical_parties
        from crm_agenda_module import apply_crm_agenda_module
        from crm_reference_modules import apply_crm_reference_modules
        from crm_reference_fidelity_fix import apply_crm_reference_fidelity_fix
        from crm_agenda_calendar_layout_fix import apply_crm_agenda_calendar_layout_fix
        from crm_global_light_surface_fix import apply_crm_global_light_surface_fix
        from crm_header_text_visibility_fix import apply_crm_header_text_visibility_fix
        from crm_financial_automations_remove import apply_crm_financial_automations_remove
        from crm_finance_transactions_label_fix import apply_crm_finance_transactions_label_fix
        from crm_tableview_header_light_fix import apply_crm_tableview_header_light_fix
        from crm_invoice_modal_refactor import apply_crm_invoice_modal_refactor
        from crm_complete_module import apply_crm_complete_module
        from crm_definitive_architecture import apply_crm_definitive_architecture

        apply_branding()
        finalize_branding()
        lock_identity()
        sweep_identity()
        apply_logo_site_fix()
        refactor_site_architecture()
        center_header_menu()
        apply_services_and_logo_refactor()
        apply_crm_dashboard()
        apply_crm_dashboard_visual_fix()
        apply_crm_dashboard_kpi_fix()
        apply_crm_relationships()
        apply_crm_header_modal_fix()
        apply_crm_global_header()
        apply_crm_header_context_actions()
        apply_crm_lead_modal_fix()
        apply_crm_lead_origin_fix()
        apply_crm_relationships_field_color_fix()
        apply_crm_relationships_intro_remove()
        apply_crm_relationships_kpi_tableview_fix()
        apply_crm_canonical_parties()
        apply_crm_agenda_module()
        apply_crm_reference_modules()
        apply_crm_reference_fidelity_fix()
        apply_crm_agenda_calendar_layout_fix()
        apply_crm_global_light_surface_fix()
        apply_crm_header_text_visibility_fix()
        apply_crm_financial_automations_remove()
        apply_crm_finance_transactions_label_fix()
        apply_crm_tableview_header_light_fix()
        apply_crm_invoice_modal_refactor()
        apply_crm_complete_module()
        apply_crm_definitive_architecture()
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

    ranges = (
        range(60970, 61160),
        range(72320, 72490),
        range(73720, 73960),
    )

    for positions in ranges:
        for position in positions:
            for char in BASE64_ALPHABET:
                candidate = encoded[:position] + char + encoded[position:]
                try:
                    archive = base64.b64decode(candidate, validate=True)
                except (ValueError, base64.binascii.Error):
                    continue

                eof, size, crc = _inflate_app(archive)
                if not eof or size != APP_UNCOMPRESSED_SIZE or crc != APP_TARGET_CRC:
                    continue
                if not _valid_zip(archive):
                    continue

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
