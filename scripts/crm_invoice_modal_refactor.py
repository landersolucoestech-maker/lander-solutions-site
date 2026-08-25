from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-invoice-modal-refactor-v1"

INVOICES_PAGE = r'''  function crmRefInvoicesPage(){crmRefEnsureState();const rows=state.crmRefInvoices||[];const actions=`<button type="button" class="primary" data-action="crm-ref-open" data-kind="invoice">${crmRefIcon('plus')} Criar Nota</button>`;const k=`<div class="crm-ref-kpis six">${crmRefKpi('Total',rows.length)}${crmRefKpi('Saídas',0,'','success')}${crmRefKpi('Entradas',0,'','warning')}${crmRefKpi('Valor Saídas',crmRefMoney(0),'','success')}${crmRefKpi('Valor Entradas',crmRefMoney(0),'','warning')}${crmRefKpi('Saldo',crmRefMoney(0))}</div>`;const filters=crmRefToolbar(`<input type="date" placeholder="Data início"><input type="date" placeholder="Data fim"><label class="crm-ref-search">${icon('search',14)}<input placeholder="Buscar por número, cliente ou fornecedor…"></label><select><option>Tipo</option><option>Todas</option><option>Saída</option><option>Entrada</option></select><select><option>Status</option><option>Todos</option><option>Emitida</option><option>Pendente</option><option>Paga</option><option>Cancelada</option></select>`);const table=crmFidelityTable('Lista de Notas Fiscais','Registro de notas de entrada e saída',['','Número','Tipo','Cliente / Fornecedor','Valor','Data Emissão','Status','PDF','Ações'],'Nenhuma nota fiscal cadastrada');return crmFidelityPage('accounting','invoices','Notas Fiscais','Registro e controle de notas fiscais de entrada e saída',actions,`${k}${filters}${table}`);}
'''

INVOICE_MODAL = r'''  function crmRefInvoiceModal(){const body=`<section class="crm-ref-form-section crm-ref-invoice-operation"><h3>Tipo da Movimentação</h3><p class="crm-ref-invoice-section-help">Defina se a nota representa uma saída emitida pela empresa ou uma entrada recebida de fornecedor.</p><div class="crm-ref-choice-row"><label><input type="radio" name="op" value="saida" checked><span><strong>Saída</strong><small>Nota emitida pela empresa</small></span></label><label><input type="radio" name="op" value="entrada"><span><strong>Entrada</strong><small>Nota recebida de fornecedor</small></span></label></div></section><section class="crm-ref-form-section"><h3>Dados da Nota</h3><div class="crm-ref-form-grid">${crmRefField('Número da Nota *','number','text','000001234')}${crmRefField('Série','series','text','001')}${crmRefSelect('Tipo de Nota *','invoiceType',[['servico','Serviço'],['produto','Produto']])}${crmRefField('Data de Emissão *','issueDate','date','Selecione a data')}${crmRefSelect('Status *','status',[['emitida','Emitida'],['pendente','Pendente'],['paga','Paga'],['cancelada','Cancelada']])}${crmRefField('Natureza da Operação','nature','text','Ex: Prestação de serviços')}${crmRefField('CFOP','cfop','text','5933')}${crmRefField('Código do Serviço','serviceCode')}</div></section><section class="crm-ref-form-section"><h3>Cliente / Fornecedor</h3><div class="crm-ref-form-grid">${crmRefField('Cliente / Fornecedor *','customer','text','Selecione ou informe o cadastro')}${crmRefField('CNPJ / CPF *','document','text','00.000.000/0001-00')}${crmRefField('Razão Social / Nome *','legalName')}${crmRefField('E-mail','email','email')}${crmRefField('Inscrição Estadual','ie')}${crmRefField('Inscrição Municipal','im')}${crmRefField('Endereço','address','text','Rua, número e complemento')}${crmRefField('Cidade','city')}${crmRefField('UF','uf')}${crmRefField('CEP','zip','text','00000-000')}</div></section><section class="crm-ref-form-section"><h3>Descrição e Valores</h3>${crmRefTextarea('Descrição / Itens da Nota *','services','Descreva os serviços, produtos ou itens da nota...')}<div class="crm-ref-form-grid three">${crmRefField('Valor Bruto *','value','number','0,00')}${crmRefField('Deduções','deductions','number','0,00')}${crmRefField('Desconto','discount','number','0,00')}</div><div class="crm-ref-invoice-tax-block"><div class="crm-ref-invoice-tax-title"><strong>Tributos e retenções</strong><span>Preencha somente quando aplicável.</span></div><div class="crm-ref-form-grid three">${crmRefField('Alíquota ISS (%)','issRate','number','0')}${crmRefField('Valor ISS','iss','number','0,00')}<label class="crm-ref-field switch"><span>ISS Retido?</span><input type="checkbox" name="issWithheld"></label>${crmRefField('PIS','pis','number','0,00')}${crmRefField('COFINS','cofins','number','0,00')}${crmRefField('IRRF','irrf','number','0,00')}${crmRefField('CSLL','csll','number','0,00')}${crmRefField('INSS','inss','number','0,00')}</div></div><div class="crm-ref-tax-summary"><div><span>Valor Líquido da Nota</span><strong>${crmRefMoney(0)}</strong></div></div></section><section class="crm-ref-form-section"><h3>Pagamento e Documento</h3><div class="crm-ref-form-grid three">${crmRefSelect('Forma de Pagamento','payment',[['dinheiro','Dinheiro'],['pix','PIX'],['transferencia','Transferência'],['boleto','Boleto'],['cartao_credito','Cartão de Crédito'],['cartao_debito','Cartão de Débito'],['cheque','Cheque']])}${crmRefField('Condição','condition','text','À vista / 30 dias / 30-60-90')}${crmRefField('Vencimento','due','date','Selecione a data')}</div><label class="crm-ref-field full"><span>Arquivo PDF da Nota</span><input type="file" accept=".pdf,application/pdf"></label>${crmRefTextarea('Observações','notes','Observações adicionais...')}</section>`;return crmRefModal('Criar Nota Fiscal',body,'crm-ref-invoice-form',true);}
'''

