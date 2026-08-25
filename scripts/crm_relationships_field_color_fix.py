from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / 'assets' / 'valtren-brand.css'
VERSION = '20260824-crm-field-colors-v1'
MARKER = '/* VALTREN CRM FIELD COLOR FIX */'

PATCH = '''
/* VALTREN CRM FIELD COLOR FIX */
.crm-rel-toolbar .crm-rel-search,
.crm-rel-toolbar .crm-rel-search input,
.crm-rel-toolbar #crm-rel-filter,
#crm-rel-modal-root .crm-rel-modal input:not([type="checkbox"]):not([type="file"]),
#crm-rel-modal-root .crm-rel-modal select,
#crm-rel-modal-root .crm-rel-modal textarea{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0B1D3A!important;
  border-color:rgba(11,29,58,.16)!important;
  box-shadow:none!important;
}
.crm-rel-toolbar .crm-rel-search input{border:0!important;}
.crm-rel-toolbar .crm-rel-search input::placeholder,
#crm-rel-modal-root .crm-rel-modal input::placeholder,
#crm-rel-modal-root .crm-rel-modal textarea::placeholder{
  color:#8A95A4!important;
  opacity:1!important;
}
.crm-rel-toolbar #crm-rel-filter option,
#crm-rel-modal-root .crm-rel-modal select option{
  background:#FFFFFF!important;
  color:#0B1D3A!important;
}
.crm-rel-toolbar .crm-rel-search:focus-within,
.crm-rel-toolbar #crm-rel-filter:focus,
#crm-rel-modal-root .crm-rel-modal input:focus,
#crm-rel-modal-root .crm-rel-modal select:focus,
#crm-rel-modal-root .crm-rel-modal textarea:focus{
  border-color:#D4AF37!important;
  box-shadow:0 0 0 2px rgba(212,175,55,.14)!important;
  outline:none!important;
}
'''

def apply_crm_relationships_field_color_fix():
    css = CSS.read_text(encoding='utf-8')
    css = re.sub(r'\n?/\* VALTREN CRM FIELD COLOR FIX \*/.*\Z', '', css, flags=re.S)
    CSS.write_text(css.rstrip() + '\n\n' + PATCH.strip() + '\n', encoding='utf-8')
    for path in ROOT.rglob('*.html'):
        rel = path.relative_to(ROOT)
        if any(part in {'.git','.bootstrap','node_modules','scripts'} for part in rel.parts):
            continue
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?', f'valtren-brand.css?v={VERSION}', text)
        path.write_text(text, encoding='utf-8')
    return 1

if __name__ == '__main__':
    apply_crm_relationships_field_color_fix()
