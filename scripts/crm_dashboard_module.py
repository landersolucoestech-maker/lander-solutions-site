from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CSS_VERSION = "20260824-crm-dashboard-executive-v1"
MARKER = "/* VALTREN CRM INTEGRATED */"

CRM_FUNCTION = r'''  function crmDashboardPage(query){
    const view = query?.get('view') || 'overview';
    const activeView = ['overview','services','ventures'].includes(view) ? view : 'overview';
    const tab = (key,label) => `<a class="${activeView === key ? 'active' : ''}" href="#/crm/dashboard?view=${key}">${label}</a>`;
    const money = (label,value,note='') => `<article class="crm-kpi"><span>${label}</span><strong>${value}</strong>${note ? `<small>${note}</small>` : ''}</article>`;
    const metric = (label,value) => `<div class="crm-mini-metric"><span>${label}</span><strong>${value}</strong></div>`;
    const stage = (name,status,cls) => `<div class="crm-stage-row"><div><strong>${name}</strong><span class="crm-stage ${cls}">${status}</span></div><div class="crm-stage-track" aria-hidden="true"><i class="${cls}"></i></div></div>`;
    const activity = (area,text,value='') => `<li><span>${area}</span><div><strong>${text}</strong>${value ? `<small>${value}</small>` : ''}</div></li>`;

    const kpis = `<div class="crm-kpi-grid">
      ${money('Receita Consolidada','R$ 275.000','Serviços + receita atribuída à Valtren nos produtos')}
      ${money('Resultado Líquido','R$ 82.500','Exemplo informado para o protótipo')}
      ${money('Receita de Serviços','R$ 180.000')}
      ${money('Receita de Produtos','R$ 95.000','Parcela econômica atribuída à Valtren')}
      ${money('Receita Recorrente','R$ 72.000')}
      ${money('Valores a Receber','R$ 38.400')}
    </div>`;

    const revenueComposition = `<section class="crm-panel crm-revenue-panel">
      <div class="crm-panel-heading"><div><span>Composição da receita</span><h2>Receita total da Valtren</h2></div><strong class="crm-panel-total">R$ 275.000</strong></div>
      <div class="crm-split-bars">
        <div><header><span>Prestação de Serviços</span><strong>R$ 180.000</strong></header><div class="crm-bar"><i style="width:65.45%"></i></div></div>
        <div><header><span>Produtos & Ventures</span><strong>R$ 95.000</strong></header><div class="crm-bar"><i style="width:34.55%"></i></div></div>
      </div>
      <div class="crm-rule-note"><strong>Regra de consolidação</strong><p>Produtos com sócios não entram pelo faturamento bruto integral. O dashboard consolida a parcela econômica atribuída à Valtren.</p></div>
      <div class="crm-product-attribution"><div><strong>Music OS 360</strong><span>Receita bruta: R$ 100.000</span></div><div><span>Participação Valtren</span><strong>60%</strong></div><div><span>Receita atribuída à Valtren</span><strong>R$ 60.000</strong></div></div>
    </section>`;

    const servicesSummary = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Prestação de Serviços</span><h2>Resumo da operação</h2></div><strong class="crm-panel-total">R$ 180.000</strong></div>
      <div class="crm-mini-grid">
        ${metric('Projetos ativos','14')}
        ${metric('Clientes ativos','23')}
        ${metric('Propostas abertas','8')}
        ${metric('Contratos ativos','17')}
        ${metric('Contas a receber','R$ 31.000')}
      </div>
      <div class="crm-service-detail-grid">
        <div class="crm-chart-placeholder">
          <div class="crm-subheading"><span>Receita de Serviços</span><strong>Últimos 12 meses</strong></div>
          <div class="crm-chart-empty"><p>O gráfico será alimentado pelos dados mensais reais do financeiro.</p></div>
        </div>
        <div class="crm-ranking-placeholder">
          <div class="crm-subheading"><span>Principais serviços</span><strong>Por faturamento</strong></div>
          <div class="crm-ranking-empty"><p>O ranking será calculado com base nos serviços cadastrados e no faturamento real.</p></div>
        </div>
      </div>
    </section>`;

    const venturesCards = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Produtos & Ventures</span><h2>Portfólio de produtos</h2></div></div>
      <div class="crm-venture-grid">
        <article class="crm-venture-card">
          <header><div><span class="crm-status active">Ativo</span><h3>Music OS 360</h3><p>SaaS / Plataforma</p></div><strong>60%</strong></header>
          <dl><div><dt>Receita</dt><dd>R$ 87.300</dd></div><div><dt>Despesas</dt><dd>R$ 29.400</dd></div><div><dt>Lucro</dt><dd>R$ 57.900</dd></div><div class="accent"><dt>Resultado Valtren</dt><dd>R$ 34.740</dd></div><div><dt>MRR</dt><dd>R$ 21.500</dd></div><div><dt>Assinantes</dt><dd>426</dd></div></dl>
        </article>
        <article class="crm-venture-card">
          <header><div><span class="crm-status development">Desenvolvimento</span><h3>Vivendo da Música</h3><p>Produto digital</p></div><strong>100%</strong></header>
          <dl><div><dt>Receita</dt><dd>R$ 12.800</dd></div><div><dt>Despesas</dt><dd>R$ 18.500</dd></div><div class="negative"><dt>Resultado</dt><dd>-R$ 5.700</dd></div><div class="accent"><dt>Resultado Valtren</dt><dd>-R$ 5.700</dd></div></dl>
        </article>
        <article class="crm-venture-card">
          <header><div><span class="crm-status active">Ativo</span><h3>Dica de Cria</h3><p>Curso / Educação · Parceiro: DJ Stay</p></div><strong>50%</strong></header>
          <dl><div><dt>Vendas</dt><dd>R$ 42.000</dd></div><div><dt>Despesas</dt><dd>R$ 7.000</dd></div><div><dt>Resultado líquido</dt><dd>R$ 35.000</dd></div><div class="accent"><dt>Parcela Valtren</dt><dd>R$ 17.500</dd></div></dl>
        </article>
      </div>
    </section>`;

    const participation = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Participações</span><h2>Participações da Valtren</h2></div></div>
      <div class="crm-table-wrap"><table class="crm-table"><thead><tr><th>Produto</th><th>Participação Valtren</th><th>Outros sócios</th><th>Resultado do período</th><th>Resultado Valtren</th></tr></thead><tbody>
        <tr><td>Music OS 360</td><td>60%</td><td>40%</td><td>R$ 57.900</td><td><strong>R$ 34.740</strong></td></tr>
        <tr><td>Vivendo da Música</td><td>100%</td><td>—</td><td>-R$ 5.700</td><td><strong>-R$ 5.700</strong></td></tr>
        <tr><td>Dica de Cria</td><td>50%</td><td>50%</td><td>R$ 35.000</td><td><strong>R$ 17.500</strong></td></tr>
      </tbody></table></div>
    </section>`;

    const consolidated = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Financeiro consolidado</span><h2>Resultado da empresa</h2></div></div>
      <div class="crm-result-grid">
        <article><span>Serviços</span><dl><div><dt>Receita</dt><dd>R$ 180.000</dd></div><div><dt>Custos</dt><dd>R$ 105.000</dd></div><div><dt>Resultado</dt><dd>R$ 75.000</dd></div></dl></article>
        <article><span>Produtos</span><dl><div><dt>Receita atribuída à Valtren</dt><dd>R$ 95.000</dd></div><div><dt>Custos / Investimentos Valtren</dt><dd>R$ 42.000</dd></div><div><dt>Resultado</dt><dd>R$ 53.000</dd></div></dl></article>
        <article class="crm-result-total"><span>Resultado consolidado Valtren</span><strong>R$ 128.000</strong><small>Serviços + parcela econômica dos produtos</small></article>
      </div>
    </section>`;

    const distribution = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Distribuição financeira</span><h2>Dica de Cria</h2></div><span class="crm-transfer-status">Repasse pendente</span></div>
      <div class="crm-distribution">
        <div class="crm-distribution-calc"><div><span>Receita bruta</span><strong>R$ 100.000</strong></div><div><span>(-) Taxas</span><strong>R$ 5.000</strong></div><div><span>(-) Marketing</span><strong>R$ 20.000</strong></div><div><span>(-) Operação</span><strong>R$ 5.000</strong></div><div class="total"><span>Lucro distribuível</span><strong>R$ 70.000</strong></div></div>
        <div class="crm-distribution-partners"><article><span>DJ Stay</span><strong>50%</strong><b>R$ 35.000</b></article><article><span>Valtren</span><strong>50%</strong><b>R$ 35.000</b></article></div>
      </div>
    </section>`;

    const portfolio = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Meu Portfólio</span><h2>Portfólio Valtren</h2></div><div class="crm-portfolio-counts"><b>3 ativos</b><b>1 em desenvolvimento</b><b>2 em planejamento</b></div></div>
      <div class="crm-stages">
        <div class="crm-stage-labels"><span>Ideia</span><span>Validação</span><span>Desenvolvimento</span><span>Lançamento</span><span>Operação</span><span>Escala</span></div>
        ${stage('Music OS 360','ESCALA','scale')}
        ${stage('Vivendo da Música','DESENVOLVIMENTO','development')}
        ${stage('Dica de Cria','OPERAÇÃO','operation')}
      </div>
    </section>`;

    const recent = `<section class="crm-panel">
      <div class="crm-panel-heading"><div><span>Movimentações</span><h2>Atividade recente</h2></div></div>
      <ul class="crm-activity">
        ${activity('Music OS 360','+17 novas assinaturas')}
        ${activity('Dica de Cria','23 novas vendas')}
        ${activity('Serviços','Novo contrato fechado','Cliente X')}
        ${activity('Financeiro','R$ 18.500 recebido')}
        ${activity('Vivendo da Música','Nova despesa registrada','R$ 4.200')}
      </ul>
    </section>`;

    let content = '';
    if (activeView === 'services') content = servicesSummary;
    else if (activeView === 'ventures') content = `${venturesCards}${participation}${distribution}${portfolio}`;
    else content = `${kpis}${revenueComposition}<div class="crm-two-col">${servicesSummary}${venturesCards}</div>${participation}${consolidated}${distribution}${portfolio}${recent}`;

    return `<div class="crm-app-shell">
      <aside class="crm-sidebar">
        <a class="crm-brand" href="#/crm/dashboard" aria-label="Valtren CRM Integrado">
          <img src="assets/valtren-mark.svg" alt="Valtren Solutions">
          <span><strong>VALTREN</strong><small>CRM Integrado</small></span>
        </a>
        <nav class="crm-nav" aria-label="Módulos do CRM">
          <a class="active" href="#/crm/dashboard">${icon('layers',18)}<span>Dashboard</span></a>
        </nav>
      </aside>
      <main class="crm-main">
        <header class="crm-topbar">
          <div><span>CRM Integrado</span><h1>Dashboard</h1><p>Visão executiva consolidada da Valtren Solutions</p></div>
          <span class="crm-demo-badge">Protótipo · dados ilustrativos</span>
        </header>
        <section class="crm-workspace" aria-label="Dashboard">
          <nav class="crm-view-tabs" aria-label="Visões do dashboard">
            ${tab('overview','Visão Geral')}
            ${tab('services','Serviços')}
            ${tab('ventures','Produtos & Ventures')}
          </nav>
          ${content}
        </section>
      </main>
    </div>`;
  }
'''

