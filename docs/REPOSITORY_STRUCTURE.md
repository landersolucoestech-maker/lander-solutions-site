# Repository Structure

Este repositório usa uma arquitetura determinística de materialização, organizada desde já com fronteiras explícitas de frontend e backend.

## Estrutura canônica de topo

- `.bootstrap/` — payload de bootstrap consumido somente por `scripts/materialize.py`.
- `.github/workflows/` — gates de CI, certificação, materialização e publicação do `dev`.
- `web/` — owner físico do frontend.
  - `web/src/app/` — composição global da aplicação.
  - `web/src/modules/` — módulos funcionais por domínio.
  - `web/src/shared/` — código compartilhado entre módulos do frontend.
- `api/` — boundary reservada para a futura API/backend.
  - `api/contracts/` — contratos públicos entre frontend e futura API.
- `assets/` — assets canônicos da marca que fazem parte do source.
- `docs/` — documentação de arquitetura, domínio e ownership.
- `mockups/` — fixtures/adapters opcionais de mock mode; nunca dados de produção.
- `scripts/` — materializadores, adapters de materialização, certificações e testes.
- `src` — ponte temporária de compatibilidade apontando para `web/src`; não é um segundo owner.
- `README.md` — regras operacionais e mapa de ownership.

## Estado atual de /api

O projeto continua frontend-only neste estágio. `api/` existe para fixar a arquitetura futura, mas não deve conter servidor fictício, persistência falsa, autenticação simulada, endpoints inventados ou integrações marcadas como conectadas sem implementação real.

Credenciais nunca pertencem ao frontend. Banco de dados, autenticação, filas, webhooks, jobs e integrações externas entram em `api/` somente quando houver implementação real.

## Frontend canônico

Todo source funcional novo do frontend deve entrar em `web/src`, nunca diretamente em uma segunda árvore paralela. A entrada `src` na raiz existe apenas para compatibilidade temporária com materializadores e testes ainda migrando.

A meta de migração é remover essa ponte quando todos os consumidores apontarem diretamente para `web/src`.

## Arquivos gerados

Arquivos como `index.html`, `app.js` e CSS materializado são gerados por `python scripts/materialize.py`. Eles não precisam existir no checkout limpo e não devem ser tratados como source canônico.

`_site/` é apenas artefato de publicação e nunca deve ser commitado.

## Regras estruturais

1. Desenvolvimento ocorre somente em `dev` salvo autorização explícita em contrário.
2. `main` permanece intocada.
3. `web/` é a fronteira do frontend; `api/` é a fronteira do backend futuro.
4. Um domínio possui um único owner canônico.
5. Cross-cutting passes não podem tomar ownership silenciosamente de módulos.
6. CI deve materializar a partir de checkout limpo antes de validar saída gerada.
7. GitHub Pages publica apenas o artefato `_site` certificado.
8. Workflows temporários de mutação devem ser removidos depois de concluídos.
9. Caches, logs, screenshots de teste e artefatos locais nunca viram source.
10. Nenhuma funcionalidade de backend pode ser simulada apenas para preencher `api/`.
11. Nenhum novo source funcional pode ser criado fora de `web/src` ou do futuro `api/src` quando o backend for iniciado.

## Adicionando ou alterando um módulo de frontend

1. Criar/alterar o owner em `web/src/modules/<domínio>`.
2. Manter core, browser/UI adapter e estilos dentro do mesmo ownership de domínio quando aplicável.
3. Manter `scripts/` apenas como camada de materialização, gates e compatibilidade enquanto a arquitetura atual exigir.
4. Conectar o materializador em `scripts/materialize.py` respeitando ordem de dependências.
5. Adicionar testes de source e de saída materializada.
6. Validar idempotência de uma segunda materialização.
7. Atualizar o structure gate quando surgir uma nova boundary estrutural.

A organização `/web` + `/api` é definitiva. A materialização legada continua apenas como mecanismo de build/migração enquanto for necessária.
