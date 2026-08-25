# Financeiro → Notas Fiscais — Arquitetura Canônica

Esta documentação registra exclusivamente a implementação de `Financeiro → Notas Fiscais`.

## Responsabilidade e ownership

Notas Fiscais é a fonte operacional dos documentos fiscais da Valtren. O módulo não é uma segunda base financeira e não substitui Contabilidade.

```text
Documento fiscal      → Notas Fiscais
Movimentação bancária → Financeiro → Transações
DRE / competência     → Financeiro → Contabilidade
Pessoa / Organização  → infraestrutura canônica + CRM
Produto / Serviço     → Negócios
Contrato               → Jurídico
```

A fonte fiscal canônica é:

```text
state.crmFiscalDocuments
ValtrenFiscalCore.createService()
```

Ela possui uma única estrutura com:

```text
documents
items
taxes
retentions
links
attachments
history
imports
metadata
```

Não existem fontes paralelas `incomingInvoices`, `outgoingInvoices`, `nfes`, `nfses`, `customerInvoices` ou `supplierInvoices`.

## Invoice legado

O legado `crmRefInvoices`, `crmRefInvoicesPage()` e `crmRefInvoiceModal()` era uma implementação de referência independente, com status que misturavam emissão e pagamento e campos fiscais hardcoded.

A página e o modal legados deixam de ser executáveis no bundle materializado. `crmRefInvoices` pode ser lido somente uma vez pelo adapter de compatibilidade.

A migração é deliberadamente conservadora:

- registro legado ambíguo não é convertido automaticamente;
- somente registro explicitamente marcado como fiscal (`canonicalFiscal`, `fiscalDocument`, access key/XML) pode ser adaptado;
- a contraparte precisa apontar para Pessoa/Organização canônica existente;
- dados sem confirmação permanecem contabilizados como `legacyInvoiceUnresolvedCount`;
- legado adaptado sem `isDemo=false` é tratado como demo/unverified e não aparece em totais reais.

A rota legada:

```text
#/crm/financeiro/invoices
```

é mantida apenas como alias. Ela normaliza para a rota canônica:

```text
#/crm/financeiro/notas-fiscais
```

sem criar um módulo `Invoices` no sidebar.

## Entrada única

Existe uma única ação principal:

```text
Criar Nota
```

O primeiro passo pergunta:

```text
Entrada
Saída
```

A direção fiscal fica persistida explicitamente como:

```text
incoming
outgoing
```

e não é inferida pelo sinal de uma transação financeira.

## Nota de Entrada

Representa documento recebido pela Valtren. A contraparte é selecionada exclusivamente da infraestrutura canônica de Pessoas/Organizações e normalmente ocupa o papel de fornecedor/emitente.

A liquidação esperada normalmente é uma transação `outflow`, mas isso é usado somente na análise/sugestão de correspondência.

## Nota de Saída

Representa documento emitido/cadastrado pela Valtren. A contraparte é selecionada da infraestrutura canônica e normalmente ocupa o papel de cliente/tomador.

A liquidação esperada normalmente é `inflow`, mas a criação da nota não gera nenhuma transação automaticamente.

`issued` significa **Emitida · registro interno**. Não representa autorização de SEFAZ/prefeitura.

## Partes canônicas

O domínio fiscal recebe `ValtrenPartyCore` através de `crmCanonicalPartyService()`.

São referências, nunca cadastros duplicados:

```text
counterpartyType / counterpartyId
issuerPartyType / issuerPartyId
recipientPartyType / recipientPartyId
customerPartyType / customerPartyId
supplierPartyType / supplierPartyId
serviceProviderPartyType / serviceProviderPartyId
serviceRecipientPartyType / serviceRecipientPartyId
```

A própria Valtren é resolvida, quando disponível, a partir dos dados institucionais de `Configurações → Empresa` e de uma eventual referência canônica `partyId`.

Nenhum CNPJ, razão social ou endereço institucional é hardcoded no módulo. Quando faltam dados, o documento recebe pendência `missingInstitutionalData` e a UI informa o problema.

## Documento fiscal

Campos principais:

```text
id
direction
documentType
model
number
series
externalId
accessKey
status
issueDate
competenceDate
receivedAt
authorizedAt
cancelledAt

partes canônicas
currency

subtotal
discountAmount
deductionAmount
taxAmount
retentionAmount
totalAmount
netAmount

productId
serviceId
businessUnitId
contractId

description
notes
source
sourceReference
integrationValidated
isDemo
reconciliationStatus
reconciliationIssues
potentialDuplicate
createdAt / updatedAt
createdBy / updatedBy
```

Itens, tributos, retenções, links e anexos vivem nas coleções canônicas relacionadas por `documentId`.

## Tipos documentais

A infraestrutura é extensível e atualmente usa tipos gerenciais genéricos:

```text
service → Nota Fiscal de Serviço
product → Nota Fiscal de Produto
other   → Outro Documento Fiscal
```

Não existe implementação simulada de NF-e/NFS-e/NFC-e, autorização fiscal ou DANFE legal.

## Itens e totais

Itens suportam:

```text
description
quantity
unit
unitPrice
grossAmount
discountAmount
taxableAmount
totalAmount
productId
serviceId
metadata
```

A implementação usa números normalizados e arredondados a duas casas para totais monetários.

Quando os valores são derivados:

```text
soma do total dos itens
- desconto do documento
- deduções do documento
+ tributos explicitamente marcados como "added"
= total fiscal calculado

total
- retenções
= líquido
```

