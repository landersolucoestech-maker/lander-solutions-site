from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260826-crm-global-header-v2"
JS_START = "  // VALTREN CRM GLOBAL HEADER START\n"
JS_END = "  // VALTREN CRM GLOBAL HEADER END\n"
DASHBOARD_START = "  // VALTREN CRM DASHBOARD START\n"
CSS_MARKER = "/* VALTREN CRM GLOBAL HEADER */"

HELPERS = r'''  // VALTREN CRM GLOBAL HEADER START
  function crmHeaderActions(context=''){
    const create = context === 'contacts'
      ? `<button class="crm-header-create" type="button" data-action="crm-rel-create" data-kind="contacts">${icon('plus',15)}<span>Novo Contato</span></button>`
      : context === 'leads'
        ? `<button class="crm-header-create" type="button" data-action="crm-rel-create" data-kind="leads">${icon('plus',15)}<span>Novo Lead</span></button>`
        : '';
    return `<div class="crm-header-actions">${create}<details class="crm-account-menu"><summary aria-label="Menu da conta"><span class="crm-account-icon" aria-hidden="true">${icon('user',16)}</span><span class="crm-account-copy"><strong>Conta</strong><small>Autenticação desativada</small></span><span class="crm-account-chevron" aria-hidden="true">⌄</span></summary><div class="crm-account-popover"><strong>Sem sessão ativa</strong><p>Este ambiente não possui autenticação ou usuário conectado. Nenhuma identidade é simulada.</p><a href="#/crm/configuracoes">Configurações</a></div></details></div>`;
  }

  function crmHeaderCloseMenus(){
    document.querySelectorAll('.crm-account-menu[open]').forEach((menu)=>menu.removeAttribute('open'));
  }
  // VALTREN CRM GLOBAL HEADER END
'''

CSS_PATCH = r'''
/* VALTREN CRM GLOBAL HEADER */
.crm-app-shell .crm-topbar{position:relative;z-index:80;overflow:visible}
.crm-header-actions{margin-left:auto;display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:0}
.crm-header-create{min-height:38px;border-radius:8px;padding:0 12px;border:0;display:inline-flex;align-items:center;justify-content:center;gap:7px;font:inherit;font-weight:700;cursor:pointer;white-space:nowrap}
.crm-account-menu{position:relative}
.crm-account-menu>summary{list-style:none;cursor:pointer}
.crm-account-menu>summary::-webkit-details-marker{display:none}
.crm-account-popover{position:absolute;right:0;top:calc(100% + 8px);z-index:500}
@media(max-width:760px){.crm-header-actions{width:100%;justify-content:flex-start;flex-wrap:wrap;margin-left:0}}
'''


def _assert_js_syntax(source: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
            raise RuntimeError(f"Header global produziu bundle inválido: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def _materialize_helpers(app: str) -> str:
    start_count = app.count(JS_START)
    end_count = app.count(JS_END)
    desired = HELPERS.rstrip() + "\n"
    if start_count == 1 and end_count == 1:
        start = app.index(JS_START)
        end = app.index(JS_END, start) + len(JS_END)
        current = app[start:end]
        return app if current == desired else app[:start] + desired + app[end:]
    if start_count or end_count:
        raise RuntimeError(f"Marcadores do header global divergentes: {start_count}/{end_count}")
    if app.count(DASHBOARD_START) != 1:
        raise RuntimeError(f"Âncora canônica do Dashboard divergente: {app.count(DASHBOARD_START)}")
    at = app.index(DASHBOARD_START)
    return app[:at] + desired + "\n" + app[at:]


def _materialize_crm_header(app: str) -> str:
    old_crm = '''        <header class="crm-topbar">\n          <div><span>CRM Integrado</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n        </header>'''
    new_crm = '''        <header class="crm-topbar">\n          <div><span>Sistema Interno</span><h1>CRM</h1><p>Relacionamentos comerciais e contatos estratégicos</p></div>\n          ${crmHeaderActions(tab)}\n        </header>'''
    old_count = app.count(old_crm)
    new_count = app.count(new_crm)
    if old_count == 1 and new_count == 0:
        return app.replace(old_crm, new_crm, 1)
    if old_count == 0 and new_count == 1:
        return app
    raise RuntimeError(f"Header CRM divergente: legado={old_count}, canônico={new_count}")


def _remove_local_create_button(app: str) -> str:
    pattern = r'\n\s*<button class="crm-rel-primary" type="button" data-action="crm-rel-create" data-kind="\$\{tab\}">\$\{icon\(\'plus\',16\)\} \$\{isContacts \? \'Novo Contato\' : \'Novo Lead\'\}</button>'
    app, count = re.subn(pattern, "", app, count=1)
    if count == 1:
        return app
    if 'class="crm-rel-primary" type="button" data-action="crm-rel-create"' not in app:
        return app
    raise RuntimeError(f"Botão local de criação do CRM divergente: {count}")


def _replace_css_block(css: str) -> str:
    desired = CSS_PATCH.strip()
    marker_at = css.find(CSS_MARKER)
    if marker_at < 0:
        return css.rstrip() + "\n\n" + desired + "\n"
    next_marker = css.find("\n/* ", marker_at + len(CSS_MARKER))
    end = len(css) if next_marker < 0 else next_marker + 1
    current = css[marker_at:end].strip()
    if current == desired:
        return css
    prefix = css[:marker_at].rstrip()
    suffix = css[end:].lstrip("\n")
    return prefix + "\n\n" + desired + "\n" + ("\n" + suffix if suffix else "")


def apply_crm_global_header() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    app = _materialize_helpers(app)

    # Dashboard pertence exclusivamente a crm_dashboard_module.py. Este materializador
    # apenas valida a presença da chamada de header já emitida pelo owner.
    if app.count("${crmHeaderActions('dashboard')}") != 1:
        raise RuntimeError("Dashboard não chegou com header canônico do próprio owner")

    app = _materialize_crm_header(app)
    app = _remove_local_create_button(app)
    _assert_js_syntax(app)
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css_block(css)
    if updated_css != css:
        CSS.write_text(updated_css, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CSS_VERSION}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Header compartilhado do Sistema Interno materializado sem assumir ownership do Dashboard e sem identidade/notificações fictícias.")
    return 1


if __name__ == "__main__":
    apply_crm_global_header()
