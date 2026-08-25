from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-global-light-surfaces-v1"

CSS_PATCH = r'''
/* VALTREN CRM GLOBAL LIGHT SURFACES */
.crm-app-shell .crm-main,
.crm-app-shell .crm-workspace,
.crm-app-shell .crm-ref-workspace,
.crm-app-shell .crm-agenda-workspace{
  color-scheme:light!important;
}

.crm-app-shell .crm-workspace input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="range"]),
.crm-app-shell .crm-workspace select,
.crm-app-shell .crm-workspace textarea,
#crm-rel-modal-root input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="range"]),
#crm-rel-modal-root select,
#crm-rel-modal-root textarea,
#crm-agenda-modal-root input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="range"]),
#crm-agenda-modal-root select,
#crm-agenda-modal-root textarea,
#crm-ref-modal-root input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="range"]),
#crm-ref-modal-root select,
#crm-ref-modal-root textarea{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  -webkit-text-fill-color:#0B1D3A!important;
  border-color:#D7DFE8!important;
  box-shadow:none!important;
  color-scheme:light!important;
}

.crm-app-shell .crm-workspace select option,
#crm-rel-modal-root select option,
#crm-agenda-modal-root select option,
#crm-ref-modal-root select option{
  background:#FFFFFF!important;
  color:#0B1D3A!important;
}

.crm-app-shell .crm-workspace input::placeholder,
.crm-app-shell .crm-workspace textarea::placeholder,
#crm-rel-modal-root input::placeholder,
#crm-rel-modal-root textarea::placeholder,
#crm-agenda-modal-root input::placeholder,
#crm-agenda-modal-root textarea::placeholder,
#crm-ref-modal-root input::placeholder,
#crm-ref-modal-root textarea::placeholder{
  color:#94A3B8!important;
  -webkit-text-fill-color:#94A3B8!important;
  opacity:1!important;
}

.crm-app-shell .crm-workspace .crm-panel,
.crm-app-shell .crm-workspace .crm-kpi,
.crm-app-shell .crm-workspace .crm-mini-metric,
.crm-app-shell .crm-workspace .crm-result-grid>article,
.crm-app-shell .crm-workspace .crm-distribution-calc>div,
.crm-app-shell .crm-workspace .crm-venture-card,
.crm-app-shell .crm-workspace .crm-rel-kpi,
.crm-app-shell .crm-workspace .crm-rel-list-panel,
.crm-app-shell .crm-workspace .crm-ref-kpi,
.crm-app-shell .crm-workspace .crm-ref-panel,
.crm-app-shell .crm-workspace .crm-ref-table-card,
.crm-app-shell .crm-workspace .crm-ref-calendar,
.crm-app-shell .crm-workspace .crm-ref-entity-list,
.crm-app-shell .crm-workspace .crm-agenda-calendar,
.crm-app-shell .crm-workspace .crm-agenda-year-card,
.crm-app-shell .crm-workspace .crm-agenda-day,
.crm-app-shell .crm-workspace .crm-agenda-time-cell,
.crm-app-shell .crm-workspace .crm-agenda-day-time-cell{
  background:#FFFFFF!important;
  color:#0B1D3A!important;
}

.crm-app-shell .crm-workspace .crm-result-total,
.crm-app-shell .crm-workspace .crm-distribution-calc .total{
  background:#FFFFFF!important;
  color:#0B1D3A!important;
  border:1px solid rgba(11,29,58,.10)!important;
}
.crm-app-shell .crm-workspace .crm-result-total>span,
.crm-app-shell .crm-workspace .crm-distribution-calc .total span{
  color:#64748B!important;
}
.crm-app-shell .crm-workspace .crm-result-total strong,
.crm-app-shell .crm-workspace .crm-distribution-calc .total strong{
  color:#B8891F!important;
}

/* Agenda: remove barras navy indevidas nos dias do mês. */
.crm-agenda-month .crm-agenda-day>header{
  display:flex!important;
  align-items:center!important;
  justify-content:flex-end!important;
  min-height:28px!important;
  margin:0 0 6px!important;
  padding:0!important;
  background:#FFFFFF!important;
  color:#0B1D3A!important;
}
.crm-agenda-month .crm-agenda-day>header span{
  display:inline-grid!important;
  place-items:center!important;
  width:24px!important;
  min-width:24px!important;
  max-width:24px!important;
  height:24px!important;
  min-height:24px!important;
  max-height:24px!important;
  flex:0 0 24px!important;
  margin:0!important;
  padding:0!important;
  border:0!important;
  border-radius:999px!important;
  background:transparent!important;
  color:#0B1D3A!important;
  box-shadow:none!important;
}
.crm-agenda-month .crm-agenda-day.muted>header span{
  color:#94A3B8!important;
}
.crm-agenda-month .crm-agenda-day.today>header span{
  background:#FFF7D6!important;
  color:#0B1D3A!important;
  box-shadow:inset 0 0 0 1px #D4AF37!important;
}

/* Estados ativos e ações internas usam dourado em vez de blocos navy. */
.crm-app-shell .crm-ref-subtabs a.active,
.crm-app-shell .crm-ref-pnl-tabs button.active,
.crm-app-shell .crm-ref-ai-tabs button.active,
.crm-app-shell .crm-agenda-view-toggle button.active,
.crm-app-shell .crm-ref-actions .primary,
.crm-app-shell .crm-ref-panel .primary,
#crm-ref-modal-root .crm-ref-modal footer .primary,
#crm-agenda-modal-root .crm-agenda-modal footer .primary,
#crm-rel-modal-root .crm-rel-modal-footer .crm-rel-primary{
  background:#D4AF37!important;
  background-color:#D4AF37!important;
  color:#0B1D3A!important;
  border-color:#D4AF37!important;
  -webkit-text-fill-color:#0B1D3A!important;
}
.crm-app-shell .crm-ref-stepper button.active b,
.crm-app-shell .crm-ref-stepper span.active{
  background:#FFF7D6!important;
  color:#0B1D3A!important;
  border-color:#D4AF37!important;
}

/* Modais: todas as superfícies estruturais permanecem claras. */
#crm-rel-modal-root .crm-rel-modal,
#crm-rel-modal-root .crm-rel-modal-header,
#crm-rel-modal-root .crm-rel-modal-body,
#crm-rel-modal-root .crm-rel-modal-footer,
#crm-agenda-modal-root .crm-agenda-modal,
#crm-agenda-modal-root .crm-agenda-modal>header,
#crm-agenda-modal-root .crm-agenda-modal-body,
#crm-agenda-modal-root .crm-agenda-modal footer,
#crm-agenda-modal-root .crm-agenda-picker-trigger,
#crm-agenda-modal-root .crm-agenda-picker-menu,
#crm-agenda-modal-root .crm-agenda-picker-search,
#crm-agenda-modal-root .crm-agenda-venue-option,
#crm-ref-modal-root .crm-ref-modal,
#crm-ref-modal-root .crm-ref-modal>header,
#crm-ref-modal-root .crm-ref-modal-body,
#crm-ref-modal-root .crm-ref-modal footer,
#crm-ref-modal-root .crm-ref-form-section,
#crm-ref-modal-root .crm-ref-campaign-stage,
#crm-ref-modal-root .crm-ref-campaign-side>section,
#crm-ref-modal-root .crm-ref-advanced,
#crm-ref-modal-root .crm-fidelity-content-preview,
#crm-ref-modal-root .crm-fidelity-content-form,
#crm-ref-modal-root .crm-fidelity-media-drop{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
}

html[data-theme="dark"] .crm-app-shell .crm-workspace,
html[data-theme="dark"] .crm-app-shell .crm-ref-workspace,
html[data-theme="dark"] .crm-app-shell .crm-agenda-workspace,
html[data-theme="dark"] #crm-rel-modal-root .crm-rel-modal,
html[data-theme="dark"] #crm-agenda-modal-root .crm-agenda-modal,
html[data-theme="dark"] #crm-ref-modal-root .crm-ref-modal{
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  color-scheme:light!important;
}
'''


def apply_crm_global_light_surface_fix() -> int:
    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM GLOBAL LIGHT SURFACES \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Superfícies internas do CRM padronizadas em tema claro; navy restrito ao chrome e estados controlados.")
    return 1


if __name__ == "__main__":
    apply_crm_global_light_surface_fix()
