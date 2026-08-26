const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
const materialized=process.argv.includes('--materialized');
const fail=(m)=>{throw new Error(m)};
const must=(c,m)=>{if(!c)fail(m)};
const read=(name)=>fs.readFileSync(path.join(__dirname,name),'utf8');
const owner=read('crm_sidebar_architecture.py');
const relationships=read('crm_relationships_module.py');
const fidelity=read('crm_reference_fidelity_fix.js.part01')+read('crm_reference_fidelity_fix.js.part02')+read('crm_reference_fidelity_fix.js.part03')+read('crm_reference_fidelity_fix.js.part04');
const definitive=read('crm_definitive_architecture.py');
const reference=read('crm_reference_modules.py');
const rawReferenceCss=read('crm_reference_modules.css.part01')+read('crm_reference_modules.css.part02');
const materialize=read('materialize.py');
const header=read('crm_global_header.py');
const review=read('crm_product_system_review.py');
const ownsSidebar=(source)=>/^[ \t]*function[ \t]+crmRelSidebar[ \t]*[(]/m.test(source);
const ownerPayloadMatch=owner.match(/JS_BLOCK = r'''([^]*?)'''\n\nCSS_PATCH/);
must(ownerPayloadMatch,'sidebar owner payload must be statically identifiable');
const ownerPayload=ownerPayloadMatch[1];
const ownerCssMatch=owner.match(/CSS_PATCH = r'''([^]*?)'''\n\n\ndef _assert_js_syntax/);
must(ownerCssMatch,'sidebar owner CSS must be statically identifiable');
const ownerCss=ownerCssMatch[1];
must(owner.includes('VALTREN SIDEBAR ARCHITECTURE START'),'sidebar owner start marker missing');
must(owner.includes('VALTREN SIDEBAR ARCHITECTURE END'),'sidebar owner end marker missing');
must(owner.includes("function crmRelSidebar(active='relationships',sub='')"),'sidebar owner declaration missing');
must(owner.includes('if start_count==1 and end_count==1'),'sidebar owner must update existing marker block in-place');
must(owner.includes('app_changed=updated_app!=app'),'sidebar owner must detect no-op app reruns');
must(owner.includes('css_changed=updated_css!=css'),'sidebar owner must detect no-op CSS reruns');
must(owner.includes('if app_changed or css_changed:'),'sidebar owner must not rewrite cache-busters on no-op reruns');
must(!ownsSidebar(relationships),'relationships still owns sidebar');
must(!ownsSidebar(fidelity),'fidelity still owns sidebar');
must(!ownsSidebar(definitive),'definitive architecture still owns sidebar');
must(!reference.includes('crm_reference_sidebar.txt'),'reference modules still rewrites sidebar');
must(!fs.existsSync(path.join(__dirname,'crm_reference_sidebar.txt')),'dead crm_reference_sidebar.txt must be removed');
must(reference.includes('_strip_legacy_sidebar_css'),'reference modules must explicitly strip its legacy sidebar CSS');
must(rawReferenceCss.includes('.crm-nav-group'),'expected audited legacy navigation CSS missing from reference source');
must(materialize.includes('from crm_sidebar_architecture import apply_crm_sidebar_architecture'),'materialize missing sidebar owner import');
must((materialize.match(/apply_crm_sidebar_architecture\(\)/g)||[]).length===1,'materialize must call sidebar owner exactly once');
must(ownerPayload.includes("nav('#/crm/marketing','Marketing'"),'Marketing must remain first-level');
must(ownerPayload.includes("nav('#/crm/relatorios','Relatórios'"),'Reports must remain');
['ValtrenChat','MusicChat',"nav('#/crm/rh'",'Administração'].forEach((token)=>must(!ownerPayload.includes(token),`sidebar payload still contains removed module: ${token}`));
must(header.includes('crm-sidebar-toggle'),'Header missing mobile navigation toggle');
must(header.includes('@media(max-width:980px){.crm-account-copy{display:none}'),'Header missing tablet Account Menu compaction');
must(!review.includes('.crm-sidebar{position:'),'global review still positions Sidebar');
must(!review.includes('.crm-account-menu>summary'),'global review still styles Account Menu');
[
  ['.crm-sidebar{','sidebar structural container missing'],
  ['width:250px','desktop canonical sidebar width missing'],
  ['.crm-sidebar-head{','sidebar header layout missing'],
  ['.crm-brand{','sidebar brand composition missing'],
  ['.crm-brand img{','sidebar brand image sizing missing'],
  ['width:34px!important','sidebar brand explicit width missing'],
  ['height:34px!important','sidebar brand explicit height missing'],
  ['.crm-brand>span{','sidebar brand text stack missing'],
  ['flex-direction:column','sidebar vertical flex direction missing'],
  ['.crm-nav{','sidebar nav container missing'],
  ['.crm-nav>a,.crm-nav-group>summary{','sidebar main-row rule missing'],
  ['width:100%','sidebar full-width row rule missing'],
  ['.crm-nav svg,.crm-nav-group>summary svg{','sidebar icon sizing rule missing'],
  ['flex:0 0 18px','sidebar icon shrink protection missing'],
  ['.crm-nav>a.active{','sidebar active main state missing'],
  ['box-shadow:inset 3px 0 0 #D4AF37','sidebar active indicator missing'],
  ['.crm-nav-group>div{','sidebar submenu layout missing'],
  ['.crm-nav-subgroup>summary{','Contracts subgroup presentation missing'],
  ['.crm-nav-subgroup>div{','Contracts nested submenu missing'],
  ['outline:2px solid #D4AF37','sidebar focus-visible state missing'],
  ['padding-left:232px','tablet content offset missing'],
  ['.crm-sidebar{width:232px','tablet readable sidebar width missing'],
  ['transform:translateX(-104%)','mobile drawer closed state missing'],
  ['.crm-sidebar.is-open{transform:translateX(0)}','mobile drawer open state missing'],
  ['html.crm-sidebar-lock,body.crm-sidebar-lock{overflow:hidden}','mobile body lock missing']
].forEach(([token,message])=>must(ownerCss.includes(token),message));
must(!ownerCss.includes('zoom:'),'sidebar owner must not use zoom hack');
must(!ownerCss.includes('scale('),'sidebar owner must not use scale hack');
must(!/font-size:\s*[0-8](?:px|rem)/.test(ownerCss),'sidebar owner contains illegibly small font sizing');
if(materialized){
 const app=fs.readFileSync(path.join(root,'app.js'),'utf8');
 const css=fs.readFileSync(path.join(root,'assets','valtren-brand.css'),'utf8');
 const decl=(app.match(/\bfunction\s+crmRelSidebar\s*\(/g)||[]).length;
 must(decl===1,`crmRelSidebar declaration count must be 1, got ${decl}`);
 must((app.match(/VALTREN SIDEBAR ARCHITECTURE START/g)||[]).length===1,'sidebar start marker count mismatch');
 must((app.match(/VALTREN SIDEBAR ARCHITECTURE END/g)||[]).length===1,'sidebar end marker count mismatch');
 const s=app.indexOf('VALTREN SIDEBAR ARCHITECTURE START');
 const e=app.indexOf('VALTREN SIDEBAR ARCHITECTURE END',s);
 const block=app.slice(s,e);
 ['ValtrenChat','MusicChat','>RH<','Administração'].forEach((token)=>must(!block.includes(token),`removed module leaked into materialized sidebar: ${token}`));
 ['Marketing','Relatórios','Configurações','Negócios','Jurídico','Financeiro'].forEach((token)=>must(block.includes(token),`required sidebar module missing: ${token}`));
 must(app.includes("if(path==='/crm/valtrenchat'||path==='/crm/musicchat')return crmLegacyRoute('#/crm/configuracoes?tab=integracoes',crmCanonicalSettingsPage);"),'ValtrenChat legacy route missing integration redirect');
 must(app.includes("if(path==='/crm/rh')return crmArchitecturePlaceholderPage('','hr','RH'"),'RH compatibility route missing honest placeholder');
 must(app.includes("if(path.startsWith('/crm/marketing'))return crmMarketingUnavailablePage();"),'Marketing route must use unavailable/non-simulated workspace');
 must(app.includes("if(path==='/crm/administracao'||path==='/crm/administracao/patrimonio-licencas')return crmArchitecturePlaceholderPage('','admin','Administração'"),'Administration compatibility route missing honest placeholder');
 must(!/function\s+crmRefValtrenChatPage\s*\(/.test(app),'dead ValtrenChat page declaration survived');
 must(!/function\s+crmRefMusicChatPage\s*\(/.test(app),'dead MusicChat alias survived');
 ['crmRefCampaignsPage','crmRefCalendarPage','crmRefMetricsPage','crmRefBriefingsPage','crmRefTasksPage'].forEach((fn)=>must(!new RegExp(`function\\s+${fn}\\s*\\(`).test(app),`dead Marketing operational function survived: ${fn}`));
 must((css.match(/\/\* VALTREN SIDEBAR ARCHITECTURE \*\//g)||[]).length===1,'sidebar CSS owner marker must exist exactly once');
 const cssStart=css.indexOf('/* VALTREN SIDEBAR ARCHITECTURE */');
 const cssNext=css.indexOf('\n/* ',cssStart+1);
 const sidebarCss=css.slice(cssStart,cssNext<0?css.length:cssNext);
 ['.crm-brand img{','.crm-nav{','.crm-nav>a.active{','.crm-nav-group>div{','.crm-nav-subgroup>div{','padding-left:232px','transform:translateX(-104%)'].forEach((token)=>must(sidebarCss.includes(token),`materialized sidebar CSS missing structural token: ${token}`));
 const refStart=css.indexOf('/* VALTREN CRM REFERENCE MODULES */');
 must(refStart>=0,'materialized Reference Modules CSS marker missing');
 const refNext=css.indexOf('\n/* ',refStart+1);
 const refCss=css.slice(refStart,refNext<0?css.length:refNext);
 must(!refCss.includes('.crm-nav-group'),'Reference Modules materialized block still styles canonical sidebar groups');
 must(!refCss.includes('.crm-nav-subgroup'),'Reference Modules materialized block still styles canonical sidebar subgroup');
 const critical=['crmRelSidebar','crmHeaderActions','crmDashboardPage','crmReferenceRoute'];
 const conflicts=[];
 for(const fn of critical){
   const count=(app.match(new RegExp(`\\bfunction\\s+${fn}\\s*\\(`,'g'))||[]).length;
   if(count!==1)conflicts.push(`${fn}:${count}`);
 }
 must(conflicts.length===0,`critical global ownership duplicates: ${conflicts.join(', ')}`);
 const declarations=[...app.matchAll(/\bfunction\s+(crm[A-Za-z0-9_$]+)\s*\(/g)].map((match)=>match[1]);
 const counts=declarations.reduce((acc,name)=>(acc[name]=(acc[name]||0)+1,acc),{});
 const duplicates=Object.entries(counts).filter(([,count])=>count>1).sort((a,b)=>b[1]-a[1]);
 console.log('crm global duplicate declaration sweep:',duplicates.length?duplicates.map(([name,count])=>`${name}:${count}`).join(', '):'none');
}
console.log(`sidebar-architecture: PASS${materialized?' (materialized)':''}`);
