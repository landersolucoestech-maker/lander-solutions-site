from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
DASHBOARD_START = "  // VALTREN CRM DASHBOARD START\n"
DASHBOARD_END = "  // VALTREN CRM DASHBOARD END\n"
CSS_MARKER = "/* VALTREN CRM INTEGRATED */"

CRM_FUNCTION = r'''  function crmDashboardPage(query){
    try { if (typeof crmCanonicalEnsureFromLegacy === 'function') crmCanonicalEnsureFromLegacy(); } catch (error) { console.error('Falha ao consolidar CRM no dashboard:', error); }
    const contacts = Array.isArray(state.crmRelContacts) ? state.crmRelContacts : [];
    const leads = Array.isArray(state.crmRelLeads) ? state.crmRelLeads : [];
    const clients = contacts.filter((item)=>{
      const roles = Array.isArray(item.canonicalRoles) ? item.canonicalRoles : [];
      const segment = String(item.segment || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
      return roles.includes('customer') || segment === 'cliente';
    });
    let transactions = [];
    try {
      if (typeof crmFinanceService === 'function') transactions = crmFinanceService().data.transactions || [];
      else if (state.crmFinancialTransactions && Array.isArray(state.crmFinancialTransactions.transactions)) transactions = state.crmFinancialTransactions.transactions;
    } catch (error) { console.error('Falha ao consolidar Financeiro no dashboard:', error); }
    const posted = transactions.filter((tx)=>tx && tx.status === 'posted' && !tx.isDemo);
    const revenue = posted.filter((tx)=>tx.financialNature === 'revenue').reduce((sum,tx)=>sum + Number(tx.amount || 0),0);
    const expenses = posted.filter((tx)=>tx.financialNature === 'expense').reduce((sum,tx)=>sum + Number(tx.amount || 0),0);
    const result = revenue - expenses;
    const pendingTransactions = transactions.filter((tx)=>tx && tx.status === 'pending' && !tx.isDemo).length;
    const openLeads = leads.filter((lead)=>!['converted','convertido'].includes(String(lead.stage || '').toLowerCase())).length;
    const money = (value)=>Number(value || 0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
    const kpi = (label,value,meta='')=>`<article class="crm-kpi"><span>${label}</span><strong>${value}</strong>${meta?`<small>${meta}</small>`:''}</article>`;
    const attention = [];
    if (openLeads) attention.push(`<a href="#/crm/relationships?tab=leads"><strong>${openLeads}</strong><span>lead${openLeads===1?'':'s'} em acompanhamento</span><small>Revisar pipeline comercial</small></a>`);
    if (pendingTransactions) attention.push(`<a href="#/crm/financeiro"><strong>${pendingTransactions}</strong><span>transaç${pendingTransactions===1?'ão':'ões'} pendente${pendingTransactions===1?'':'s'}</span><small>Classificar ou lançar no Financeiro</small></a>`);
    const attentionBody = attention.length ? `<div class="crm-dashboard-attention-grid">${attention.join('')}</div>` : `<div class="crm-empty-state"><strong>Nenhuma pendência consolidada</strong><p>O dashboard exibirá aqui apenas itens reais que exigirem atenção.</p></div>`;
    const noData = !contacts.length && !leads.length && !posted.length;
    return `<div class="crm-app-shell">${crmRelSidebar('dashboard','dashboard')}<main class="crm-main"><header class="crm-topbar"><div><span>Sistema Interno</span><h1>Dashboard</h1><p>Visão objetiva dos dados reais já registrados no sistema.</p></div>${crmHeaderActions('dashboard')}</header><section class="crm-workspace crm-dashboard-workspace" aria-label="Dashboard"><div class="crm-page-header"><div><h2>Visão geral</h2><p>Indicadores essenciais de CRM e Financeiro, sem duplicar os módulos operacionais.</p></div></div><div class="crm-kpi-grid crm-dashboard-kpis">${kpi('Contatos',contacts.length)}${kpi('Leads',leads.length)}${kpi('Clientes',clients.length)}${kpi('Receitas',money(revenue),'Transações lançadas')}${kpi('Despesas',money(expenses),'Transações lançadas')}${kpi('Resultado',money(result),'Receitas − despesas')}</div>${noData?`<section class="crm-panel"><div class="crm-empty-state"><strong>Ainda não há dados operacionais</strong><p>Cadastre contatos, leads ou transações reais para alimentar esta visão. O sistema não cria números fictícios para preencher o dashboard.</p></div></section>`:''}<div class="crm-dashboard-grid"><section class="crm-panel"><div class="crm-panel-heading"><div><span>Prioridades</span><h2>O que precisa de atenção</h2></div></div>${attentionBody}</section><section class="crm-panel"><div class="crm-panel-heading"><div><span>Navegação</span><h2>Acessos principais</h2></div></div><nav class="crm-dashboard-shortcuts" aria-label="Acessos principais"><a href="#/crm/relationships">CRM<span>Contatos, clientes e leads</span></a><a href="#/crm/financeiro">Financeiro<span>Transações e conciliação operacional</span></a><a href="#/crm/negocios">Negócios<span>Produtos, serviços e unidades</span></a><a href="#/crm/juridico">Jurídico<span>Assuntos, contratos e demais owners jurídicos</span></a></nav></section></div></section></main></div>`;
  }
'''

