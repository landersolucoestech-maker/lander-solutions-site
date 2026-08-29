# Valtren Solutions — Site institucional e Sistema Interno

Projeto da **Valtren Solutions** organizado como monorepo com aplicação frontend em `web/` e boundary de backend futuro em `api/`.

## Regras de desenvolvimento

- Desenvolvimento exclusivamente na branch `dev`;
- `main` preservada e sem escrita até liberação explícita;
- autenticação desativada nesta etapa;
- nenhum usuário, sessão, papel, permissão, notificação, integração ou dado operacional deve ser simulado como se viesse de backend;
- sem Supabase ou outro backend externo nesta etapa;
- credenciais nunca são armazenadas no frontend;
- dados operacionais iniciam vazios quando não houver fonte real; mock/demo não é registro real.

## Estrutura

```text
/
├─ web/                  # aplicação frontend canônica
│  ├─ src/
│  │  ├─ app/
│  │  ├─ modules/
│  │  └─ shared/
│  ├─ public/assets/
│  └─ tests/
├─ api/                  # backend futuro; sem runtime fictício
│  ├─ src/{modules,shared,config}/
│  ├─ contracts/
│  └─ tests/
├─ scripts/              # tooling/materialização/certificação
├─ docs/
├─ mockups/
├─ .bootstrap/           # payload legado de reconstrução
└─ .github/
```

`web/src` é o único source frontend versionado. `src/` na raiz é proibido. Assets públicos canônicos ficam em `web/public/assets`; `assets/` na raiz só existe como saída runtime da materialização.

## Materialização

Enquanto o bundle legado ainda existir, a aplicação final é reconstruída a partir de `.bootstrap`, dos owners em `web/src` e dos orquestradores em `scripts/`:

```bash
python scripts/materialize.py
python -m http.server 4173
```

Os materializadores leem diretamente de `web/src`. Não existe mais ponte ou cópia temporária `src/` na raiz. Durante a materialização, `web/public/assets` é preparado em `assets/` porque o bundle legado ainda espera os assets públicos nesse caminho de saída.

## Ownership funcional

- Dashboard: módulo global em `web/src/modules/dashboard`;
- Agenda: módulo global em `web/src/modules/agenda`;
- CRM: `web/src/modules/crm`, com Pessoas/Organizações e workspace comercial;
- Financeiro: `web/src/modules/finance` — Transações, Contabilidade, Fiscal, Rateios, Participações e Repasses;
- Jurídico: `web/src/modules/legal` — Contratos, Assuntos, Compliance, Propriedade Intelectual e Societário;
- Negócios: `web/src/modules/business` — Produtos, Serviços e Unidades de Negócio;
- Marketing: `web/src/modules/marketing`;
- Communications, Integrations, Settings e Notifications possuem boundaries explícitas em `web/src/modules` sem backend simulado.

Os scripts Python continuam como orquestradores temporários de materialização; eles não são o owner final do código de produto.

## API futura

`api/` existe para evitar uma futura reorganização destrutiva quando o backend for implementado. Nesta fase não existem endpoints, persistência, autenticação, filas, jobs ou provedores reais. `api/contracts/` é a área preparada para contratos estáveis entre frontend e backend.

## Certificação

Pipeline verde isolado não certifica interface. A saída da `dev` precisa passar por testes de source e materialized, idempotência, ownership, hashes do artifact, certificação visual e verificação da URL pública.

O artifact do GitHub Pages contém somente a saída materializada do site. `web/`, `api/`, `scripts/`, `docs/` e demais fontes/tooling não são publicados.

## Integrações e autenticação

Integrações sem credenciais e backend seguro aparecem apenas como **Não configurado**. Autenticação permanece **desativada** até existir provedor real de identidade e persistência segura.

## Identidade visual

Os assets oficiais versionados são:

- `web/public/assets/valtren-logo.svg`
- `web/public/assets/valtren-logo-light.svg`
- `web/public/assets/valtren-mark.svg`