CSS_PATCH = r'''
/* VALTREN CRM INTEGRATED */
.crm-app-shell{min-height:100vh;background:#F4F6F8;color:#0B1D3A;display:grid;grid-template-columns:250px minmax(0,1fr);font-family:Raleway,Montserrat,Arial,sans-serif}.crm-sidebar{background:#0B1D3A;color:#fff;padding:22px 16px;display:flex;flex-direction:column;gap:28px;border-right:1px solid rgba(212,175,55,.22)}.crm-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#fff;padding:4px 8px}.crm-brand img{width:34px;height:34px;object-fit:contain}.crm-brand span{display:flex;flex-direction:column;line-height:1.05}.crm-brand strong{font-size:15px;letter-spacing:.12em}.crm-brand small{font-family:Montserrat,Arial,sans-serif;color:#D4AF37;font-size:10px;margin-top:5px;letter-spacing:.04em}.crm-nav{display:flex;flex-direction:column;gap:6px}.crm-nav a{display:flex;align-items:center;gap:11px;min-height:44px;padding:0 12px;border-radius:8px;color:rgba(255,255,255,.78);text-decoration:none;font-size:14px;font-weight:600}.crm-nav a.active{background:rgba(212,175,55,.13);color:#fff;border:1px solid rgba(212,175,55,.24)}.crm-nav a.active svg{color:#D4AF37}
.crm-main{min-width:0;display:flex;flex-direction:column}.crm-topbar{min-height:88px;background:#fff;border-bottom:1px solid rgba(11,29,58,.1);display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 30px}.crm-topbar>div>span{display:block;font-family:Montserrat,Arial,sans-serif;color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px}.crm-topbar h1{font-size:25px;line-height:1.1;margin:0;color:#0B1D3A}.crm-topbar p{margin:6px 0 0;color:#64748B;font-size:12px;font-family:Montserrat,Arial,sans-serif}.crm-demo-badge{flex:0 0 auto;background:#FFF8E1;border:1px solid rgba(212,175,55,.45);color:#7A5B12;border-radius:999px;padding:8px 12px;font-size:11px;font-family:Montserrat,Arial,sans-serif;font-weight:600}
.crm-workspace{padding:26px 30px 40px;min-width:0}.crm-view-tabs{display:flex;align-items:center;gap:6px;margin-bottom:22px;padding:4px;background:#E9EDF2;border:1px solid rgba(11,29,58,.08);border-radius:10px;width:max-content;max-width:100%}.crm-view-tabs a{min-height:38px;padding:0 15px;display:flex;align-items:center;border-radius:7px;text-decoration:none;color:#566273;font-size:13px;font-weight:700;white-space:nowrap}.crm-view-tabs a.active{background:#fff;color:#0B1D3A;box-shadow:0 1px 4px rgba(11,29,58,.09)}
.crm-kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-bottom:16px}.crm-kpi{background:#fff;border:1px solid rgba(11,29,58,.09);border-radius:12px;padding:16px;min-width:0}.crm-kpi span{display:block;color:#697586;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em}.crm-kpi strong{display:block;margin-top:8px;font-size:22px;letter-spacing:-.03em;color:#0B1D3A}.crm-kpi small{display:block;margin-top:7px;color:#8A94A3;font-family:Montserrat,Arial,sans-serif;font-size:10px;line-height:1.45}
.crm-panel{background:#fff;border:1px solid rgba(11,29,58,.09);border-radius:14px;padding:20px;margin-bottom:16px;min-width:0}.crm-panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:18px}.crm-panel-heading>div>span{display:block;color:#B8891F;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.09em}.crm-panel-heading h2{margin:5px 0 0;font-size:19px;color:#0B1D3A}.crm-panel-total{font-size:21px;color:#0B1D3A;white-space:nowrap}
.crm-split-bars{display:grid;grid-template-columns:1fr 1fr;gap:22px}.crm-split-bars header{display:flex;justify-content:space-between;gap:12px;font-size:13px;color:#566273}.crm-split-bars header strong{color:#0B1D3A}.crm-bar{height:8px;background:#E8EDF2;border-radius:99px;overflow:hidden;margin-top:9px}.crm-bar i{display:block;height:100%;background:#D4AF37;border-radius:99px}.crm-split-bars>div:nth-child(2) .crm-bar i{background:#0B1D3A}.crm-rule-note{margin-top:18px;padding:13px 15px;background:#F8F9FB;border-left:3px solid #D4AF37;border-radius:0 8px 8px 0}.crm-rule-note strong{display:block;font-size:12px}.crm-rule-note p{margin:4px 0 0;color:#657183;font-family:Montserrat,Arial,sans-serif;font-size:11px;line-height:1.55}.crm-product-attribution{display:grid;grid-template-columns:1.5fr .7fr 1fr;gap:12px;margin-top:14px;border-top:1px solid rgba(11,29,58,.08);padding-top:14px}.crm-product-attribution>div{display:flex;flex-direction:column;gap:4px}.crm-product-attribution span{color:#758091;font-size:11px}.crm-product-attribution strong{font-size:13px}
.crm-mini-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}.crm-mini-metric{background:#F8FAFC;border:1px solid rgba(11,29,58,.07);border-radius:9px;padding:13px}.crm-mini-metric span{display:block;color:#718096;font-size:10px;text-transform:uppercase;letter-spacing:.04em}.crm-mini-metric strong{display:block;margin-top:6px;font-size:17px;color:#0B1D3A}.crm-service-detail-grid{display:grid;grid-template-columns:1.4fr 1fr;gap:12px;margin-top:14px}.crm-chart-placeholder,.crm-ranking-placeholder{border:1px solid rgba(11,29,58,.08);border-radius:10px;padding:15px;min-height:190px}.crm-subheading span{display:block;color:#7A8493;font-size:10px;text-transform:uppercase}.crm-subheading strong{display:block;margin-top:3px;font-size:13px}.crm-chart-empty{height:125px;margin-top:13px;position:relative;display:flex;align-items:center;justify-content:center;border-left:1px solid #DDE3EA;border-bottom:1px solid #DDE3EA}.crm-chart-empty:before,.crm-chart-empty:after{content:"";position:absolute;left:0;right:0;border-top:1px dashed #E5E9EE}.crm-chart-empty:before{top:33%}.crm-chart-empty:after{top:66%}.crm-chart-empty p,.crm-ranking-empty p{position:relative;z-index:1;background:#fff;padding:8px 10px;border-radius:6px;color:#8A94A3;font-size:10px;font-family:Montserrat,Arial,sans-serif;text-align:center;max-width:230px;line-height:1.45}.crm-ranking-empty{height:125px;margin-top:13px;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,#FBFCFD,#F7F9FB);border-radius:7px}
.crm-two-col{display:grid;grid-template-columns:1fr 1.18fr;gap:16px}.crm-two-col>.crm-panel{margin-bottom:16px}
.crm-venture-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.crm-venture-card{border:1px solid rgba(11,29,58,.1);border-radius:11px;padding:15px;background:#FBFCFD;min-width:0}.crm-venture-card header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;border-bottom:1px solid rgba(11,29,58,.08);padding-bottom:12px;margin-bottom:10px}.crm-venture-card header>strong{font-size:18px;color:#B8891F}.crm-venture-card h3{font-size:16px;margin:7px 0 3px}.crm-venture-card p{margin:0;color:#7B8696;font-size:10px;font-family:Montserrat,Arial,sans-serif}.crm-status{display:inline-flex;border-radius:999px;padding:4px 7px;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.05em}.crm-status.active{background:#E8F6EF;color:#26734D}.crm-status.development{background:#EDF3FE;color:#315D9B}.crm-venture-card dl{margin:0;display:grid;gap:7px}.crm-venture-card dl>div{display:flex;justify-content:space-between;gap:10px}.crm-venture-card dt{color:#778291;font-size:10px}.crm-venture-card dd{margin:0;font-weight:700;font-size:11px;color:#0B1D3A}.crm-venture-card .accent{padding-top:7px;border-top:1px solid rgba(212,175,55,.28)}.crm-venture-card .accent dd{color:#B8891F}.crm-venture-card .negative dd{color:#A13B3B}
.crm-table-wrap{overflow:auto}.crm-table{width:100%;border-collapse:collapse;min-width:760px}.crm-table th{text-align:left;padding:9px 10px;background:#F6F8FA;color:#6C7787;font-size:10px;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid rgba(11,29,58,.08)}.crm-table td{padding:11px 10px;border-bottom:1px solid rgba(11,29,58,.07);font-size:11px;color:#4B5768}.crm-table td:first-child{font-weight:700;color:#0B1D3A}.crm-table td strong{color:#B8891F}
.crm-result-grid{display:grid;grid-template-columns:1fr 1fr .9fr;gap:12px}.crm-result-grid>article{border:1px solid rgba(11,29,58,.08);border-radius:10px;padding:15px;background:#FAFBFC}.crm-result-grid>article>span{font-size:11px;text-transform:uppercase;color:#6F7B8B;font-weight:800}.crm-result-grid dl{margin:12px 0 0;display:grid;gap:7px}.crm-result-grid dl div{display:flex;justify-content:space-between;gap:12px}.crm-result-grid dt{font-size:10px;color:#7B8695}.crm-result-grid dd{margin:0;font-size:11px;font-weight:700}.crm-result-total{background:#0B1D3A!important;color:#fff!important;display:flex;flex-direction:column;justify-content:center}.crm-result-total>span{color:rgba(255,255,255,.65)!important}.crm-result-total strong{display:block;font-size:28px;margin-top:9px;color:#D4AF37}.crm-result-total small{color:rgba(255,255,255,.62);font-size:9px;margin-top:6px;line-height:1.4}
.crm-transfer-status{border-radius:999px;background:#FFF4E5;color:#95601A;border:1px solid #F0D19F;padding:6px 9px;font-size:9px;font-weight:800;text-transform:uppercase;white-space:nowrap}.crm-distribution{display:grid;grid-template-columns:1.15fr .85fr;gap:16px}.crm-distribution-calc{display:grid;gap:7px}.crm-distribution-calc>div{display:flex;justify-content:space-between;padding:8px 10px;background:#F8FAFC;border-radius:7px}.crm-distribution-calc span{font-size:10px;color:#6E7988}.crm-distribution-calc strong{font-size:11px}.crm-distribution-calc .total{background:#0B1D3A;color:#fff;margin-top:3px}.crm-distribution-calc .total span{color:rgba(255,255,255,.72)}.crm-distribution-calc .total strong{color:#D4AF37}.crm-distribution-partners{display:grid;grid-template-columns:1fr 1fr;gap:9px}.crm-distribution-partners article{border:1px solid rgba(11,29,58,.08);border-radius:9px;padding:14px;display:flex;flex-direction:column}.crm-distribution-partners span{color:#6F7988;font-size:10px}.crm-distribution-partners strong{font-size:22px;margin-top:7px;color:#0B1D3A}.crm-distribution-partners b{font-size:12px;margin-top:auto;padding-top:15px;color:#B8891F}
.crm-portfolio-counts{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.crm-portfolio-counts b{font-size:9px;border-radius:999px;padding:6px 8px;background:#F0F3F6;color:#627082}.crm-stages{overflow:hidden}.crm-stage-labels{display:grid;grid-template-columns:repeat(6,1fr);gap:2px;font-size:8px;text-transform:uppercase;letter-spacing:.04em;color:#8A94A3;text-align:center;margin-bottom:12px}.crm-stage-row{display:grid;grid-template-columns:200px 1fr;gap:16px;align-items:center;margin-bottom:12px}.crm-stage-row>div:first-child{display:flex;align-items:center;gap:9px;min-width:0}.crm-stage-row strong{font-size:11px}.crm-stage{font-size:8px;font-weight:800;border-radius:999px;padding:4px 6px}.crm-stage.scale{background:#E8F6EF;color:#26734D}.crm-stage.development{background:#EDF3FE;color:#315D9B}.crm-stage.operation{background:#FFF4E5;color:#95601A}.crm-stage-track{height:8px;background:repeating-linear-gradient(90deg,#E8EDF2 0,#E8EDF2 calc(16.66% - 2px),transparent calc(16.66% - 2px),transparent 16.66%);border-radius:99px;overflow:hidden}.crm-stage-track i{display:block;height:100%;background:#D4AF37;border-radius:99px}.crm-stage-track i.scale{width:100%}.crm-stage-track i.development{width:50%}.crm-stage-track i.operation{width:83.33%}
.crm-activity{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}.crm-activity li{border:1px solid rgba(11,29,58,.08);border-radius:9px;padding:11px;min-width:0}.crm-activity li>span{display:block;color:#B8891F;font-size:8px;text-transform:uppercase;font-weight:800;letter-spacing:.05em}.crm-activity li strong{display:block;margin-top:7px;font-size:10px;line-height:1.4}.crm-activity li small{display:block;margin-top:4px;color:#798493;font-size:9px}
@media(max-width:1280px){.crm-kpi-grid{grid-template-columns:repeat(3,1fr)}.crm-two-col{grid-template-columns:1fr}.crm-venture-grid{grid-template-columns:repeat(3,1fr)}.crm-mini-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:980px){.crm-app-shell{grid-template-columns:210px minmax(0,1fr)}.crm-workspace{padding:22px}.crm-kpi-grid{grid-template-columns:repeat(2,1fr)}.crm-venture-grid{grid-template-columns:1fr}.crm-result-grid{grid-template-columns:1fr}.crm-distribution{grid-template-columns:1fr}.crm-activity{grid-template-columns:1fr 1fr}.crm-split-bars{grid-template-columns:1fr}.crm-product-attribution{grid-template-columns:1fr 1fr}.crm-service-detail-grid{grid-template-columns:1fr}}
@media(max-width:760px){.crm-app-shell{grid-template-columns:1fr}.crm-sidebar{padding:14px;gap:14px}.crm-brand img{width:30px;height:30px}.crm-nav{flex-direction:row}.crm-nav a{flex:0 0 auto}.crm-topbar{padding:15px 18px;align-items:flex-start}.crm-demo-badge{display:none}.crm-workspace{padding:16px}.crm-view-tabs{width:100%;overflow:auto}.crm-kpi-grid{grid-template-columns:1fr 1fr}.crm-kpi strong{font-size:19px}.crm-mini-grid{grid-template-columns:1fr 1fr}.crm-product-attribution{grid-template-columns:1fr}.crm-distribution-partners{grid-template-columns:1fr 1fr}.crm-stage-labels{display:none}.crm-stage-row{grid-template-columns:1fr;gap:7px}.crm-activity{grid-template-columns:1fr}}
@media(max-width:440px){.crm-kpi-grid{grid-template-columns:1fr}.crm-mini-grid{grid-template-columns:1fr}.crm-distribution-partners{grid-template-columns:1fr}}
'''


