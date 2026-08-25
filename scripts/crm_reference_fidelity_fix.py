from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "assets" / "valtren-brand.css"
CACHE_VERSION = "20260825-crm-reference-modules-v3"

INVOICE_MODAL = r'''  function crmRefInvoiceModal(){const body=`<section class="crm-ref-form-section"><h3>Tipo de Operação</h3><div class="crm-ref-choice-row"><label><input type="radio" name="op" checked> Saída</label><label><input type="radio" name="op"> Entrada</label></div></section><section class="crm-ref-form-section"><h3>Identificação</h3><div class="crm-ref-form-grid">${crmRefField('Número da Nota','number','text','000001234')}${crmRefField('Série','series','text','001')}${crmRefSelect('Tipo de Nota','invoiceType',[['servico','Serviço'],['produto','Produto']])}${crmRefField('Data de Emissão','issueDate','date','Selecione a data')}${crmRefSelect('Status','status',[['emitida','Emitida'],['pendente','Pendente'],['paga','Paga'],['cancelada','Cancelada']])}${crmRefField('Natureza da Operação','nature')}${crmRefField('CFOP','cfop','text','5933')}${crmRefField('Código Serviço Municipal','serviceCode')}${crmRefField('Código Município (IBGE)','ibge','text','3550308')}</div></section><section class="crm-ref-form-section"><h3>Tomador / Cliente</h3><div class="crm-ref-form-grid">${crmRefField('Cliente / Fornecedor','customer','text','Selecione um cliente')}${crmRefField('CNPJ / CPF','document','text','00.000.000/0001-00')}${crmRefField('Razão Social / Nome','legalName')}${crmRefField('Inscrição Estadual','ie')}${crmRefField('Inscrição Municipal','im')}${crmRefField('E-mail','email','email')}${crmRefField('Endereço','address','text','Av. Paulista, 1000')}${crmRefField('Cidade','city')}${crmRefField('UF','uf')}${crmRefField('CEP','zip','text','00000-000')}</div></section><section class="crm-ref-form-section"><h3>Serviços</h3>${crmRefTextarea('Descrição dos Serviços','services','Descrição completa dos serviços prestados...')}<section class="crm-ref-panel crm-ref-invoice-items"><header><h3>Itens da Nota</h3><button type="button">${crmRefIcon('plus')} Adicionar Item</button></header><div class="crm-ref-form-grid invoice-item">${crmRefField('Descrição','itemDescription')}${crmRefField('Cód. Serviço','itemCode')}${crmRefField('Qtd','itemQty','number','1')}${crmRefField('Vlr Unit.','itemUnit','number','0,00')}<div class="crm-ref-field"><span>Total</span><strong>${crmRefMoney(0)}</strong></div></div><div class="crm-ref-invoice-total"><span>Total dos Serviços</span><strong>${crmRefMoney(0)}</strong></div></section></section><section class="crm-ref-form-section"><h3>Tributos</h3><div class="crm-ref-tax-head"><p>Tributos calculados automaticamente sobre o valor dos serviços.</p><button type="button">${crmRefIcon('calculator')} Recalcular</button></div><div class="crm-ref-form-grid three">${crmRefField('Valor dos Serviços','value','number','0,00')}${crmRefField('Deduções','deductions','number','0,00')}${crmRefField('Base de Cálculo','base','number','0,00')}</div><section class="crm-ref-panel"><header><h3>ISS</h3></header><div class="crm-ref-form-grid three">${crmRefField('Alíquota ISS (%)','issRate','number','0')}${crmRefField('Valor ISS','iss','number','0,00')}<label class="crm-ref-field switch"><span>ISS Retido na Fonte?</span><input type="checkbox" name="issWithheld"></label></div></section><section class="crm-ref-panel"><header><h3>Retenções Federais</h3></header><div class="crm-ref-form-grid five">${crmRefField('PIS','pis','number','0,00')}${crmRefField('COFINS','cofins','number','0,00')}${crmRefField('IRRF','irrf','number','0,00')}${crmRefField('CSLL','csll','number','0,00')}${crmRefField('INSS','inss','number','0,00')}</div></section><div class="crm-ref-tax-summary"><div><span>Valor Líquido da Nota</span><strong>${crmRefMoney(0)}</strong></div><div><span>Bruto: ${crmRefMoney(0)}</span><span>Total Retenções: ${crmRefMoney(0)}</span></div></div></section><section class="crm-ref-form-section"><h3>Pagamento</h3><div class="crm-ref-form-grid three">${crmRefSelect('Forma de Pagamento','payment',[['dinheiro','Dinheiro'],['pix','PIX'],['transferencia','Transferência'],['boleto','Boleto'],['cartao_credito','Cartão de Crédito'],['cartao_debito','Cartão de Débito'],['cheque','Cheque']])}${crmRefField('Condição','condition','text','30 dias / À vista / 30/60/90')}${crmRefField('Vencimento','due','date','Selecione a data')}</div><label class="crm-ref-field full"><span>Arquivo PDF da Nota</span><input type="file" accept=".pdf,application/pdf"></label><p class="crm-ref-note">O PDF é enviado ao armazenamento antes de salvar a nota. Se o armazenamento não estiver configurado, o formulário deve mostrar o erro real e não simular sucesso.</p>${crmRefTextarea('Observações','notes','Observações adicionais...')}</section>`;return crmRefModal('Registrar Nota Fiscal',body,'crm-ref-invoice-form',true);}
'''

