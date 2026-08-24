# Valtren Solutions — Site institucional

Site institucional da **Valtren Solutions**, mantido neste repositório durante a transição da identidade anterior.

## Identidade visual

A interface utiliza a identidade visual oficial da Valtren Solutions:

- Azul-marinho: `#0B1D3A`;
- Dourado metálico: `#D4AF37`;
- Branco: `#FFFFFF`;
- Carvão: `#1E1E1E`;
- Azul acinzentado: `#475569`;
- Tipografia principal: **Raleway SemiBold/Bold**;
- Tipografia secundária: **Montserrat Regular/Medium**.

Os arquivos `assets/valtren-logo.svg`, `assets/valtren-logo-light.svg` e `assets/valtren-mark.svg` foram construídos a partir da identidade visual fornecida para o projeto. O script `scripts/apply_valtren_brand.py` aplica a marca, a paleta, a tipografia e os tratamentos visuais ao projeto materializado.

## Estado do projeto

- Desenvolvimento concentrado exclusivamente na branch `dev`;
- Branch `main` preservada até validação e liberação formal;
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
3. O pacote será reconstruído, a identidade Valtren será aplicada automaticamente e o site abrirá em `http://localhost:4173`.

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

Senha inicial local mantida por compatibilidade:

```text
lander-admin
```

A senha deve ser alterada no primeiro uso. Como ainda não existe backend, autenticação, conteúdo editado e mensagens do formulário permanecem no `localStorage` do navegador utilizado.

## Supabase

A integração com Supabase permanece adiada. Nenhuma chave, URL de projeto ou credencial foi adicionada ao repositório.
