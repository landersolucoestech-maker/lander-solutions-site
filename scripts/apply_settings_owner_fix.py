from pathlib import Path

p=Path('scripts/crm_definitive_architecture.py')
text=p.read_text(encoding='utf-8')
anchor="  if(!window.__valtrenCanonicalAccountMenuBound){\n"
handler="""  if(!window.__valtrenCanonicalSettingsTabsBound){
    window.__valtrenCanonicalSettingsTabsBound=true;
    document.addEventListener('click',(event)=>{
      const target=event.target.closest('[data-action="crm-ref-settings-tab"]');
      if(!target)return;
      event.preventDefault();
      const next=target.dataset.tab||'empresa';
      location.hash=`#/crm/configuracoes?tab=${encodeURIComponent(next)}`;
    });
  }

"""
if handler not in text:
    if text.count(anchor)!=1:
        raise RuntimeError(f'account menu anchor count={text.count(anchor)}')
    text=text.replace(anchor,handler+anchor,1)
legacy="""    old_settings_handler = "if(a==='crm-ref-settings-tab'){state.crmRefSettingsTab=t.dataset.tab;renderCurrentWithoutReset();return;}"
    new_settings_handler = "if(a==='crm-ref-settings-tab'){const next=t.dataset.tab;if(routeInfo().path==='/crm/configuracoes'){location.hash=`#/crm/configuracoes?tab=${encodeURIComponent(next)}`;return;}state.crmRefSettingsTab=next;renderCurrentWithoutReset();return;}"
    if old_settings_handler not in app:
        raise RuntimeError("Handler de tabs de Configurações não encontrado")
    app = app.replace(old_settings_handler, new_settings_handler, 1)

"""
if legacy in text:
    text=text.replace(legacy,'',1)
elif 'Handler de tabs de Configurações não encontrado' in text:
    raise RuntimeError('legacy settings handler block diverged')
old_validation="""    if "#/crm/configuracoes?tab=${encodeURIComponent(next)}" not in new_settings_handler:
        raise RuntimeError("Handler de deep link das abas de Configurações ausente")
"""
new_validation="""    if "window.__valtrenCanonicalSettingsTabsBound" not in JS_BLOCK or "#/crm/configuracoes?tab=${encodeURIComponent(next)}" not in JS_BLOCK:
        raise RuntimeError("Handler canônico de deep link das abas de Configurações ausente")
"""
if old_validation in text:
    text=text.replace(old_validation,new_validation,1)
elif new_validation not in text:
    raise RuntimeError('settings validation block diverged')
p.write_text(text,encoding='utf-8')
print('Settings tab handler moved into canonical architecture owner.')
