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

    forbidden = "JSON.parse(localStorage.getItem("
    if forbidden in app:
        # Outros domínios materializados depois ainda podem possuir seu próprio owner;
        # este owner garante que a persistência base do site não reintroduza o padrão.
        base_window = app[: app.find("// VALTREN CRM", 0) if "// VALTREN CRM" in app else len(app)]
        if forbidden in base_window:
            raise RuntimeError("Site storage: parsing direto de localStorage permaneceu no runtime base")

    APP.write_text(app, encoding="utf-8")
    print("Persistência base do site materializada com leitura validada e fallback seguro.")
    return 1


if __name__ == "__main__":
    apply_site_storage_runtime()
