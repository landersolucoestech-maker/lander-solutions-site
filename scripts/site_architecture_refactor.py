from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT/'app.js'; CONTENT = ROOT/'content.js'; CSS = ROOT/'assets'/'valtren-brand.css'

NAV = {
'      "solutions": "Soluções",\n      "products": "Produtos",\n      "projects": "Projetos",\n      "portfolio": "Portfólio",\n      "content": "Conteúdos",':'      "products": "Produtos",\n      "cases": "Cases",\n      "content": "Blog",',
'      "solutions": "Solutions",\n      "products": "Products",\n      "projects": "Projects",\n      "portfolio": "Portfolio",\n      "content": "Insights",':'      "products": "Products",\n      "cases": "Cases",\n      "content": "Blog",',
'      "solutions": "Soluciones",\n      "products": "Productos",\n      "projects": "Proyectos",\n      "portfolio": "Portafolio",\n      "content": "Contenidos",':'      "products": "Productos",\n      "cases": "Casos",\n      "content": "Blog",',
}

HEADER_FOOTER = r'''  function header() {
    const c = localizedContent();
    const path = routeInfo().path;
    const nav = [['/empresa',tr('nav.company')],['/servicos',tr('nav.services')],['/produtos',tr('nav.products')],['/cases',tr('nav.cases')],['/blog',tr('nav.content')]];
    const categoryColumns = localizedCategories().map((category) => {
      const items = c.services.filter((service) => service.visible && service.category === category.key).slice(0,6).map((service) => link(`/servicos/${service.slug}`,esc(service.title))).join('');
      return items ? `<div><strong>${esc(category.name)}</strong>${items}</div>` : '';
    }).join('');
    const desktopLinks = nav.map(([href,label]) => href === '/servicos'
      ? `<div class="nav-dropdown"><button type="button" class="${path === '/servicos' || path.startsWith('/servicos/') ? 'active' : ''}" data-action="toggle-services">${esc(label)} <span>⌄</span></button>${state.servicesOpen ? `<div class="mega-menu">${categoryColumns}${link('/servicos',`${esc(tr('allServices'))} ${icon('arrow',14)}`,'mega-all')}</div>` : ''}</div>`
      : link(href,label,path === href || path.startsWith(`${href}/`) ? 'active' : '')).join('');
    const mobileLinks = [...nav,['/contato',tr('nav.contact')]].map(([href,label]) => link(href,label,path === href || path.startsWith(`${href}/`) ? 'active' : '')).join('');
    const logo = 'assets/valtren-logo.svg?v=20260824-white-wordmark-v3';
    return `<header class="site-header"><div class="container header-inner"><a class="brand" href="#/" aria-label="Valtren Solutions"><img src="${logo}" alt="Valtren Solutions"></a><nav class="desktop-nav" aria-label="${esc(tr('nav.services'))}">${desktopLinks}</nav><div class="header-actions">${preferenceControls()}${link('/contato',tr('nav.contact'),'button button-small')}<button class="menu-button" type="button" data-action="toggle-menu" aria-label="Menu">${icon(state.mobileOpen ? 'close' : 'menu')}</button></div></div>${state.mobileOpen ? `<nav class="mobile-nav container">${mobileLinks}${preferenceControls(true)}</nav>` : ''}</header>`;
  }

  function footer() {
    const c = localizedContent();
    const services = c.services.filter((service) => service.visible).slice(0,5);
    const contactLinks = [link('/contato',tr('talk')),c.global.email ? `<a href="mailto:${esc(c.global.email)}">${esc(c.global.email)}</a>`:'',c.global.whatsapp ? `<a href="${safeUrl(c.global.whatsapp)}" target="_blank" rel="noreferrer">WhatsApp</a>`:''].join('');
    return `<footer class="site-footer"><div class="container footer-grid"><div class="footer-brand"><img src="assets/valtren-logo.svg?v=20260824-white-wordmark-v3" alt="Valtren Solutions"><p>${esc(c.global.technologyPositioning)}</p><small>© ${new Date().getFullYear()} Valtren Solutions. ${esc(tr('rights'))}<br>${link('/privacidade',tr('privacy'))} · ${link('/termos',tr('terms'))}</small></div><div><h3>${esc(tr('nav.services'))}</h3>${services.map((service) => link(`/servicos/${service.slug}`,esc(service.title))).join('')}</div><div><h3>${esc(tr('nav.company'))}</h3>${link('/empresa',tr('who'))}${link('/produtos',tr('nav.products'))}${link('/cases',tr('nav.cases'))}${link('/blog',tr('nav.content'))}</div><div><h3>${esc(tr('nav.contact'))}</h3>${contactLinks}</div></div></footer>`;
  }
'''