CSS_PATCH = r'''
/* VALTREN CRM INTEGRATED */
.crm-dashboard-workspace{display:grid;gap:var(--crm-space-5,24px)}
.crm-dashboard-workspace>.crm-page-header{margin-bottom:0}
.crm-dashboard-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}
.crm-dashboard-attention-grid,.crm-dashboard-shortcuts{display:grid;gap:10px}
.crm-dashboard-attention-grid a,.crm-dashboard-shortcuts a{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;align-items:center;padding:12px;border:1px solid var(--crm-border,rgba(11,29,58,.12));border-radius:var(--crm-radius-sm,8px);color:var(--crm-text,#0b1d3a);text-decoration:none;background:var(--crm-surface,#fff)}
.crm-dashboard-attention-grid a strong{grid-row:1/3;font-size:22px}
.crm-dashboard-attention-grid a small,.crm-dashboard-shortcuts a span{grid-column:2;color:var(--crm-muted,#687386);font-size:11px}
.crm-dashboard-shortcuts a{grid-template-columns:1fr}
.crm-dashboard-shortcuts a span{grid-column:1}
@media(max-width:1200px){.crm-dashboard-grid{grid-template-columns:1fr}}
'''


def _assert_js_syntax(source: str, stage: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(temp_path)], capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sintático desconhecido").strip()
            raise RuntimeError(f"Dashboard produziu bundle inválido em {stage}: {detail}")
    finally:
        temp_path.unlink(missing_ok=True)


def _dashboard_block() -> str:
    return DASHBOARD_START + CRM_FUNCTION.rstrip() + "\n" + DASHBOARD_END


def _materialize_dashboard_function(app: str) -> str:
    block = _dashboard_block()
    start_count = app.count(DASHBOARD_START)
    end_count = app.count(DASHBOARD_END)
    if start_count == 1 and end_count == 1:
        start = app.index(DASHBOARD_START)
        end = app.index(DASHBOARD_END, start) + len(DASHBOARD_END)
        current = app[start:end]
        return app if current == block else app[:start] + block + app[end:]
    if start_count or end_count:
        raise RuntimeError(f"Marcadores do Dashboard divergentes: {start_count}/{end_count}")

    function_anchor = "  function crmDashboardPage("
    contact_anchor = "  function contactPage(query)"
    function_count = app.count(function_anchor)
    contact_count = app.count(contact_anchor)
    if function_count not in {0, 1} or contact_count != 1:
        raise RuntimeError(f"Âncoras do Dashboard inválidas: dashboard={function_count}, contactPage={contact_count}")
    contact_at = app.index(contact_anchor)
    if function_count == 1:
        start = app.index(function_anchor)
        if start >= contact_at:
            raise RuntimeError("crmDashboardPage apareceu depois da âncora contactPage")
        app = app[:start] + block + "\n" + app[contact_at:]
    else:
        app = app[:contact_at] + block + "\n" + app[contact_at:]
    return app


def _materialize_route(app: str) -> str:
    old_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage();"
    new_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query);"
    if old_route in app:
        app = app.replace(old_route, new_route)
    if new_route in app:
        return app
    if "path === '/crm/dashboard'" in app or "path==='/crm/dashboard'" in app:
        return app
    anchor = "    else if (path === '/contato') app.innerHTML = contactPage(query);"
    count = app.count(anchor)
    if count < 1:
        raise RuntimeError("Rota do Dashboard ausente e âncora de compatibilidade não encontrada")
    return app.replace(anchor, new_route + "\n" + anchor)


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


def apply_crm_dashboard() -> int:
    if not APP.exists() or not CSS.exists():
        raise FileNotFoundError("app.js ou assets/valtren-brand.css ausente")
    app = APP.read_text(encoding="utf-8")
    app = _materialize_dashboard_function(app)
    app = _materialize_route(app)
    if app.count(DASHBOARD_START) != 1 or app.count(DASHBOARD_END) != 1 or app.count("function crmDashboardPage(") != 1:
        raise RuntimeError("Dashboard canônico não ficou materializado exatamente uma vez")
    for forbidden in ("Receita Consolidada","R$ 275.000","Music OS 360</h3><p>SaaS / Plataforma","23 novas vendas","R$ 18.500 recebido","Protótipo · dados ilustrativos"):
        if forbidden in CRM_FUNCTION:
            raise RuntimeError(f"Dashboard canônico contém dado ilustrativo proibido: {forbidden}")
    _assert_js_syntax(app, "crmDashboardPage")
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    updated_css = _replace_css_block(css)
    if updated_css != css:
        CSS.write_text(updated_css, encoding="utf-8")
    print("Dashboard canônico materializado pelo owner do Dashboard, sem dados ilustrativos.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard()