CSS_PATCH = r'''
/* VALTREN CRM INVOICE MODAL REFACTOR */
#crm-ref-invoice-form .crm-ref-modal-body{gap:18px!important}
#crm-ref-invoice-form .crm-ref-form-section{padding:0!important;background:#fff!important}
#crm-ref-invoice-form .crm-ref-form-section>h3{font-size:10px!important;color:#0B1D3A!important;letter-spacing:.05em!important}
#crm-ref-invoice-form .crm-ref-invoice-section-help{margin:0 0 10px;color:#64748B;font-size:9px;line-height:1.45}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row label{min-height:58px;padding:10px 12px;border:1px solid #D9E0E8;border-radius:9px;background:#fff;display:flex;align-items:center;gap:10px;cursor:pointer;color:#0B1D3A}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row label:has(input:checked){border-color:#D4AF37;box-shadow:0 0 0 2px rgba(212,175,55,.12);background:#FFFDF5}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row label>span{display:grid;gap:3px}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row strong{font-size:10px;color:#0B1D3A}
#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row small{font-size:8px;color:#64748B}
#crm-ref-invoice-form .crm-ref-invoice-tax-block{margin-top:12px;padding:12px;border:1px solid #E2E8F0;border-radius:9px;background:#F8FAFC}
#crm-ref-invoice-form .crm-ref-invoice-tax-title{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}
#crm-ref-invoice-form .crm-ref-invoice-tax-title strong{font-size:9px;color:#0B1D3A}
#crm-ref-invoice-form .crm-ref-invoice-tax-title span{font-size:8px;color:#64748B}
#crm-ref-invoice-form .crm-ref-tax-summary{margin-top:12px;border:1px solid #E2E8F0!important;background:#fff!important}
#crm-ref-invoice-form .crm-ref-tax-summary strong{color:#0B1D3A!important}
@media(max-width:700px){#crm-ref-invoice-form .crm-ref-invoice-operation .crm-ref-choice-row{grid-template-columns:1fr}}
'''


def apply_crm_invoice_modal_refactor() -> int:
    app = APP.read_text(encoding="utf-8")

    app, page_count = re.subn(
        r"  function crmRefInvoicesPage\(\)\{[^\n]*\}\n",
        INVOICES_PAGE,
        app,
        count=1,
    )
    if page_count != 1:
        raise RuntimeError("crmRefInvoicesPage não encontrada para remover o dropdown de criação")

    app, modal_count = re.subn(
        r"  function crmRefInvoiceModal\(\)\{[^\n]*\}\n",
        INVOICE_MODAL,
        app,
        count=1,
    )
    if modal_count != 1:
        raise RuntimeError("crmRefInvoiceModal não encontrada para refatoração")

    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM INVOICE MODAL REFACTOR \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")

    print("Notas Fiscais: criação direta no modal, dropdown removido e modal refatorado.")
    return 1


if __name__ == "__main__":
    apply_crm_invoice_modal_refactor()
