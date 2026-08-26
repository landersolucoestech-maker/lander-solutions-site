from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"


def _assert_js_syntax(source: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
            raise RuntimeError(f"Contextualização do header produziu bundle inválido: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def apply_crm_header_context_actions() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)

    app = APP.read_text(encoding="utf-8")

    # O helper compartilhado já nasce contextualizado em crm_global_header.py.
    # Este passe existe apenas como gate estrutural; não reescreve o Dashboard.
    if app.count("  function crmHeaderActions(context=''){") != 1:
        raise RuntimeError("crmHeaderActions contextualizado não encontrado exatamente uma vez")
    if app.count("${crmHeaderActions('dashboard')}") != 1:
        raise RuntimeError("Dashboard não preservou a chamada contextual emitida pelo próprio owner")
    if app.count("${crmHeaderActions(tab)}") != 1:
        raise RuntimeError("CRM não preservou a chamada contextual do header")

    forbidden = [
        "state.crmUserName || 'Administrador'",
        "state.crmUserInitials || 'AD'",
        "Usuário logado",
        "3 notificações não lidas",
        "Novo lead cadastrado",
    ]
    leaked = [token for token in forbidden if token in app]
    if leaked:
        raise RuntimeError(f"Header contextual ainda contém capacidade/identidade fictícia: {leaked}")

    _assert_js_syntax(app)
    print("Ações do header validadas por contexto; Dashboard permanece sob seu owner canônico.")
    return 1


if __name__ == "__main__":
    apply_crm_header_context_actions()
