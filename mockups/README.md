# Mock Mode

Este diretório contém exclusivamente a infraestrutura e os dados de demonstração do Sistema Interno.

## Estrutura
- `data/` — única fonte canônica de dados mockados/fixtures por domínio.
- `factories/` — geradores auxiliares de IDs e datas para mocks.
- `manifest.js` — registro dos datasets disponíveis e configuração do preview.
- `adapter.js` — adaptação dos dados mockados aos contratos do runtime.
- `loader.js` — bootstrap e persistência isolada do Mock Mode.

Dados de demonstração não devem ser declarados diretamente dentro de módulos, páginas, componentes ou materializadores. Quando um populated state for necessário para desenvolvimento ou certificação, ele deve nascer em `mockups/data/`.

## Ativação
No GitHub Pages publicado a partir da branch `dev`, o Mock Mode é ativado automaticamente para que o sistema abra com dados preenchidos.

- `?mock=1` força Mock Mode em qualquer ambiente.
- `?mock=0` força o estado normal/vazio, inclusive no preview publicado.

A query deve ficar antes do hash, por exemplo `?mock=1#/dashboard` ou `?mock=0#/dashboard`.

## Isolamento
Fora do preview publicado, o modo normal não carrega fixtures por padrão. No Mock Mode, persistência demonstrativa usa exclusivamente `valtren:mock:*`. As fixtures-fonte são base imutável; CRUD opera sobre clones materializados no runtime.

## Reset
Use **Resetar dados de demonstração** ou `window.__VALTREN_MOCK_MODE__.reset()`. O reset remove somente chaves `valtren:mock:*` e recarrega as fixtures-base.

## Remoção futura
Exclua `/mockups`, remova `scripts/crm_mock_mode.py` e seu único hook em `scripts/materialize.py`. Nenhum owner de domínio deve depender de fixtures para funcionar em produção.

Mocks são dados de visualização/teste de populated state; não são fallback, seed operacional, autenticação, integração externa ou verdade de produção.
