# Lander Solutions — Site institucional

Repositório oficial do site institucional da **Lander Solutions**.

## Estado do projeto

- Desenvolvimento concentrado na branch `dev`;
- Branch `main` preservada até a validação e liberação formal;
- Sem Supabase ou outro backend externo nesta etapa;
- Conteúdo persistido localmente no navegador;
- Site disponível em português, inglês e espanhol;
- Modos claro e escuro;
- Layout responsivo para desktop, tablet e celular;
- Painel local para alteração de textos, serviços, produtos, contatos e SEO sem edição manual do código.

## Serviços apresentados publicamente

1. Engenharia de Software e Sistemas;
2. Websites e Soluções Web;
3. Branding e Design como competência complementar.

Não são comercializados separadamente no site: EAD, automações, inteligência artificial, APIs, dados, infraestrutura, consultoria técnica, marketing digital, audiovisual, dispatching, BPO, back office, assistência administrativa ou suporte operacional.

## Configuração inicial no Windows

1. Clone ou baixe a branch `dev`;
2. Execute `CONFIGURAR-PROJETO.bat`;
3. O pacote será reconstruído e o site abrirá em `http://localhost:4173`.

Também é possível executar manualmente:

```bash
python scripts/materialize.py
python -m http.server 4173
```

## Painel de conteúdo

Acesse:

```text
http://localhost:4173/#/admin
```

Senha inicial local:

```text
lander-admin
```

A senha deve ser alterada no primeiro uso. Como ainda não existe backend, autenticação, conteúdo editado e mensagens do formulário permanecem no `localStorage` do navegador utilizado.

## Supabase

A integração com Supabase foi deliberadamente adiada. Nenhuma chave, URL de projeto ou credencial foi adicionada ao repositório.
