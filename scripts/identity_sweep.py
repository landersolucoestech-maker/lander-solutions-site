from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_CSS = ROOT / "assets" / "valtren-brand.css"

SWEEP = r'''
/* VALTREN FULL-SITE SWEEP */
.visual-topbar{background:#FFFFFF!important;border-bottom-color:rgba(11,29,58,.14)!important}.visual-topbar span{background:#D4AF37!important}.visual-main{background:#FFFFFF!important}.visual-heading small,.metric-row small,.chart-label{color:#475569!important}.metric-row div,.chart-panel{background:#FFFFFF!important;border-color:rgba(11,29,58,.14)!important}.chart-bars{border-bottom-color:rgba(11,29,58,.14)!important}
.area-card>span{color:rgba(212,175,55,.28)!important}.architecture-visual{border-color:rgba(212,175,55,.30)!important;background:radial-gradient(circle,rgba(212,175,55,.24),transparent 58%)!important}.architecture-visual::before,.architecture-visual::after{border-color:rgba(212,175,55,.24)!important}.architecture-center{background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(212,175,55,.42)!important;box-shadow:0 18px 45px rgba(11,29,58,.16)!important}.orbit-item{border-color:rgba(212,175,55,.38)!important;background:rgba(11,29,58,.68)!important;color:#FFFFFF!important}
.product-card,.product-grid-light .product-card{background:#0B1D3A!important;color:#FFFFFF!important;border:1px solid rgba(212,175,55,.24)!important}.product-card p{color:rgba(255,255,255,.76)!important}.product-card a{color:#D4AF37!important}.status-badge{background:rgba(212,175,55,.12)!important;color:#D4AF37!important;border-color:rgba(212,175,55,.36)!important}.structure-grid>div{background:rgba(255,255,255,.04)!important;border-color:rgba(212,175,55,.24)!important}.structure-grid p{color:rgba(255,255,255,.76)!important}.product-identity{background:#0B1D3A!important;border-color:rgba(212,175,55,.28)!important}.product-identity small{color:rgba(255,255,255,.74)!important}.status-large{color:#D4AF37!important;border-color:rgba(212,175,55,.32)!important}
.contact-details>a,.contact-details>div{background:#FFFFFF!important;color:#0B1D3A!important;border:1px solid rgba(11,29,58,.14)!important}.contact-details>a:hover{border-color:rgba(212,175,55,.55)!important}.footer-brand p,.footer-brand small{color:rgba(255,255,255,.72)!important}
.admin-button,.message-list header button{background:#FFFFFF!important;border-color:rgba(11,29,58,.18)!important;color:#0B1D3A!important}.admin-button:hover,.message-list header button:hover{border-color:#D4AF37!important;color:#B8891F!important}.admin-image-field,.admin-empty{border-color:rgba(212,175,55,.38)!important}.admin-note,.admin-nested,.backup-card,.message-list article{background:#FFFFFF!important;color:#0B1D3A!important;border-color:rgba(11,29,58,.14)!important}.section-dark .section-title p{color:rgba(255,255,255,.76)!important}
html[data-theme="dark"] .visual-topbar,html[data-theme="dark"] .visual-main,html[data-theme="dark"] .metric-row div,html[data-theme="dark"] .chart-panel{background:#FFFFFF!important;color:#0B1D3A!important;border-color:rgba(11,29,58,.14)!important}html[data-theme="dark"] .visual-heading small,html[data-theme="dark"] .metric-row small,html[data-theme="dark"] .chart-label{color:#475569!important}html[data-theme="dark"] .product-card,html[data-theme="dark"] .product-grid-light .product-card{background:#0B1D3A!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.24)!important}html[data-theme="dark"] .product-identity{background:#0B1D3A!important}html[data-theme="dark"] .contact-details>a,html[data-theme="dark"] .contact-details>div,html[data-theme="dark"] .admin-button,html[data-theme="dark"] .message-list header button,html[data-theme="dark"] .admin-note,html[data-theme="dark"] .admin-nested,html[data-theme="dark"] .backup-card,html[data-theme="dark"] .message-list article{background:#1E1E1E!important;color:#FFFFFF!important;border-color:rgba(212,175,55,.22)!important}
'''


def sweep_identity() -> None:
    if not BRAND_CSS.exists():
        raise FileNotFoundError(BRAND_CSS)
    css = BRAND_CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN FULL-SITE SWEEP \*/.*\Z", "", css, flags=re.S)
    BRAND_CSS.write_text(css.rstrip() + "\n\n" + SWEEP.strip() + "\n", encoding="utf-8")
    print("Valtren full-site sweep aplicado.")


if __name__ == "__main__":
    sweep_identity()
