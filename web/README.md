# Web

Frontend da aplicação Valtren Solutions.

Esta camada é o destino canônico da interface web. Durante a migração estrutural, o runtime materializado existente continua sendo gerado pela pipeline atual para preservar compatibilidade e publicação no GitHub Pages.

Regras:
- nenhum backend deve ser simulado nesta camada;
- chamadas futuras a serviços devem passar por contratos/adapters explícitos;
- módulos funcionais continuam organizados por domínio;
- a migração física completa do runtime para `web/` deve preservar materialização determinística e idempotência.
