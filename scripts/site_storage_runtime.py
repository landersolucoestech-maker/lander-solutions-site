from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
START = "  // VALTREN SAFE LOCAL STORAGE START\n"
END = "  // VALTREN SAFE LOCAL STORAGE END\n"

SAFE_STORAGE_BLOCK = r'''  // VALTREN SAFE LOCAL STORAGE START
  function safeStorageRead(key,fallback,validator){
    try {
      const raw=localStorage.getItem(key);
      if(raw==null||raw==='')return fallback;
      const parsed=JSON.parse(raw);
      if(validator&&!validator(parsed))return fallback;
      return parsed;
    } catch (_) {
      return fallback;
    }
  }

  function safeStorageWrite(key,value){
    try {
      localStorage.setItem(key,JSON.stringify(value));
      return true;
    } catch (_) {
      return false;
    }
  }
  // VALTREN SAFE LOCAL STORAGE END
'''

LOAD_CONTENT = r'''  function loadContent() {
    const validObject=(value)=>!!value&&typeof value==='object'&&!Array.isArray(value);
    const saved=safeStorageRead(CONTENT_KEY,null,validObject);
    if (saved) {
      const migratedSaved = mergeDefaults(defaultContent, saved);
      migratedSaved.services = clone(defaultContent.services);
      migratedSaved.translations = migratedSaved.translations || {};
      ['en','es'].forEach((language) => {
        migratedSaved.translations[language] = migratedSaved.translations[language] || {};
        migratedSaved.translations[language].services = clone(defaultContent.translations?.[language]?.services || {});
      });
      safeStorageWrite(CONTENT_KEY,migratedSaved);
      return migratedSaved;
    }

    const legacy=safeStorageRead(LEGACY_CONTENT_KEY,null,validObject);
    if (!legacy) return clone(defaultContent);

    const migrated = clone(defaultContent);
    if (legacy.global) {
      ['email','phone','whatsapp','instagram','linkedin','youtube'].forEach((key) => {
        if (legacy.global[key]) migrated.global[key] = legacy.global[key];
      });
    }
    if (legacy.home?.heroImage) migrated.home.heroImage = legacy.home.heroImage;
    if (Array.isArray(legacy.products)) migrated.products = legacy.products;
    if (legacy.collections) migrated.collections = mergeDefaults(migrated.collections, legacy.collections);
    if (legacy.legal) migrated.legal = mergeDefaults(migrated.legal, legacy.legal);
    safeStorageWrite(CONTENT_KEY,migrated);
    return migrated;
  }

  function saveContent(content) {
    safeStorageWrite(CONTENT_KEY,content);
    state.content = clone(content);
  }

  function loadMessages() {
    return safeStorageRead(MESSAGES_KEY,[],Array.isArray);
  }

  function saveMessages(messages) {
    return safeStorageWrite(MESSAGES_KEY,Array.isArray(messages)?messages:[]);
  }
'''

ADMIN_DATA = r'''  function adminData() {
    return `<section class="admin-panel"><h2>Backup e transferência</h2><p>Exporte o conteúdo antes de trocar de computador, navegador ou limpar os dados locais.</p><div class="backup-grid"><button class="backup-card" data-action="export-content">${icon('download')}<strong>Exportar conteúdo</strong><span>Baixa um arquivo JSON com textos e imagens.</span></button><button class="backup-card" data-action="import-content">${icon('upload')}<strong>Importar conteúdo</strong><span>Restaura um backup previamente exportado.</span></button><button class="backup-card danger" data-action="reset-content">${icon('refresh')}<strong>Restaurar padrão</strong><span>Remove as alterações locais e volta ao conteúdo inicial.</span></button></div><div class="admin-note">${icon('shield')}<div><strong>Protótipo local — autenticação desativada</strong><p>Os dados ficam somente neste navegador. Nenhuma senha ou sessão local é simulada. Para produção multiusuário, conecte um backend com autenticação e armazenamento persistente.</p></div></div></section>`;
  }
'''