COLLECTION = r'''  function collectionPage(type,title,intro){const c=localizedContent();const legacy=type==='cases'?[...(c.collections?.projects||[]),...(c.collections?.portfolio||[]),...(c.collections?.clients||[])]:[];const items=type==='cases'?[...(c.collections?.cases||[]),...legacy]:(c.collections?.posts||[]);const visible=items.filter((item)=>item.visible!==false);const localizedTitle=type==='cases'?tr('nav.cases'):tr('nav.content');if(!visible.length)return layout(`${pageHero(String(localizedTitle).toUpperCase(),`${localizedTitle} — Valtren Solutions`,intro)}<section class="section"><div class="container empty-state"><div>${icon('layers',58)}<h2>${esc(tr('emptyTitle'))}</h2><p>${esc(tr('emptyText'))}</p>${link('/contato',tr('talk'),'button')}</div></div></section>`);return layout(`${pageHero(String(localizedTitle).toUpperCase(),`${localizedTitle} — Valtren Solutions`,intro)}<section class="section"><div class="container collection-grid">${visible.map((item)=>`<article class="collection-card">${item.image?`<img src="${esc(item.image)}" alt="${esc(item.title)}">`:`<div class="collection-placeholder">${icon('image',38)}</div>`}<div><span>${esc(item.category||localizedTitle)}</span><h3>${esc(item.title)}</h3><p>${esc(item.summary||item.description||'')}</p>${type==='cases'&&item.challenge?`<p><strong>Desafio:</strong> ${esc(item.challenge)}</p>`:''}${type==='cases'&&item.solution?`<p><strong>Solução:</strong> ${esc(item.solution)}</p>`:''}${type==='cases'&&item.results?`<p><strong>Resultados:</strong> ${esc(item.results)}</p>`:''}${item.link?`<a href="${safeUrl(item.link)}" target="_blank" rel="noreferrer">${esc(tr('open'))} ${icon('arrow',16)}</a>`:''}</div></article>`).join('')}</div></section>`);}'''

ROUTES_A = r'''    else if (path === '/solucoes') { location.replace('#/servicos'); return; }
    else if (path === '/produtos') app.innerHTML = productsPage();
    else if (path.startsWith('/produtos/')) app.innerHTML = productDetailPage(decodeURIComponent(path.split('/')[2] || ''));
    else if (path === '/cases') app.innerHTML = collectionPage('cases','Cases','Trabalhos realizados, desafios, soluções desenvolvidas e resultados alcançados.');
    else if (path === '/blog') app.innerHTML = collectionPage('posts','Blog','Artigos, análises e materiais produzidos pela Valtren Solutions.');
    else if (['/projetos','/portfolio','/clientes'].includes(path)) { location.replace('#/cases'); return; }
    else if (path === '/conteudos') { location.replace('#/blog'); return; }'''
ROUTES_B = ROUTES_A.replace("decodeURIComponent(path.split('/')[2] || '')", "path.split('/')[2] || ''")

CSS_PATCH = r'''
/* VALTREN INFORMATION ARCHITECTURE */
.site-footer .footer-grid{grid-template-columns:1.6fr repeat(3,1fr)!important}.site-footer .footer-brand small a{display:inline!important;margin:0!important}
.collection-card strong{color:#0B1D3A}html[data-theme="dark"] .collection-card strong{color:#D4AF37}
@media(max-width:900px){.site-footer .footer-grid{grid-template-columns:1fr 1fr!important}}@media(max-width:640px){.site-footer .footer-grid{grid-template-columns:1fr!important}}
'''

def one(text, old, new, label):
    if old not in text: raise RuntimeError(f'architecture target missing: {label}')
    return text.replace(old,new,1)

