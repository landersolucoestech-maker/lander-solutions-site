# API

Fronteira reservada para a futura API/backend da Valtren Solutions.

No estado atual do projeto esta camada NÃO implementa servidor, persistência, autenticação, integrações externas ou endpoints fictícios. Sua existência define desde já a fronteira arquitetural entre frontend e backend e evita acoplamento direto da interface a provedores futuros.

Regras:
- não criar mocks apresentados como API real;
- não armazenar credenciais no frontend;
- contratos futuros devem ser versionados e independentes da UI;
- autenticação, banco de dados, filas, webhooks e integrações só entram aqui quando houver implementação real.
