(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenFiscalCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const SCHEMA_VERSION=1;
  const DIRECTIONS=['incoming','outgoing'];
  const DOCUMENT_TYPES=['service','product','other'];
  const STATUSES=['draft','pending','issued','received','cancelled','rejected','archived'];
  const SOURCES=['manual','import','integration'];
  const FINANCIAL_STATUSES=['unlinked','pending','partial','settled'];
  const FILE_KINDS=['xml','pdf','receipt','proof','contract','other'];

  const clone=(value)=>value==null?value:JSON.parse(JSON.stringify(value));
  const text=(value)=>String(value??'').trim().replace(/\s+/g,' ');
  const fold=(value)=>text(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const num=(value)=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0;};
  const money=(value)=>Math.round((num(value)+Number.EPSILON)*100)/100;
  const nonNegative=(value,label)=>{const parsed=Number(value??0);if(!Number.isFinite(parsed)||parsed<0)throw new Error(`${label} inválido`);return money(parsed);};
  const moneyEqual=(a,b)=>Math.abs(money(a)-money(b))<0.005;
  const isoDate=(value)=>{const v=text(value);return !v||/^\d{4}-\d{2}-\d{2}$/.test(v)?v:'';};
  const normalizeAccessKey=(value)=>text(value).replace(/[^0-9A-Za-z]/g,'').toUpperCase();
  const isLikelyNfeAccessKey=(value)=>/^\d{44}$/.test(normalizeAccessKey(value));
  const normalizeHash=(value)=>text(value).replace(/\s+/g,'').toLowerCase();
  function defaultId(prefix){const token=(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():`${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;return `${prefix}_${token}`;}

  function createState(){
    return {
      schemaVersion:SCHEMA_VERSION,
      documents:[],
      items:[],
      taxes:[],
      retentions:[],
      links:[],
      attachments:[],
      history:[],
      imports:[],
      metadata:{legacyReviewed:false,legacyInvoiceUnresolvedCount:0}
    };
  }
  function ensureState(input){
    const data=input&&typeof input==='object'?input:createState(),template=createState();
    for(const [key,value] of Object.entries(template))if(Array.isArray(value)&&!Array.isArray(data[key]))data[key]=[];
    if(!data.metadata||typeof data.metadata!=='object')data.metadata={};
    data.schemaVersion=SCHEMA_VERSION;
    return data;
  }

  function createService(store,options={}){
    const data=ensureState(store);
    const now=options.now||(()=>new Date().toISOString());
    const idFactory=options.idFactory||defaultId;
    const actor=options.actorProvider||(()=>null);
    const party=options.partyService||null;
    const finance=options.financeService||null;
    const companyProvider=options.companyProvider||(()=>null);
    const defaultCurrencyProvider=options.defaultCurrencyProvider||(()=>'BRL');
    const integrationValidator=options.integrationValidator||(()=>false);

    const getDocument=(id)=>data.documents.find((row)=>row.id===id)||null;
    const getItem=(id)=>data.items.find((row)=>row.id===id)||null;
    const getTax=(id)=>data.taxes.find((row)=>row.id===id)||null;
    const getRetention=(id)=>data.retentions.find((row)=>row.id===id)||null;
    const getLink=(id)=>data.links.find((row)=>row.id===id)||null;
    const documentItems=(id)=>data.items.filter((row)=>row.documentId===id);
    const documentTaxes=(id)=>data.taxes.filter((row)=>row.documentId===id);
    const documentRetentions=(id)=>data.retentions.filter((row)=>row.documentId===id);
    const documentLinks=(id)=>data.links.filter((row)=>row.documentId===id&&row.status==='active');
    const documentAttachments=(id)=>data.attachments.filter((row)=>row.documentId===id&&row.status!=='removed');
    const history=(action,documentId,before,after,metadata={})=>{
      const event={id:idFactory('fishist'),action,documentId:documentId||'',at:now(),actorId:actor()||null,before:clone(before),after:clone(after),metadata:clone(metadata)};
      data.history.push(event);return event;
    };
    const touch=(row)=>{row.updatedAt=now();row.updatedBy=actor()||null;return row;};

    function assertDirection(value){if(!DIRECTIONS.includes(value))throw new Error('Direção fiscal inválida');return value;}
    function assertDocumentType(value){const type=DOCUMENT_TYPES.includes(value)?value:'other';return type;}
    function assertStatus(value){if(!STATUSES.includes(value))throw new Error('Status fiscal inválido');return value;}
    function assertSource(value){if(!SOURCES.includes(value))throw new Error('Origem fiscal inválida');return value;}
    function assertDate(value,label){const raw=text(value);if(raw&&!isoDate(raw))throw new Error(`${label} inválida`);return raw;}
    function assertParty(type,id,label='Parte'){
      if(!id)return null;
      if(!['person','organization'].includes(type))throw new Error(`${label}: tipo canônico inválido`);
      if(!party||!party.getEntity(type,id))throw new Error(`${label}: Pessoa/Organização canônica não encontrada`);
      return party.getEntity(type,id);
    }
    function partyLabel(type,id){
      const entity=id&&party?.getEntity(type,id);
      if(!entity)return id||'';
      return type==='person'?entity.fullName:(entity.tradeName||entity.legalName||entity.name||id);
    }
    function normalizePartyRef(type,id,label){
      const t=text(type),key=text(id);
      if(key)assertParty(t,key,label);
      return {type:key?t:'',id:key};
    }

    function normalizeItem(input={},index=0){
      const quantity=input.quantity==null||input.quantity===''?1:Number(input.quantity);
      if(!Number.isFinite(quantity)||quantity<=0)throw new Error(`Item ${index+1}: quantidade inválida`);
      const unitPrice=nonNegative(input.unitPrice??0,`Item ${index+1}: valor unitário`);
      const grossProvided=input.grossAmount!=null&&input.grossAmount!=='';
      const grossAmount=grossProvided?nonNegative(input.grossAmount,`Item ${index+1}: valor bruto`):money(quantity*unitPrice);
      const discountAmount=nonNegative(input.discountAmount??0,`Item ${index+1}: desconto`);
      if(discountAmount>grossAmount+0.005)throw new Error(`Item ${index+1}: desconto excede o valor bruto`);
      const computedTotal=money(grossAmount-discountAmount);
      const totalProvided=input.totalAmount!=null&&input.totalAmount!=='';
      const totalAmount=totalProvided?nonNegative(input.totalAmount,`Item ${index+1}: total`):computedTotal;
      const taxableAmount=input.taxableAmount==null||input.taxableAmount===''?computedTotal:nonNegative(input.taxableAmount,`Item ${index+1}: base tributável`);
      const reconciliationIssues=[];
      if(totalProvided&&!moneyEqual(totalAmount,computedTotal))reconciliationIssues.push('item_total_mismatch');
      return {
        id:input.id||idFactory('fitem'),
        description:text(input.description)||`Item ${index+1}`,
        quantity,
        unit:text(input.unit||'un'),
        unitPrice,
        grossAmount,
        discountAmount,
        taxableAmount,
        totalAmount,
        productId:text(input.productId),
        serviceId:text(input.serviceId),
        metadata:clone(input.metadata||{}),
        reconciliationIssues
      };
    }
    function normalizeTax(input={},index=0){
      const baseAmount=nonNegative(input.baseAmount??0,`Tributo ${index+1}: base`);
      const rate=input.rate==null||input.rate===''?null:Number(input.rate);
      if(rate!=null&&(!Number.isFinite(rate)||rate<0))throw new Error(`Tributo ${index+1}: alíquota inválida`);
      const amount=nonNegative(input.amount??0,`Tributo ${index+1}: valor`);
      const treatment=input.treatment==='added'?'added':'informational';
      return {id:input.id||idFactory('ftax'),taxType:text(input.taxType||input.type)||'Outro',taxCode:text(input.taxCode||input.code),baseAmount,rate,amount,withheld:!!input.withheld,treatment,metadata:clone(input.metadata||{})};
    }
    function normalizeRetention(input={},index=0){
      const baseAmount=nonNegative(input.baseAmount??0,`Retenção ${index+1}: base`);
      const rate=input.rate==null||input.rate===''?null:Number(input.rate);
      if(rate!=null&&(!Number.isFinite(rate)||rate<0))throw new Error(`Retenção ${index+1}: alíquota inválida`);
      const amount=nonNegative(input.amount??0,`Retenção ${index+1}: valor`);
      if(baseAmount>0&&amount>baseAmount+0.005)throw new Error(`Retenção ${index+1}: valor excede a base`);
      return {id:input.id||idFactory('fret'),type:text(input.type)||'Outra',baseAmount,rate,amount,metadata:clone(input.metadata||{})};
    }
    function normalizeAttachment(input={},index=0){
      const kind=FILE_KINDS.includes(input.kind)?input.kind:'other';
      return {
        id:input.id||idFactory('fatt'),
        kind,
        fileName:text(input.fileName),
        mimeType:text(input.mimeType),
        source:text(input.source||'metadata'),
        hash:normalizeHash(input.hash),
        uploadedAt:input.uploadedAt||now(),
        storageReference:text(input.storageReference),
        status:'active',
        metadata:clone(input.metadata||{}),
        index
      };
    }

    function computeTotals(input,items,taxes,retentions){
      const itemGross=money(items.reduce((sum,row)=>sum+row.grossAmount,0));
      const itemDiscount=money(items.reduce((sum,row)=>sum+row.discountAmount,0));
      const itemNet=money(items.reduce((sum,row)=>sum+row.totalAmount,0));
      const taxAmount=money(taxes.reduce((sum,row)=>sum+row.amount,0));
      const addedTaxAmount=money(taxes.filter((row)=>row.treatment==='added'&&!row.withheld).reduce((sum,row)=>sum+row.amount,0));
      const retentionByRows=money(retentions.reduce((sum,row)=>sum+row.amount,0));
      const documentDiscount=nonNegative(input.discountAmount??0,'Desconto');
      const deductionAmount=nonNegative(input.deductionAmount??0,'Deduções');
      const subtotalProvided=input.subtotal!=null&&input.subtotal!=='';
      const subtotal=subtotalProvided?nonNegative(input.subtotal,'Subtotal'):(items.length?itemGross:nonNegative(input.totalAmount??0,'Subtotal'));
      const computedTotal=money((items.length?itemNet:subtotal)-documentDiscount-deductionAmount+addedTaxAmount);
      if(computedTotal<-.005)throw new Error('Total fiscal calculado não pode ser negativo');
      const totalProvided=input.totalAmount!=null&&input.totalAmount!=='';
      const totalAmount=totalProvided?nonNegative(input.totalAmount,'Total'):Math.max(0,computedTotal);
      const retentionProvided=input.retentionAmount!=null&&input.retentionAmount!=='';
      const retentionAmount=retentionProvided?nonNegative(input.retentionAmount,'Retenções'):retentionByRows;
      if(retentionAmount>totalAmount+0.005)throw new Error('Retenções excedem o total do documento');
      const netComputed=money(totalAmount-retentionAmount);
      const netProvided=input.netAmount!=null&&input.netAmount!=='';
      const netAmount=netProvided?nonNegative(input.netAmount,'Valor líquido'):netComputed;
      const taxProvided=input.taxAmount!=null&&input.taxAmount!=='';
      const reportedTaxAmount=taxProvided?nonNegative(input.taxAmount,'Tributos'):taxAmount;
      const issues=[];
      if(items.some((row)=>row.reconciliationIssues.length))issues.push('item_total_mismatch');
      if(items.length&&subtotalProvided&&!moneyEqual(subtotal,itemGross))issues.push('subtotal_items_mismatch');
      if(items.length&&totalProvided&&!moneyEqual(totalAmount,computedTotal))issues.push('total_calculation_mismatch');
      if(retentionProvided&&!moneyEqual(retentionAmount,retentionByRows))issues.push('retention_total_mismatch');
      if(taxProvided&&!moneyEqual(reportedTaxAmount,taxAmount))issues.push('tax_total_mismatch');
      if(netProvided&&!moneyEqual(netAmount,netComputed))issues.push('net_total_mismatch');
      return {
        subtotal,
        itemGrossAmount:itemGross,
        itemDiscountAmount:itemDiscount,
        discountAmount:documentDiscount,
        deductionAmount,
        taxAmount:reportedTaxAmount,
        retentionAmount,
        totalAmount,
        netAmount,
        calculatedTotalAmount:Math.max(0,computedTotal),
        calculatedNetAmount:netComputed,
        reconciliationStatus:issues.length?'inconsistent':'reconciled',
        reconciliationIssues:issues
      };
    }

    function duplicateSignals(input={}){
      const accessKey=normalizeAccessKey(input.accessKey);
      const externalId=text(input.externalId);
      const xmlHash=normalizeHash(input.xmlMetadata?.hash||input.xmlHash||'');
      const number=text(input.number),series=text(input.series),direction=input.direction;
      const issuerPartyId=text(input.issuerPartyId),recipientPartyId=text(input.recipientPartyId);
      const strong=[],potential=[];
      for(const row of data.documents){
        if(row.status==='archived')continue;
        if(accessKey&&row.accessKey&&row.accessKey===accessKey)strong.push({id:row.id,reason:'access_key'});
        else if(externalId&&row.externalId&&row.externalId===externalId)strong.push({id:row.id,reason:'external_id'});
        else {
          const rowXml=documentAttachments(row.id).find((a)=>a.kind==='xml'&&a.hash);
          if(xmlHash&&rowXml?.hash===xmlHash)strong.push({id:row.id,reason:'xml_hash'});
          else if(number&&row.number===number&&row.series===series&&row.direction===direction&&
                  ((!issuerPartyId&&!row.issuerPartyId)||row.issuerPartyId===issuerPartyId)&&
                  ((!recipientPartyId&&!row.recipientPartyId)||row.recipientPartyId===recipientPartyId)){
            potential.push({id:row.id,reason:'party_number_series'});
          }
        }
      }
      return {strong,potential};
    }

    function resolveCompany(){
      const company=companyProvider()||null;
      const type=text(company?.partyType);
      const id=text(company?.partyId);
      const entity=id&&['person','organization'].includes(type)&&party?.getEntity(type,id)?party.getEntity(type,id):null;
      const required=['legalName','document','address'].filter((key)=>!text(company?.[key]));
      return {company,partyType:entity?type:'',partyId:entity?id:'',entity,missingInstitutionalFields:required};
    }

    function createDocument(input={},opts={}){
      const direction=assertDirection(input.direction);
      const documentType=assertDocumentType(input.documentType||'other');
      const source=assertSource(input.source||'manual');
      const status=assertStatus(input.status||'draft');
      if(status==='issued'&&direction!=='outgoing')throw new Error('Status Emitida é aplicável a Nota de Saída');
      if(status==='received'&&direction!=='incoming')throw new Error('Status Recebida é aplicável a Nota de Entrada');
      if(status!=='draft'&&!text(input.issueDate))throw new Error('Data de emissão é obrigatória fora de rascunho');
      const issueDate=assertDate(input.issueDate,'Data de emissão');
      const competenceDate=assertDate(input.competenceDate,'Competência fiscal');
      const receivedAt=input.receivedAt||null;
      const authorizedAt=input.authorizedAt||null;
      if(authorizedAt&&!integrationValidator(input.sourceReference))throw new Error('Autorização fiscal não pode ser registrada sem integração validada');
      const counterparty=normalizePartyRef(input.counterpartyType,input.counterpartyId,direction==='incoming'?'Fornecedor/Emitente':'Cliente/Tomador');
      if(!counterparty.id&&!opts.allowMissingCounterparty)throw new Error(direction==='incoming'?'Fornecedor/Emitente é obrigatório':'Cliente/Tomador é obrigatório');

      const company=resolveCompany();
      let issuer=normalizePartyRef(input.issuerPartyType,input.issuerPartyId,'Emitente');
      let recipient=normalizePartyRef(input.recipientPartyType,input.recipientPartyId,'Destinatário');
      if(direction==='incoming'&&!issuer.id)issuer=counterparty;
      if(direction==='outgoing'&&!recipient.id)recipient=counterparty;
      if(direction==='outgoing'&&!issuer.id&&company.partyId)issuer={type:company.partyType,id:company.partyId};
      if(direction==='incoming'&&!recipient.id&&company.partyId)recipient={type:company.partyType,id:company.partyId};

      const customer=direction==='outgoing'?counterparty:normalizePartyRef(input.customerPartyType,input.customerPartyId,'Cliente');
      const supplier=direction==='incoming'?counterparty:normalizePartyRef(input.supplierPartyType,input.supplierPartyId,'Fornecedor');
      const items=(Array.isArray(input.items)?input.items:[]).filter((row)=>row&&Object.values(row).some((value)=>text(value))).map(normalizeItem);
      const taxes=(Array.isArray(input.taxes)?input.taxes:[]).filter((row)=>row&&Object.values(row).some((value)=>text(value))).map(normalizeTax);
      const retentions=(Array.isArray(input.retentions)?input.retentions:[]).filter((row)=>row&&Object.values(row).some((value)=>text(value))).map(normalizeRetention);
      const totals=computeTotals(input,items,taxes,retentions);
      if(source==='manual'&&totals.reconciliationIssues.length&&!opts.allowInconsistentTotals){
        const error=new Error(`Totais não reconciliam: ${totals.reconciliationIssues.join(', ')}`);
        error.code='FISCAL_TOTAL_MISMATCH';throw error;
      }

      const xmlMetadata=clone(input.xmlMetadata||{});
      const pdfMetadata=clone(input.pdfMetadata||{});
      const attachments=(Array.isArray(input.attachments)?input.attachments:[]).map(normalizeAttachment);
      if(Object.keys(xmlMetadata).length)attachments.push(normalizeAttachment({kind:'xml',...xmlMetadata},attachments.length));
      if(Object.keys(pdfMetadata).length)attachments.push(normalizeAttachment({kind:'pdf',...pdfMetadata},attachments.length));
      const candidateForDup={
        ...input,direction,issuerPartyId:issuer.id,recipientPartyId:recipient.id,
        xmlMetadata
      };
      const duplicates=duplicateSignals(candidateForDup);
      if(duplicates.strong.length&&!opts.allowDuplicate){
        const error=new Error('Documento fiscal duplicado por identificador forte');
        error.code='DUPLICATE_FISCAL_DOCUMENT';error.matches=duplicates.strong;throw error;
      }

      const accessKey=normalizeAccessKey(input.accessKey);
      const integrationValidated=source==='integration'&&integrationValidator(input.sourceReference);
      const row={
        id:input.id||idFactory('fdoc'),
        direction,documentType,model:text(input.model),
        number:text(input.number),series:text(input.series),externalId:text(input.externalId),accessKey,
        accessKeyValid:accessKey?isLikelyNfeAccessKey(accessKey):null,
        status,issueDate,competenceDate,receivedAt,authorizedAt:integrationValidated?authorizedAt:null,cancelledAt:null,
        issuerPartyType:issuer.type,issuerPartyId:issuer.id,
        recipientPartyType:recipient.type,recipientPartyId:recipient.id,
        customerPartyType:customer.type,customerPartyId:customer.id,
        supplierPartyType:supplier.type,supplierPartyId:supplier.id,
        serviceProviderPartyType:text(input.serviceProviderPartyType),serviceProviderPartyId:text(input.serviceProviderPartyId),
        serviceRecipientPartyType:text(input.serviceRecipientPartyType),serviceRecipientPartyId:text(input.serviceRecipientPartyId),
        counterpartyType:counterparty.type,counterpartyId:counterparty.id,
        currency:text(input.currency||defaultCurrencyProvider()||'BRL').toUpperCase(),
        ...totals,
        description:text(input.description),
        productId:text(input.productId),serviceId:text(input.serviceId),businessUnitId:text(input.businessUnitId),contractId:text(input.contractId),
        notes:text(input.notes),
        source,sourceReference:text(input.sourceReference),integrationValidated,
        isDemo:!!input.isDemo,
        potentialDuplicate:duplicates.potential.length>0,
        potentialDuplicateMatches:clone(duplicates.potential),
        missingInstitutionalData:company.missingInstitutionalFields.length>0||!company.partyId,
        institutionalPendingFields:clone(company.missingInstitutionalFields),
        metadata:{...(input.metadata||{}),legacyInvoiceId:text(input.legacyInvoiceId)},
        createdAt:now(),updatedAt:now(),createdBy:actor()||null,updatedBy:actor()||null
      };
      data.documents.push(row);
      for(const item of items)data.items.push({...item,documentId:row.id,createdAt:now(),updatedAt:now()});
      for(const tax of taxes)data.taxes.push({...tax,documentId:row.id,createdAt:now(),updatedAt:now()});
      for(const retention of retentions)data.retentions.push({...retention,documentId:row.id,createdAt:now(),updatedAt:now()});
      for(const attachment of attachments)data.attachments.push({...attachment,documentId:row.id,createdAt:now(),updatedAt:now()});
      history(source==='import'?'document.imported':'document.created',row.id,null,row,{source,reconciliationStatus:row.reconciliationStatus});
      return row;
    }

    function updateDocument(id,input={},opts={}){
      const current=getDocument(id);if(!current)throw new Error('Nota Fiscal não encontrada');
      const before=clone(current);
      const merged={
        ...current,...input,
        items:'items'in input?input.items:documentItems(id),
        taxes:'taxes'in input?input.taxes:documentTaxes(id),
        retentions:'retentions'in input?input.retentions:documentRetentions(id),
        attachments:'attachments'in input?input.attachments:documentAttachments(id),
        source:current.source,
        id:current.id
      };
      const shadowStore=createState();
      const shadow=createService(shadowStore,{...options,partyService:party,financeService:finance,companyProvider,defaultCurrencyProvider,integrationValidator,now,idFactory,actorProvider:actor});
      const normalized=shadow.createDocument(merged,{...opts,allowDuplicate:true,allowMissingCounterparty:true,allowInconsistentTotals:opts.allowInconsistentTotals??current.source!=='manual'});
      const mutable=[
        'direction','documentType','model','number','series','externalId','accessKey','accessKeyValid','status','issueDate','competenceDate','receivedAt',
        'issuerPartyType','issuerPartyId','recipientPartyType','recipientPartyId','customerPartyType','customerPartyId','supplierPartyType','supplierPartyId',
        'serviceProviderPartyType','serviceProviderPartyId','serviceRecipientPartyType','serviceRecipientPartyId','counterpartyType','counterpartyId','currency',
        'subtotal','itemGrossAmount','itemDiscountAmount','discountAmount','deductionAmount','taxAmount','retentionAmount','totalAmount','netAmount',
        'calculatedTotalAmount','calculatedNetAmount','reconciliationStatus','reconciliationIssues','description','productId','serviceId','businessUnitId',
        'contractId','notes','potentialDuplicate','potentialDuplicateMatches','missingInstitutionalData','institutionalPendingFields','metadata'
      ];
      for(const key of mutable)current[key]=clone(normalized[key]);
      touch(current);

      data.items=data.items.filter((row)=>row.documentId!==id);
      data.taxes=data.taxes.filter((row)=>row.documentId!==id);
      data.retentions=data.retentions.filter((row)=>row.documentId!==id);
      if('attachments'in input)data.attachments=data.attachments.filter((row)=>row.documentId!==id);
      for(const item of shadow.documentItems(normalized.id))data.items.push({...clone(item),id:idFactory('fitem'),documentId:id,createdAt:now(),updatedAt:now()});
      for(const tax of shadow.documentTaxes(normalized.id))data.taxes.push({...clone(tax),id:idFactory('ftax'),documentId:id,createdAt:now(),updatedAt:now()});
      for(const retention of shadow.documentRetentions(normalized.id))data.retentions.push({...clone(retention),id:idFactory('fret'),documentId:id,createdAt:now(),updatedAt:now()});
      if('attachments'in input)for(const attachment of shadow.documentAttachments(normalized.id))data.attachments.push({...clone(attachment),id:idFactory('fatt'),documentId:id,createdAt:now(),updatedAt:now()});
      history('document.updated',id,before,current);
      return current;
    }

    function changeStatus(id,status,metadata={}){
      const row=getDocument(id);if(!row)throw new Error('Nota Fiscal não encontrada');
      const next=assertStatus(status),before=clone(row);
      if(next==='cancelled'){row.cancelledAt=metadata.cancelledAt||now();row.metadata={...(row.metadata||{}),cancellationSource:text(metadata.source||'manual-record'),cancellationReference:text(metadata.reference)};}
      row.status=next;touch(row);history('document.status.changed',id,before,row,{status:next,...metadata});return row;
    }
    function markCancelled(id,metadata={}){return changeStatus(id,'cancelled',{source:'manual-record',...metadata});}
    function archive(id,reason=''){const row=getDocument(id);if(!row)throw new Error('Nota Fiscal não encontrada');const before=clone(row);row.status='archived';row.metadata={...(row.metadata||{}),archiveReason:text(reason)};touch(row);history('document.archived',id,before,row,{reason:text(reason)});return row;}

    function addAttachment(documentId,input={}){
      const row=getDocument(documentId);if(!row)throw new Error('Nota Fiscal não encontrada');
      const attachment={...normalizeAttachment(input),documentId,createdAt:now(),updatedAt:now()};
      data.attachments.push(attachment);history('document.attachment.added',documentId,null,attachment,{kind:attachment.kind});return attachment;
    }
    function removeAttachment(id){
      const attachment=data.attachments.find((row)=>row.id===id);if(!attachment)return false;
      const before=clone(attachment);attachment.status='removed';attachment.updatedAt=now();history('document.attachment.removed',attachment.documentId,before,attachment);return true;
    }

    function linkTransaction(documentId,transactionId,metadata={}){
      const doc=getDocument(documentId);if(!doc)throw new Error('Nota Fiscal não encontrada');
      if(!finance)throw new Error('Serviço financeiro indisponível');
      const tx=finance.getTransaction(transactionId);if(!tx)throw new Error('Transação não encontrada');
      let existing=data.links.find((row)=>row.documentId===documentId&&row.transactionId===transactionId&&row.status==='active');
      if(existing)return existing;
      const match=finance.addMatch(transactionId,{targetType:'fiscal_document',targetId:documentId,amount:metadata.amount==null?tx.amount:metadata.amount});
      const link={id:idFactory('flink'),documentId,transactionId,matchId:match?.id||'',status:'active',createdAt:now(),createdBy:actor()||null,metadata:clone(metadata)};
      data.links.push(link);history('document.transaction.linked',documentId,null,link,{transactionId,matchId:link.matchId});return link;
    }
    function unlinkTransaction(documentId,transactionId){
      const link=data.links.find((row)=>row.documentId===documentId&&row.transactionId===transactionId&&row.status==='active');
      if(!link)return false;
      const before=clone(link);link.status='inactive';link.updatedAt=now();if(link.matchId&&finance)finance.removeMatch(link.matchId);
      history('document.transaction.unlinked',documentId,before,link,{transactionId});return true;
    }
    function eligibleSettlementTransaction(tx){return !!tx&&tx.status==='posted'&&!tx.isDemo&&tx.financialNature!=='transfer';}
    function settlementEffect(doc,tx){
      if(!eligibleSettlementTransaction(tx))return 0;
      const expected=doc.direction==='outgoing'?'inflow':'outflow';
      return money(tx.direction===expected?tx.amount:-tx.amount);
    }
    function settlement(documentId){
      const doc=getDocument(documentId);if(!doc)throw new Error('Nota Fiscal não encontrada');
      const links=documentLinks(documentId),rows=links.map((link)=>({link,tx:finance?.getTransaction(link.transactionId)||null}));
      const eligible=rows.filter(({tx})=>eligibleSettlementTransaction(tx));
      const settledAmount=money(eligible.reduce((sum,{tx})=>sum+settlementEffect(doc,tx),0));
      const effective=Math.max(0,settledAmount),balance=money(Math.max(0,doc.netAmount-effective));
      let status='unlinked';
      if(links.length)status=eligible.length?'pending':'pending';
      if(effective>0&&effective+0.005<doc.netAmount)status='partial';
      if(doc.netAmount===0||effective+0.005>=doc.netAmount)status='settled';
      return {status,linkedCount:links.length,eligibleCount:eligible.length,settledAmount:effective,rawSettlementAmount:settledAmount,balance,rows};
    }

    function suggestionScore(doc,tx){
      if(!eligibleSettlementTransaction(tx))return {score:-1,reasons:[]};
      let score=0;const reasons=[];
      const expected=doc.direction==='outgoing'?'inflow':'outflow';
      if(tx.direction===expected){score+=4;reasons.push('direção');}
      if(moneyEqual(tx.amount,doc.netAmount)){score+=4;reasons.push('valor');}
      else if(Math.abs(tx.amount-doc.netAmount)<=Math.max(1,doc.netAmount*0.1)){score+=2;reasons.push('valor aproximado');}
      if(doc.counterpartyId&&tx.counterpartyId===doc.counterpartyId){score+=3;reasons.push('contraparte');}
      const dateA=new Date(doc.issueDate||doc.createdAt),dateB=new Date(tx.transactionDate||tx.createdAt),days=Math.abs((dateA-dateB)/86400000);
      if(Number.isFinite(days)&&days<=7){score+=2;reasons.push('data');}else if(Number.isFinite(days)&&days<=30){score+=1;reasons.push('período');}
      const blob=fold([tx.originalDescription,tx.normalizedDescription,tx.externalId].join(' '));
      if(doc.number&&blob.includes(fold(doc.number))){score+=2;reasons.push('número');}
      return {score,reasons};
    }
    function suggestTransactions(documentId,limit=8){
      const doc=getDocument(documentId);if(!doc)throw new Error('Nota Fiscal não encontrada');
      if(!finance)return [];
      const linked=new Set(documentLinks(documentId).map((row)=>row.transactionId));
      return finance.query({status:'posted',includeDemo:false,limit:0}).rows
        .filter((tx)=>!linked.has(tx.id)&&tx.financialNature!=='transfer')
        .map((tx)=>({tx,...suggestionScore(doc,tx)}))
        .filter((row)=>row.score>0)
        .sort((a,b)=>b.score-a.score||String(b.tx.transactionDate).localeCompare(String(a.tx.transactionDate)))
        .slice(0,Math.max(1,Number(limit)||8));
    }

    function searchBlob(doc){
      return fold([
        doc.number,doc.series,doc.accessKey,doc.externalId,doc.description,doc.totalAmount,doc.netAmount,doc.currency,
        partyLabel(doc.issuerPartyType,doc.issuerPartyId),partyLabel(doc.recipientPartyType,doc.recipientPartyId),
        partyLabel(doc.counterpartyType,doc.counterpartyId)
      ].join(' '));
    }
    function list(filters={}){
      let rows=data.documents.filter((row)=>filters.includeDemo?true:!row.isDemo).filter((row)=>filters.includeArchived?true:row.status!=='archived');
      if(filters.direction)rows=rows.filter((row)=>row.direction===filters.direction);
      if(filters.status)rows=rows.filter((row)=>row.status===filters.status);
      if(filters.partyId)rows=rows.filter((row)=>[row.counterpartyId,row.issuerPartyId,row.recipientPartyId].includes(filters.partyId));
      if(filters.productId)rows=rows.filter((row)=>row.productId===filters.productId||documentItems(row.id).some((item)=>item.productId===filters.productId));
      if(filters.serviceId)rows=rows.filter((row)=>row.serviceId===filters.serviceId||documentItems(row.id).some((item)=>item.serviceId===filters.serviceId));
      if(filters.businessUnitId)rows=rows.filter((row)=>row.businessUnitId===filters.businessUnitId);
      if(filters.linked==='yes')rows=rows.filter((row)=>documentLinks(row.id).length>0);
      if(filters.linked==='no')rows=rows.filter((row)=>documentLinks(row.id).length===0);
      if(filters.financialStatus)rows=rows.filter((row)=>settlement(row.id).status===filters.financialStatus);
      if(filters.from)rows=rows.filter((row)=>(row.issueDate||row.createdAt.slice(0,10))>=filters.from);
      if(filters.to)rows=rows.filter((row)=>(row.issueDate||row.createdAt.slice(0,10))<=filters.to);
      if(filters.search){const needle=fold(filters.search);rows=rows.filter((row)=>searchBlob(row).includes(needle));}
      rows.sort((a,b)=>String(b.issueDate||b.createdAt).localeCompare(String(a.issueDate||a.createdAt))||String(b.createdAt).localeCompare(String(a.createdAt)));
      const total=rows.length,offset=Math.max(0,Number(filters.offset)||0);
      if(filters.limit===0)return {total,rows};
      const limit=Math.max(1,Number(filters.limit)||50);
      return {total,rows:rows.slice(offset,offset+limit)};
    }

    function accountingFeed(filters={}){
      return list({...filters,limit:0}).rows.map((doc)=>({
        fiscalDocumentId:doc.id,
        direction:doc.direction,
        status:doc.status,
        issueDate:doc.issueDate,
        competenceDate:doc.competenceDate,
        currency:doc.currency,
        totalAmount:doc.totalAmount,
        netAmount:doc.netAmount,
        taxes:clone(documentTaxes(doc.id)),
        retentions:clone(documentRetentions(doc.id)),
        transactionIds:documentLinks(doc.id).map((link)=>link.transactionId),
        productId:doc.productId,
        serviceId:doc.serviceId,
        businessUnitId:doc.businessUnitId,
        isDemo:doc.isDemo
      }));
    }

    function migrateLegacy(rows=[]){
      if(data.metadata.legacyReviewed)return 0;
      let migrated=0,unresolved=0;
      for(const legacy of rows||[]){
        if(!legacy||typeof legacy!=='object')continue;
        if(data.documents.some((row)=>row.metadata?.legacyInvoiceId&&row.metadata.legacyInvoiceId===String(legacy.id||'')))continue;
        const explicitlyFiscal=legacy.fiscalDocument===true||legacy.canonicalFiscal===true||legacy.accessKey||legacy.xmlMetadata;
        const counterpartyType=text(legacy.counterpartyType);
        const counterpartyId=text(legacy.counterpartyId);
        if(!explicitlyFiscal||!counterpartyId||!['person','organization'].includes(counterpartyType)||!party?.getEntity(counterpartyType,counterpartyId)){unresolved++;continue;}
        try{
          createDocument({
            direction:legacy.direction==='incoming'?'incoming':'outgoing',
            documentType:legacy.documentType||legacy.invoiceType||'other',
            number:legacy.number,series:legacy.series,externalId:legacy.externalId,accessKey:legacy.accessKey,
            status:legacy.status==='received'?'received':legacy.status==='issued'?'issued':'draft',
            issueDate:legacy.issueDate||legacy.date||'',competenceDate:legacy.competenceDate||'',
            counterpartyType,counterpartyId,currency:legacy.currency||defaultCurrencyProvider(),
            subtotal:legacy.subtotal,totalAmount:legacy.totalAmount??Math.abs(Number(legacy.value||0)),netAmount:legacy.netAmount,
            description:legacy.description,notes:legacy.notes,source:'manual',
            isDemo:legacy.isDemo!==false,legacyInvoiceId:String(legacy.id||''),metadata:{legacySnapshot:clone(legacy),legacySemanticReview:'explicit-fiscal'}
          },{allowInconsistentTotals:true,allowMissingCounterparty:false});
          migrated++;
        }catch{unresolved++;}
      }
      data.metadata.legacyReviewed=true;
      data.metadata.legacyReviewedAt=now();
      data.metadata.legacyInvoiceUnresolvedCount=unresolved;
      return migrated;
    }

    return {
      data,getDocument,getItem,getTax,getRetention,getLink,documentItems,documentTaxes,documentRetentions,documentLinks,documentAttachments,
      createDocument,updateDocument,changeStatus,markCancelled,archive,addAttachment,removeAttachment,
      linkTransaction,unlinkTransaction,eligibleSettlementTransaction,settlementEffect,settlement,suggestTransactions,list,accountingFeed,migrateLegacy,
      duplicateSignals,computeTotals,partyLabel,history
    };
  }

  return {
    SCHEMA_VERSION,DIRECTIONS,DOCUMENT_TYPES,STATUSES,SOURCES,FINANCIAL_STATUSES,FILE_KINDS,
    createState,ensureState,createService,text,fold,num,money,moneyEqual,normalizeAccessKey,isLikelyNfeAccessKey
  };
});