def refactor_site_architecture():
    app=APP.read_text(encoding='utf-8')
    for old,new in NAV.items(): app=one(app,old,new,'navigation labels')
    app=re.sub(r"  function header\(\) \{.*?\n  \}\n\n  function footer\(\) \{.*?\n  \}\n",HEADER_FOOTER,app,count=1,flags=re.S)
    app=app.replace("    collectionType: 'projects',","    collectionType: 'cases',")
    app=app.replace("${link('/solucoes',`${esc(tr('techAction'))} ${icon('arrow',18)}`,'button')}","${link('/servicos',`${esc(tr('techAction'))} ${icon('arrow',18)}`,'button')}")
    app=re.sub(r"  function collectionPage\(type,title,intro\)\{.*?\}\n",COLLECTION+'\n',app,count=1)
    app=one(app,"    return {projects:'Projetos',portfolio:'Portfólio',clients:'Clientes',posts:'Conteúdos'}[type] || type;","    return {cases:'Cases',posts:'Blog'}[type] || type;",'collection labels')
    app=one(app,"    if (!c.collections) c.collections = {projects:[],portfolio:[],clients:[],posts:[]};","    if (!c.collections) c.collections = {cases:[],posts:[]};\n    if (!Array.isArray(c.collections.cases)) c.collections.cases = [...(c.collections.projects||[]),...(c.collections.portfolio||[]),...(c.collections.clients||[])];\n    if (!Array.isArray(c.collections.posts)) c.collections.posts = [];",'admin collections')
    app=one(app,"${['projects','portfolio','clients','posts'].map((type) =>","${['cases','posts'].map((type) =>",'admin options')
    app=one(app,"${selected ? `<div class=\"admin-grid\">${field('Título',`${base}.title`,selected.title)}${field('Categoria ou tipo',`${base}.category`,selected.category || '')}${field('Link externo',`${base}.link`,selected.link || '')}${selectField('Visibilidade',`${base}.visible`,selected.visible !== false,[{value:true,label:'Publicado'},{value:false,label:'Oculto'}])}</div>${textarea('Descrição',`${base}.description`,selected.description || '')}${imageField('Imagem',`${base}.image`,selected.image || '')}<div class=\"admin-actions\">","${selected ? `<div class=\"admin-grid\">${field('Título',`${base}.title`,selected.title)}${field('Categoria ou tipo',`${base}.category`,selected.category || '')}${field('Link externo',`${base}.link`,selected.link || '')}${selectField('Visibilidade',`${base}.visible`,selected.visible !== false,[{value:true,label:'Publicado'},{value:false,label:'Oculto'}])}</div>${textarea('Resumo',`${base}.summary`,selected.summary || selected.description || '')}${state.collectionType === 'cases' ? `${textarea('Contexto / descrição',`${base}.description`,selected.description || '')}${textarea('Desafio',`${base}.challenge`,selected.challenge || '')}${textarea('Solução desenvolvida',`${base}.solution`,selected.solution || '')}${textarea('Resultados alcançados',`${base}.results`,selected.results || '')}` : `${textarea('Conteúdo do artigo',`${base}.description`,selected.description || '',16)}`}${imageField('Imagem',`${base}.image`,selected.image || '')}<div class=\"admin-actions\">",'admin fields')
    app=one(app,"      state.adminDraft.collections[state.collectionType].push({id,title:'Novo item',description:'Descrição do item.',category:collectionLabel(state.collectionType),image:'',link:'',visible:false});","      state.adminDraft.collections[state.collectionType].push(state.collectionType === 'cases' ? {id,title:'Novo case',summary:'Resumo do case.',description:'Contexto do trabalho.',challenge:'',solution:'',results:'',category:'Case',image:'',link:'',visible:false} : {id,title:'Novo artigo',summary:'Resumo do artigo.',description:'Conteúdo do artigo.',category:'Blog',image:'',link:'',visible:false});",'new items')
    oldA="""    else if (path === '/solucoes') app.innerHTML = servicesPage(true);\n    else if (path === '/produtos') app.innerHTML = productsPage();\n    else if (path.startsWith('/produtos/')) app.innerHTML = productDetailPage(decodeURIComponent(path.split('/')[2] || ''));\n    else if (path === '/projetos') app.innerHTML = collectionPage('projects','Projetos','Projetos e estudos de caso serão publicados somente após cadastro e autorização.');\n    else if (path === '/portfolio') app.innerHTML = collectionPage('portfolio','Portfólio','Trabalhos realizados serão apresentados com dados reais e autorização de divulgação.');\n    else if (path === '/clientes') app.innerHTML = collectionPage('clients','Clientes','Logotipos e informações de clientes serão exibidos somente com autorização.');\n    else if (path === '/conteudos') app.innerHTML = collectionPage('posts','Conteúdos','Artigos, análises e materiais institucionais serão publicados nesta área.');"""
    oldB=oldA.replace("decodeURIComponent(path.split('/')[2] || '')","path.split('/')[2] || ''")
    app=one(app,oldA,ROUTES_A,'routes')
    app=one(app,oldB,ROUTES_B,'routes no reset')
    APP.write_text(app,encoding='utf-8')

    content=CONTENT.read_text(encoding='utf-8')
    content=one(content,'  "collections": {\n    "projects": [],\n    "portfolio": [],\n    "clients": [],\n    "posts": []\n  },','  "collections": {\n    "cases": [],\n    "posts": []\n  },','default collections')
    CONTENT.write_text(content,encoding='utf-8')

    css=CSS.read_text(encoding='utf-8')
    css=re.sub(r"\n?/\* VALTREN INFORMATION ARCHITECTURE \*/.*\Z","",css,flags=re.S)
    CSS.write_text(css.rstrip()+'\n\n'+CSS_PATCH.strip()+'\n',encoding='utf-8')
    print('Arquitetura comercial Valtren aplicada.')

if __name__=='__main__': refactor_site_architecture()