def _disable_fake_admin_auth(app: str) -> str:
    app = re.sub(r"^\s*const PASSWORD_KEY = .*?;\n", "", app, count=1, flags=re.M)
    app = re.sub(r"^\s*const SESSION_KEY = .*?;\n", "", app, count=1, flags=re.M)

    app = re.sub(
        r"\n  function adminLoginPage\(\) \{.*?\n  \}\n",
        "\n",
        app,
        count=1,
        flags=re.S,
    )

    admin_data_pattern = re.compile(r"  function adminData\(\) \{.*?\n  \}\n", re.S)
    if len(list(admin_data_pattern.finditer(app))) != 1:
        raise RuntimeError("Site runtime: adminData ambíguo")
    app = admin_data_pattern.sub(ADMIN_DATA, app, count=1)

    login_guard = "    if (sessionStorage.getItem(SESSION_KEY) !== 'ok') return adminLoginPage();\n"
    if login_guard not in app:
        raise RuntimeError("Site runtime: guard de autenticação local legado não encontrado")
    app = app.replace(login_guard, "", 1)

    logout_button = '<button class="admin-preview" data-action="logout-admin">${icon(\'lock\',16)}Sair</button>'
    if logout_button not in app:
        raise RuntimeError("Site runtime: botão Sair legado não encontrado")
    app = app.replace(logout_button, "", 1)

    old_warning = '<div class="admin-warning">${icon(\'shield\')}Este CMS utiliza o armazenamento local do navegador para funcionar imediatamente. Para produção multiusuário, conecte um backend com autenticação e armazenamento persistente.</div>'
    new_warning = '<div class="admin-warning">${icon(\'shield\')}Protótipo local com autenticação desativada. O CMS usa somente o armazenamento deste navegador; nenhuma sessão ou identidade é simulada.</div>'
    if old_warning not in app:
        raise RuntimeError("Site runtime: aviso do CMS legado não encontrado")
    app = app.replace(old_warning, new_warning, 1)

    app = re.sub(r"\n\s*if \(action === 'logout-admin'\) \{.*?\}\n", "\n", app, count=1)
    app = re.sub(r"\n\s*if \(action === 'change-password'\) \{.*?\n\s*\}\n", "\n", app, count=1, flags=re.S)
    app = app.replace("    if (target.dataset.field === 'admin.newPassword') return;\n", "", 1)
    app = re.sub(
        r"\n\s*if \(event\.target\.id === 'admin-login'\) \{.*?\n\s*\}\n",
        "\n",
        app,
        count=1,
        flags=re.S,
    )

    forbidden = (
        "valtren-solutions:admin-password",
        "valtren-solutions:admin-session",
        "valtren-admin",
        "admin-login",
        "change-password",
        "logout-admin",
        "SESSION_KEY",
        "PASSWORD_KEY",
    )
    leaked = [token for token in forbidden if token in app]
    if leaked:
        raise RuntimeError(f"Site runtime: autenticação local fictícia ainda presente: {leaked}")
    return app


def apply_site_storage_runtime() -> int:
    if not APP.exists():
        raise FileNotFoundError(APP)
    app = APP.read_text(encoding="utf-8")

    app = re.sub(
        rf"\n?{re.escape(START)}.*?{re.escape(END)}",
        "\n",
        app,
        count=1,
        flags=re.S,
    )
    anchor = "  function loadLanguage() {"
    if app.count(anchor) != 1:
        raise RuntimeError(f"Site storage: âncora loadLanguage ambígua: {app.count(anchor)}")
    app = app.replace(anchor, SAFE_STORAGE_BLOCK + "\n" + anchor, 1)

    pattern = re.compile(
        r"  function loadContent\(\) \{.*?\n  \}\n\n"
        r"  function saveContent\(content\) \{.*?\n  \}\n\n"
        r"  function loadMessages\(\) \{.*?\n  \}\n\n"
        r"  function saveMessages\(messages\) \{.*?\n  \}\n",
        re.S,
    )
    matches = list(pattern.finditer(app))
    if len(matches) != 1:
        raise RuntimeError(f"Site storage: bloco de persistência base ambíguo: {len(matches)}")
    app = pattern.sub(LOAD_CONTENT, app, count=1)
    app = _disable_fake_admin_auth(app)

    forbidden = "JSON.parse(localStorage.getItem("
    if forbidden in app:
        base_window = app[: app.find("// VALTREN CRM", 0) if "// VALTREN CRM" in app else len(app)]
        if forbidden in base_window:
            raise RuntimeError("Site storage: parsing direto de localStorage permaneceu no runtime base")

    APP.write_text(app, encoding="utf-8")
    print("Persistência base e CMS local materializados sem parsing inseguro nem autenticação fictícia.")
    return 1


if __name__ == "__main__":
    apply_site_storage_runtime()
