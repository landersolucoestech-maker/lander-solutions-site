from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CACHE_VERSION = "20260824-crm-rel-modal-structure-v1"

HELPERS = r'''  // VALTREN CRM RELATIONSHIP MODAL STRUCTURE HELPERS START
  function crmRelContactProfileOptions(type,category){
    const profiles = {
      pessoa_fisica: {
        'Cliente':['Artista/Banda','Empresário Artístico','Influenciador','Contratante de Show','Parceiros','Outros'],
        'Parceiro':['Empresário Artístico','Parceiro Comercial','Influenciador','Outros'],
        'Fornecedor':['Outros'],
        'Prestador de Serviços':['Advogado','A&R','Beatmaker','Compositor','Coach Vocal','Contador','Curador Musical','Designer','Diretor','Diretor de Vídeo','Editor de Vídeo','Engenheiro de Som','Fotógrafo','Jornalista','Manager','Masterizador','Mix Engineer','Motion Designer','Operador de Câmera','Produtor Executivo','Produtor Musical','Programador','Psicólogo','Outros'],
        'Investidor':['Investidor','Fundo de Investimento','Outros'],
        'Órgão':['Outros']
      },
      pessoa_juridica: {
        'Cliente':['Empresa','Marca','Contratante de Show','Produtora de Eventos','Outros'],
        'Parceiro':['Agência','Agência de Booking','Agência de Modelos','Agência de Publicidade','Distribuidora Digital','Empresa','Gravadora/Selo','Parceiro Comercial','Patrocinador','Plataforma Digital','Produtora Audiovisual','Produtora de Eventos','Outros'],
        'Fornecedor':['Banco','Cartório','Cloud Provider','Construtora','Empresa de IA','Empresa de Internet','Empresa de Som','Estúdio','Gateway de Pagamento','Hosting','Oficina Mecânica','Sala de Ensaio','Outros'],
        'Prestador de Serviços':['Produtora Audiovisual','Estúdio','Agência','Outros'],
        'Investidor':['Fundo de Investimento','Investidor','Outros'],
        'Órgão':['ABRAMUS','ECAD','INPI','Prefeitura','Outros']
      }
    };
    return profiles[type]?.[category] || ['Outros'];
  }

  function crmRelContactProfileField(type,category,value=''){
    const values = crmRelContactProfileOptions(type,category);
    const options = [['','Selecione o Perfil do Contato'], ...values.map((item) => [item,item])];
    if (value && !values.includes(value)) options.push([value,value]);
    return `<label class="crm-rel-field"><span>Perfil do Contato *</span><select name="perfil" required>${options.map(([v,l]) => `<option value="${esc(v)}" ${String(value)===String(v)?'selected':''}>${esc(l)}</option>`).join('')}</select></label>`;
  }

  function crmRelSyncContactProfileOptions(reset=false){
    const form = document.getElementById('crm-rel-form');
    if (!form || form.dataset.kind !== 'contacts') return;
    const type = form.querySelector('[name="tipo_pessoa"]')?.value || 'pessoa_fisica';
    const category = form.querySelector('[name="categoria"]')?.value || 'Cliente';
    const select = form.querySelector('[name="perfil"]');
    if (!select) return;
    const current = reset ? '' : select.value;
    const values = crmRelContactProfileOptions(type,category);
    const options = [['','Selecione o Perfil do Contato'], ...values.map((item) => [item,item])];
    if (current && !values.includes(current)) options.push([current,current]);
    select.innerHTML = options.map(([v,l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('');
    select.value = current && options.some(([v]) => v === current) ? current : '';
  }
  // VALTREN CRM RELATIONSHIP MODAL STRUCTURE HELPERS END
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"{label} não encontrado")
    return text.replace(old, new, 1)


def apply_crm_lead_origin_fix() -> int:
    app = APP.read_text(encoding="utf-8")
    app = re.sub(
        r"  // VALTREN CRM RELATIONSHIP MODAL STRUCTURE HELPERS START\n.*?  // VALTREN CRM RELATIONSHIP MODAL STRUCTURE HELPERS END\n",
        "",
        app,
        flags=re.S,
    )
    anchor = "  function crmRelFormModal(kind,mode,item){\n"
    if anchor not in app:
        raise RuntimeError("crmRelFormModal não encontrado")
    app = app.replace(anchor, HELPERS + "\n" + anchor, 1)

    app = replace_once(
        app,
        "    const lead = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',profile:'',status:'Ativo',priority:'Média',stage:'Novo',source:'',interactions:[]};",
        "    const lead = item || {tipo_pessoa:'pessoa_fisica',segment:'Cliente',status:'Ativo',priority:'Média',stage:'Novo',source:'Website',interactions:[]};",
        "defaults do Lead",
    )
    app = replace_once(app, "    const profileLabel = isContact ? 'Perfil do Contato *' : 'Perfil do Lead *';\n", "", "profileLabel")

    old_classification = "    body += crmRelSection(classificationTitle, `<div class=\"crm-rel-form-grid three\">${crmRelSelect('Tipo *','tipo_pessoa',record.tipo_pessoa || 'pessoa_fisica',[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',record.segment || 'Cliente',[['Cliente','Cliente'],['Parceiro','Parceiro'],['Fornecedor','Fornecedor'],['Prestador de Serviços','Prestador de Serviços'],['Investidor','Investidor'],['Órgão','Órgão']])}${crmRelField(profileLabel,'perfil',record.profile || '','text','required')}</div>`);"
    new_classification = "    const categoryOptions = [['Cliente','Cliente'],['Parceiro','Parceiro'],['Fornecedor','Fornecedor'],['Prestador de Serviços','Prestador de Serviços'],['Investidor','Investidor'],['Órgão','Órgão']];\n    const leadOriginOptions = [['Website','Website'],['WhatsApp','WhatsApp'],['Email','Email'],['Google','Google'],['Instagram','Instagram'],['TikTok','TikTok'],['Indicação','Indicação'],['Telefone','Telefone']];\n    if (isContact) {\n      body += crmRelSection('Classificação do Contato', `<div class=\"crm-rel-form-grid three\">${crmRelSelect('Tipo de Contato *','tipo_pessoa',record.tipo_pessoa || 'pessoa_fisica',[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',record.segment || 'Cliente',categoryOptions)}${crmRelContactProfileField(record.tipo_pessoa || 'pessoa_fisica',record.segment || 'Cliente',record.profile || '')}</div>`);\n    } else {\n      body += crmRelSection('Classificação do Lead', `<div class=\"crm-rel-form-grid two\">${crmRelSelect('Tipo de Lead *','tipo_pessoa',record.tipo_pessoa || 'pessoa_fisica',[['pessoa_fisica','Pessoa Física'],['pessoa_juridica','Pessoa Jurídica']])}${crmRelSelect('Categoria *','categoria',record.segment || 'Cliente',categoryOptions)}</div>`);\n    }"
    app = replace_once(app, old_classification, new_classification, "classificação inicial")

    pj_line = "    body += `<div class=\"crm-contact-pj\">${crmRelSection('Dados da Pessoa Jurídica', `<div class=\"crm-rel-form-grid two\">${crmRelField('Razão Social *','razao_social',record.tipo_pessoa==='pessoa_juridica'?record.name:'','text','required')}${crmRelField('Nome Fantasia','nome_fantasia',record.company || '')}${crmRelField('CNPJ','cnpj',record.cnpj || '')}${crmRelField('Email','email_pj',record.email || '','email')}${crmRelField('Instagram','instagram_pj',record.instagram || '')}${crmRelField('Telefone','telefone_pj',record.phone || '')}</div>`)}</div>`;"
    app = replace_once(
        app,
        pj_line,
        pj_line + "\n    if (!isContact) body += crmRelSection('Origem do Lead', `<div class=\"crm-rel-form-grid two\">${crmRelSelect('Origem do Lead *','origem',record.source || 'Website',leadOriginOptions)}</div>`);",
        "posição da origem do Lead",
    )

    old_view_class = "    body += crmRelSection(classificationTitle, `<div class=\"crm-rel-view-grid\">${crmRelViewRow('Tipo',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}${crmRelViewRow(isContact ? 'Perfil do Contato' : 'Perfil do Lead',item.profile)}</div>`);"
    new_view_class = "    if (isContact) body += crmRelSection('Classificação do Contato', `<div class=\"crm-rel-view-grid\">${crmRelViewRow('Tipo de Contato',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}${crmRelViewRow('Perfil do Contato',item.profile)}</div>`);\n    else body += crmRelSection('Classificação do Lead', `<div class=\"crm-rel-view-grid\">${crmRelViewRow('Tipo de Lead',item.tipo_pessoa==='pessoa_juridica'?'Pessoa Jurídica':'Pessoa Física')}${crmRelViewRow('Categoria',item.segment)}</div>`);"
    app = replace_once(app, old_view_class, new_view_class, "classificação da visualização")

    view_data = "    body += crmRelSection(item.tipo_pessoa==='pessoa_juridica'?'Dados da Pessoa Jurídica':'Dados da Pessoa Física', `<div class=\"crm-rel-view-grid\">${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Razão Social':'Nome Completo',item.name)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'Nome Fantasia':'Função',item.tipo_pessoa==='pessoa_juridica'?item.company:item.function)}${crmRelViewRow(item.tipo_pessoa==='pessoa_juridica'?'CNPJ':'CPF',item.tipo_pessoa==='pessoa_juridica'?item.cnpj:item.cpf)}${crmRelViewRow('Email',item.email)}${crmRelViewRow('Telefone',item.phone)}${crmRelViewRow('Instagram',item.instagram)}</div>`);"
    app = replace_once(app, view_data, view_data + "\n    if (!isContact) body += crmRelSection('Origem do Lead', `<div class=\"crm-rel-view-grid\">${crmRelViewRow('Origem do Lead',item.source)}</div>`);", "origem na visualização")

    profile_save = "        segment:String(data.get('categoria') || ''),profile:String(data.get('perfil') || ''),phone,email,city,"
    occurrences = app.count(profile_save)
    if occurrences < 2:
        raise RuntimeError(f"blocos de perfil no salvamento não encontrados: {occurrences}")
    first = app.find(profile_save)
    second = app.find(profile_save, first + len(profile_save))
    app = app[:second] + "        segment:String(data.get('categoria') || ''),source:String(data.get('origem') || 'Website'),phone,email,city," + app[second + len(profile_save):]

    old_toggle_end = "    form.querySelectorAll('.crm-contact-pj').forEach((el) => {\n      const show = type === 'pessoa_juridica';\n      el.hidden = !show;\n      el.querySelectorAll('input,select,textarea,button').forEach((field) => { field.disabled = !show; });\n    });\n  }"
    new_toggle_end = "    form.querySelectorAll('.crm-contact-pj').forEach((el) => {\n      const show = type === 'pessoa_juridica';\n      el.hidden = !show;\n      el.querySelectorAll('input,select,textarea,button').forEach((field) => { field.disabled = !show; });\n    });\n    if (form.dataset.kind === 'contacts') crmRelSyncContactProfileOptions(false);\n  }"
    app = replace_once(app, old_toggle_end, new_toggle_end, "toggle PF/PJ")

    old_change = "      if (event.target?.matches?.('[name=\"tipo_pessoa\"]')) crmRelToggleContactType();"
    new_change = "      if (event.target?.matches?.('[name=\"tipo_pessoa\"]')) { crmRelToggleContactType(); if (event.target.closest('#crm-rel-form')?.dataset.kind === 'contacts') crmRelSyncContactProfileOptions(true); }\n      if (event.target?.matches?.('[name=\"categoria\"]') && event.target.closest('#crm-rel-form')?.dataset.kind === 'contacts') crmRelSyncContactProfileOptions(true);"
    app = replace_once(app, old_change, new_change, "eventos da classificação")

    APP.write_text(app, encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", original)
        updated = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    print("Modais de Contato e Lead corrigidos; Origem do Lead reposicionada.")
    return 1


if __name__ == "__main__":
    apply_crm_lead_origin_fix()