CSS_PATCH = r'''
/* VALTREN CRM REFERENCE FIDELITY */
.crm-ref-form-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.crm-ref-form-grid.five{grid-template-columns:repeat(5,minmax(0,1fr))}.crm-ref-invoice-items{margin:10px 0 0!important}.crm-ref-invoice-items>.crm-ref-form-grid{margin:12px}.crm-ref-invoice-total{display:flex;justify-content:flex-end;align-items:flex-end;gap:10px;padding:10px 12px;border-top:1px solid #e7ebf0}.crm-ref-invoice-total span{font-size:8px;color:#7a8796}.crm-ref-invoice-total strong{font-size:15px}.crm-ref-tax-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.crm-ref-tax-head p{margin:0;color:#748193;font-size:8px}.crm-ref-tax-head button{height:31px;border:1px solid #dce3ea;border-radius:7px;background:#fff;color:#0B1D3A;padding:0 10px;font-size:8px;font-weight:800}.crm-ref-tax-summary{border:1px solid rgba(11,29,58,.13);background:#f3f6f9;border-radius:8px;padding:12px;display:flex;align-items:center;justify-content:space-between;gap:12px}.crm-ref-tax-summary>div{display:grid;gap:3px}.crm-ref-tax-summary span{font-size:8px;color:#697688}.crm-ref-tax-summary strong{font-size:18px;color:#0B1D3A}
@media(max-width:860px){.crm-ref-form-grid.three,.crm-ref-form-grid.five{grid-template-columns:1fr}}
'''


def apply_crm_reference_fidelity_fix() -> int:
    app = APP.read_text(encoding="utf-8")
    pattern = r"  function crmRefInvoiceModal\(\)\{.*?\n  function crmRefCategoryModal"
    if not re.search(pattern, app, flags=re.S):
        raise RuntimeError("Modal de Nota Fiscal de referência não encontrado")
    app = re.sub(pattern, INVOICE_MODAL + "  function crmRefCategoryModal", app, count=1, flags=re.S)
    app = app.replace("Arraste ou clique para escolher XLSX/CSV", "XLSX")
    app = app.replace('accept=".xlsx,.csv"', 'accept=".xlsx"')
    APP.write_text(app, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(r"\n?/\* VALTREN CRM REFERENCE FIDELITY \*/.*\Z", "", css, flags=re.S)
    CSS.write_text(css.rstrip() + "\n" + CSS_PATCH.strip() + "\n", encoding="utf-8")

    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".bootstrap", "node_modules", "scripts"} for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"app\.js(?:\?v=[A-Za-z0-9._-]+)?", f"app.js?v={CACHE_VERSION}", text)
        text = re.sub(r"valtren-brand\.css(?:\?v=[A-Za-z0-9._-]+)?", f"valtren-brand.css?v={CACHE_VERSION}", text)
        path.write_text(text, encoding="utf-8")
    print("Fidelidade dos módulos anexados reforçada: Nota Fiscal e Relatórios XLSX.")
    return 1


if __name__ == "__main__":
    apply_crm_reference_fidelity_fix()