Tributos informativos não são adicionados ao total por padrão.

Quando um documento manual informa valores incompatíveis, a operação é rejeitada.

Quando um documento importado/integrado traz valores incompatíveis, os valores reportados são preservados e o documento recebe:

```text
reconciliationStatus = inconsistent
reconciliationIssues[]
```

Nada é corrigido silenciosamente.

## Tributos

Tributos são dados explícitos:

```text
taxType
taxCode
baseAmount
rate
amount
withheld
treatment
metadata
```

Nenhuma alíquota é inventada ou inferida a partir de uma receita.

`treatment` permite distinguir tributo meramente informativo de valor explicitamente adicionado ao total do documento.

## Retenções

Retenções são estruturas separadas:

```text
type
baseAmount
rate
amount
metadata
```

O total de retenções reduz o valor líquido. A validação impede valor negativo e retenção superior à base quando uma base foi informada.

## Competência fiscal

`competenceDate` é própria do documento fiscal.

```text
Fiscal competenceDate
≠
Contabilidade recognitionDate
```

A implementação disponibiliza um selector de leitura:

```text
crmFiscalAccountingFeed()
```

que expõe competência, tributos, retenções e referências, sem escrever em `state.crmAccounting` e sem alterar a DRE automaticamente.

## Relação com Transações

A nota pode possuir zero, uma ou várias transações relacionadas.

A associação usa:

```text
Financeiro → Transações
ValtrenFinanceCore.addMatch()
targetType = fiscal_document
targetId   = fiscalDocumentId
```

e uma coleção fiscal de links que referencia apenas os IDs.

A criação da nota nunca chama `createTransaction()`.

## Liquidação derivada

Não existe `paidAmount` persistido.

O valor liquidado é calculado a partir de transações vinculadas que sejam:

```text
status = posted
isDemo = false
financialNature != transfer
```

Para Saída, `inflow` contribui positivamente e `outflow` negativamente.

Para Entrada, `outflow` contribui positivamente e `inflow` negativamente.

Com isso, reversões, refunds, reimbursements e chargebacks em direção oposta reduzem a liquidação.

Estados derivados:

```text
unlinked → Sem movimentação
pending  → Pendente
partial  → Parcial
settled  → Liquidada
```

O status fiscal permanece independente.

## Sugestões de match

Sugestões podem considerar:

```text
direção esperada
valor
contraparte
proximidade de data
número da nota na descrição
```

Nenhum vínculo é executado automaticamente. O usuário precisa confirmar `Vincular`.

## Deduplicação

Sinais fortes:

```text
accessKey
externalId
hash do XML
```

Sinal de potencial duplicidade:

```text
direção + parte + número + série
```

Sinais fortes bloqueiam duplicação. Sinais incertos produzem aviso `potentialDuplicate`.

A chave de acesso é normalizada e uma chave numérica de 44 dígitos pode ser reconhecida como formato provável, mas o sistema não gera chaves.

## XML, PDF e anexos

O stack atual não implementa storage fiscal.

Por isso o módulo armazena somente metadados/referências:

```text
kind
fileName
mimeType
source
hash
uploadedAt
storageReference
metadata
```

Não existe parser fiscal XML apresentado como validado, armazenamento fictício, DANFE falso ou PDF oficial inventado.

## Origem e integração

Origens:

```text
manual
import
integration
```

`integrationValidated` somente pode ser verdadeiro quando um `integrationValidator` real aprovar a referência. A implementação browser atual fornece `false`, porque não existe provedor fiscal conectado nesta etapa.

`authorizedAt` é rejeitado sem integração validada.

## Status fiscal

Status internos:

```text
draft
pending
issued
received
cancelled
rejected
archived
```

`issued` é registro interno.

`cancelled` criado pelo sistema significa apenas que o usuário registrou um cancelamento ocorrido externamente/manual; a interface usa a ação:

```text
Marcar como cancelada · registro
```

e informa que isso não executa cancelamento oficial.

## Produto, Serviço, Unidade e Contrato

São referências somente:

```text
productId
serviceId
businessUnitId
contractId
```

Os selects usam registros reais, quando disponíveis, dos respectivos owners. Se não houver dados, ficam sem opções reais.

Nenhum catálogo de Negócios ou Jurídico é criado dentro de Notas Fiscais.

## Dados demo

`isDemo=true`:

- não aparece na consulta padrão;
- não é tratado como documento real;
- não conta em liquidação;
- não alimenta o adapter contábil quando a consulta real é usada;
- não transforma legado ambíguo em documento fiscal real.

## UI final

Estrutura:

```text
Financeiro / Notas Fiscais

Criar Nota

Entrada | Saída

Busca + filtros

TableView

Paginação
```

O drawer organiza:

```text
Dados gerais
Partes
Itens
Tributos
Retenções
Relacionamentos
Transações vinculadas
Documentos e anexos
Observações
Histórico
```

A interface não oferece emissão SEFAZ/NFS-e, autorização oficial, criação de pagamento ou editor de transação bancária.

## Materialização

A ordem canônica da etapa é:

```text
arquitetura definitiva
CRM completo
Transações
Contabilidade
Notas Fiscais
```

`scripts/crm_fiscal_documents.py` roda por último nesta etapa e substitui apenas a implementação/rota fiscal, validando que Transações, Contabilidade e o sidebar oficial continuam presentes.