def _write_css_cache_version() -> None:
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = re.sub(
            r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?",
            f"valtren-brand.css?v={CSS_VERSION}",
            original,
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def apply_crm_dashboard() -> int:
    app = APP.read_text(encoding="utf-8")

    existing = re.search(
        r"  function crmDashboardPage\([^)]*\)\{.*?\n  \}\n\n(?=  function contactPage)",
        app,
        flags=re.S,
    )
    if existing:
        app = app[:existing.start()] + CRM_FUNCTION + "\n" + app[existing.end():]
    else:
        anchor = "  function contactPage(query)"
        if anchor not in app:
            raise RuntimeError("CRM function anchor not found")
        app = app.replace(anchor, CRM_FUNCTION + "\n" + anchor, 1)

    old_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage();"
    new_route = "    else if (path === '/crm/dashboard' || path === '/crm') app.innerHTML = crmDashboardPage(query);"
    if old_route in app:
        app = app.replace(old_route, new_route)

    if "path === '/crm/dashboard'" not in app:
        anchor = "    else if (path === '/contato') app.innerHTML = contactPage(query);"
        count = app.count(anchor)
        if count < 2:
            raise RuntimeError(f"Expected two route anchors, found {count}")
        app = app.replace(anchor, new_route + "\n" + anchor)

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM INTEGRATED \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    _write_css_cache_version()
    print("Dashboard executivo do CRM aplicado.")
    return 1


if __name__ == "__main__":
    apply_crm_dashboard()
