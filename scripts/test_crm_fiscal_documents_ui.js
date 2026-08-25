const assert=require('assert');
const fs=require('fs');
const path=require('path');

const browser=fs.readFileSync(path.join(__dirname,'crm_fiscal_documents_browser.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'crm_fiscal_documents.css'),'utf8');
let passed=0;
function test(name,fn){try{fn();passed++;console.log(`PASS ${passed} ${name}`);}catch(error){console.error(`FAIL ${name}: ${error.message}`);throw error;}}

test('1 nome oficial é Notas Fiscais',()=>{assert(browser.includes("'Notas Fiscais'"));assert(browser.includes('Financeiro</a><span>/</span><strong>Notas Fiscais</strong>'));});
test('2 rota canônica usa /notas-fiscais',()=>{assert(browser.includes('#/crm/financeiro/notas-fiscais'));});
test('3 alias /invoices apenas normaliza para rota canônica',()=>{assert(browser.includes('function crmFiscalLegacyInvoicesRoute()'));assert(browser.includes("replace('#/crm/financeiro/invoices','#/crm/financeiro/notas-fiscais')"));});
test('4 existe uma única ação principal Criar Nota',()=>{assert(browser.includes('data-action="crm-fiscal-create"'));assert(browser.includes('Criar Nota</button>'));assert(!browser.includes('Nova Nota de Entrada'));assert(!browser.includes('Nova Nota de Saída'));});
test('5 Criar Nota começa por escolha Entrada/Saída',()=>{assert(browser.includes('Qual tipo de nota deseja registrar?'));assert(browser.includes('data-direction="incoming"'));assert(browser.includes('data-direction="outgoing"'));});
test('6 tab Entrada existe',()=>{assert(browser.includes("['incoming','Entrada']"));});
test('7 tab Saída existe',()=>{assert(browser.includes("['outgoing','Saída']"));});
test('8 contadores das tabs são reais',()=>{assert(browser.includes("service.list({direction,limit:0}).total"));});
test('9 tableview possui campos operacionais',()=>{for(const label of ['Data','Número','Tipo','Descrição','Valor','Tributos / Retenções','Status Fiscal','Status Financeiro','Vínculo','Ação'])assert(browser.includes(label));});
test('10 busca cobre número/série/chave/parte/descrição/valor',()=>{assert(browser.includes('Buscar número, série, chave, parte, descrição, valor ou documento'));assert(browser.includes('id="crm-fiscal-search"'));});
test('11 filtros de período existem',()=>{assert(browser.includes('id="crm-fiscal-from"'));assert(browser.includes('id="crm-fiscal-to"'));});
test('12 filtro status fiscal existe e é separado',()=>{assert(browser.includes('id="crm-fiscal-status"'));assert(browser.includes('Todo status fiscal'));});
test('13 filtro status financeiro existe e é separado',()=>{assert(browser.includes('id="crm-fiscal-financial"'));assert(browser.includes('Todo status financeiro'));});
test('14 Mais filtros contém parte/produto/serviço/unidade/vínculo',()=>{for(const id of ['crm-fiscal-party','crm-fiscal-product','crm-fiscal-service','crm-fiscal-unit','crm-fiscal-linked'])assert(browser.includes(`id="${id}"`));});
test('15 formulário Entrada reutiliza Pessoa/Organização canônica',()=>{assert(browser.includes('Fornecedor / Emitente'));assert(browser.includes('crmFiscalPartyOptions()'));assert(browser.includes('crmCanonicalPartyService()'));});
test('16 formulário Saída reutiliza Pessoa/Organização canônica',()=>{assert(browser.includes('Cliente / Tomador'));assert(browser.includes('crmFiscalPartyOptions()'));});
test('17 formulário possui competência fiscal sem recognitionDate',()=>{assert(browser.includes('Competência fiscal'));assert(browser.includes('name="competenceDate"'));assert(!browser.includes('name="recognitionDate"'));});
test('18 formulário possui itens múltiplos',()=>{assert(browser.includes('data-fiscal-item-row'));assert(browser.includes('crm-fiscal-add-item'));assert(browser.includes('Adicionar item'));});
test('19 formulário possui tributos explícitos',()=>{assert(browser.includes('data-fiscal-tax-row'));assert(browser.includes('Adicionar tributo'));assert(browser.includes('Nenhuma alíquota é inferida automaticamente.'));});
test('20 formulário possui retenções explícitas',()=>{assert(browser.includes('data-fiscal-retention-row'));assert(browser.includes('Adicionar retenção'));});
test('21 Produto Serviço Unidade e Contrato são selects referenciais',()=>{for(const name of ['productId','serviceId','businessUnitId','contractId'])assert(browser.includes(`name="${name}"`));assert(browser.includes('Sem produtos cadastrados'));assert(browser.includes('Sem serviços cadastrados'));assert(browser.includes('Sem unidades cadastradas'));assert(browser.includes('Sem contratos disponíveis'));});
test('22 XML/PDF são apresentados como metadata sem storage falso',()=>{assert(browser.includes('Apenas metadados/referências')||browser.includes('registra metadados/referências'));assert(browser.includes('XML · nome do arquivo'));assert(browser.includes('PDF · nome do arquivo'));assert(browser.includes('Não simula armazenamento de XML/PDF nem DANFE oficial.'));});
test('23 não existe botão de emissão fiscal falsa',()=>{for(const forbidden of ['Emitir na SEFAZ','Emitir NFS-e','Autorizar nota','Transmitir para SEFAZ'])assert(!browser.includes(forbidden));});
test('24 status Emitida informa registro interno',()=>{assert(browser.includes('Emitida · registro interno'));});
test('25 integração nunca aparece conectada sem validação',()=>{assert(browser.includes('integrationValidator:()=>false'));assert(browser.includes('Integração não validada'));});
test('26 drawer contém dados gerais partes itens tributos retenções relacionamentos transações documentos histórico',()=>{for(const label of ['Dados gerais','Partes','Itens','Tributos','Retenções','Relacionamentos','Transações vinculadas','Documentos e anexos','Histórico'])assert(browser.includes(label));});
test('27 transações vinculadas oferecem Ver em Transações',()=>{assert(browser.includes('Ver em Transações'));assert(browser.includes('crmFinanceService().getTransaction'));});
test('28 vincular transação é confirmação explícita',()=>{assert(browser.includes('data-action="crm-fiscal-link-transaction"'));assert(browser.includes('>Vincular</button>'));assert(browser.includes('Nenhum vínculo é realizado automaticamente.'));});
test('29 desvincular transação existe',()=>{assert(browser.includes('crm-fiscal-unlink-transaction'));assert(browser.includes('Desvincular'));});
test('30 pagamento parcial é exibido com derivação',()=>{assert(browser.includes("settlement.status==='partial'"));assert(browser.includes('settlement.settledAmount'));assert(browser.includes('settlement.balance'));});
test('31 cancelar deixa claro que é registro e não operação oficial',()=>{assert(browser.includes('Marcar como cancelada · registro'));assert(browser.includes('Não executa cancelamento oficial.'));});
test('32 estado vazio Entrada é explícito',()=>{assert(browser.includes('Nenhuma nota fiscal de entrada encontrada.'));assert(browser.includes('As notas recebidas ou importadas aparecerão aqui.'));});
test('33 estado vazio Saída é explícito',()=>{assert(browser.includes('Nenhuma nota fiscal de saída encontrada.'));assert(browser.includes('As notas emitidas ou cadastradas aparecerão aqui.'));});
test('34 dados institucionais ausentes geram pendência',()=>{assert(browser.includes('Dados institucionais da Valtren estão incompletos em Configurações → Empresa. Nenhum dado foi inventado.'));});
test('35 divergência de totais importados é visível',()=>{assert(browser.includes('Totais importados/informados não reconciliam'));});
test('36 potencial duplicidade é visível',()=>{assert(browser.includes('Possível duplicidade detectada'));});
test('37 responsividade possui quatro breakpoints',()=>{for(const width of ['1380px','1050px','760px','520px'])assert(css.includes(`max-width:${width}`));});
test('38 mobile preserva tabela com número/data/parte/valor/status/ação',()=>{assert(css.includes('.crm-fiscal-table-wrap table{min-width:620px}'));assert(css.includes('nth-child(3)'));assert(css.includes('nth-child(5)'));});
test('39 drawer respeita viewport',()=>{assert(css.includes('width:min(920px,100%)'));assert(css.includes('.crm-fiscal-drawer-body{min-height:0;overflow:auto'));});
test('40 modal e linhas refluem em mobile',()=>{assert(css.includes('.crm-fiscal-form-grid,.crm-fiscal-form-grid.compact{grid-template-columns:1fr}'));assert(css.includes('.crm-fiscal-line,.crm-fiscal-line.tax,.crm-fiscal-line.retention{grid-template-columns:1fr}'));});
test('41 não existe editor bancário dentro de Notas Fiscais',()=>{for(const forbidden of ['crmFinanceOpenTransactionModal','data-action="crm-fin-edit"','Nova Transação'])assert(!browser.includes(forbidden));});
test('42 UI usa state.crmFiscalDocuments como fonte fiscal',()=>{assert(browser.includes('state.crmFiscalDocuments=ValtrenFiscalCore.ensureState'));assert(!browser.includes('incomingInvoices'));assert(!browser.includes('outgoingInvoices'));});
test('43 legado crmRefInvoices é somente entrada de compatibilidade',()=>{const occurrences=(browser.match(/crmRefInvoices/g)||[]).length;assert.equal(occurrences,2);assert(browser.includes('service.migrateLegacy'));});
test('44 paginação é limitada a 50',()=>{assert(browser.includes('limit:50'));assert(browser.includes('crm-fiscal-page'));});
test('45 adapter Contabilidade é somente leitura',()=>{assert(browser.includes('function crmFiscalAccountingFeed(filters={})'));assert(browser.includes('crmFiscalService().accountingFeed(filters)'));assert(!browser.includes('state.crmAccounting='));});

if(process.argv.includes('--materialized')){
  const app=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
  const bundleCss=fs.readFileSync(path.join(__dirname,'..','assets','valtren-brand.css'),'utf8');
  test('46 UI fiscal final está no bundle',()=>{for(const fn of ['function crmFiscalDocumentsPage()','function crmFiscalOpenCreate()','function crmFiscalOpenForm(direction)','function crmFiscalOpenDetail(id)'])assert(app.includes(fn));});
  test('47 breadcrumb publicado é Financeiro / Notas Fiscais',()=>{assert(app.includes('Financeiro</a><span>/</span><strong>Notas Fiscais</strong>'));});
  test('48 Criar Nota publicado mantém entrada única',()=>{assert(app.includes('data-action="crm-fiscal-create"'));assert(!app.includes('Nova Nota de Entrada'));assert(!app.includes('Nova Nota de Saída'));});
  test('49 nenhum crmRefInvoicesPage/modal sobrevive',()=>{assert(!app.includes('function crmRefInvoicesPage()'));assert(!app.includes('function crmRefInvoiceModal()'));});
  test('50 nome principal do sidebar continua Notas Fiscais',()=>{const start=app.lastIndexOf('function crmRelSidebar'),end=app.indexOf('function crmReferenceRoute',start),side=app.slice(start,end);assert(side.includes('Notas Fiscais'));assert(!side.includes('>Fiscal<'));assert(!side.includes('>Invoices<'));});
  test('51 Transações e Contabilidade continuam no bundle',()=>{assert(app.includes('function crmTransactionsPage()'));assert(app.includes('function crmAccountingPage()'));});
  test('52 CSS fiscal responsivo está publicado',()=>{assert(bundleCss.includes('/* VALTREN FISCAL DOCUMENTS */'));for(const width of ['1380px','1050px','760px','520px'])assert(bundleCss.includes(`max-width:${width}`));});
}
console.log(`Fiscal documents UI tests: ${passed} passed`);
