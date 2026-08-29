# Business

Domínio de catálogo e estrutura operacional formado por **Unidades de Negócio** e **Serviços**.

## Regra canônica

Não existe mais um módulo independente de **Produtos**. O que anteriormente era tratado como produto do negócio passa a ser representado pela própria **Unidade de Negócio**.

Enquanto o bundle legado ainda utiliza campos como `product` e `productId`, esses identificadores existem somente como camada temporária de compatibilidade e devem resolver para `business_unit` / `businessUnitId`. Eles não podem criar página, item de navegação, cadastro ou fonte de dados paralela de Produto.

Rotas canônicas:

- `#/crm/negocios` — Unidades de Negócio;
- `#/crm/negocios/servicos` — Serviços;
- `#/crm/negocios/unidades` — compatibilidade para Unidades de Negócio.
