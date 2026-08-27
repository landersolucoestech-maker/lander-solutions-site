# Mock Mode

Este diretório é a única fonte de fixtures de demonstração do Sistema Interno.

## Ativação
Use `?mock=1` antes do hash, por exemplo `?mock=1#/crm/dashboard`. A query fica em `location.search`, portanto permanece ativa durante navegação por hash e após reload.

## Isolamento
O modo normal não carrega nenhuma fixture. No Mock Mode, persistência demonstrativa usa exclusivamente `valtren:mock:*`. As fixtures-fonte são base imutável; CRUD opera sobre clones materializados no runtime.

## Reset
Use **Resetar dados de demonstração** ou `window.__VALTREN_MOCK_MODE__.reset()`. O reset remove somente chaves `valtren:mock:*` e recarrega as fixtures-base.

## Remoção futura
Exclua `/mockups`, remova `scripts/crm_mock_mode.py` e seu único hook em `scripts/materialize.py`. Nenhum owner de domínio contém fixtures de demonstração.

Mocks são dados de visualização/teste de populated state; não são fallback, seed operacional, autenticação, integração externa ou verdade de produção.
