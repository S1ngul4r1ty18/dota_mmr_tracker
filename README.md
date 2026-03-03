⚔️ Dota 2 MMR Tracker - V7 Full Experience

O Dota 2 MMR Tracker é uma plataforma robusta de análise e acompanhamento de desempenho para jogadores de Dota 2. Ao contrário de outras ferramentas, este sistema foi desenhado para capturar todas as partidas, incluindo o modo Turbo, oferecendo estimativas de MMR realistas e um histórico detalhado através da API OpenDota.

🚀 Funcionalidades Principais

Sincronização Turbo Total: Utiliza parâmetros avançados da API (significant=0) para garantir que nenhuma partida Turbo ou Casual fique de fora do seu histórico.

Perfil em Tempo Real: Integração direta com a API para exibir a sua Medalha de Rank atual, nome e avatar da Steam.

Estimativas de MMR: Exibição do MMR calculado (computed_mmr) tanto para partidas Rankeds como para partidas Turbo.

Sistema de Cache Local Inteligente:

Heróis e Itens: As imagens são descarregadas uma única vez e servidas localmente.

Medalhas Liquipedia: Sistema de proxy que extrai as medalhas oficiais da Liquipedia via hash MD5 e as armazena no servidor.

Recordes Estilo Dotabuff: Uma página dedicada aos seus maiores feitos (Kills, Dano, Cura, Last Hits), filtrando automaticamente partidas contra bots ou modos não oficiais.

Rede Social de Partidas: Visualização de aliados e inimigos mais frequentes com taxas de vitória (Winrate) específicas para cada um.

Painel Administrativo Seguro:

Acesso restrito via /painel-admin-secreto-99.

Autenticação obrigatória.

Segurança: Palavra-passe inicial superadmin123 com alteração obrigatória no primeiro login.

Auditoria: Capacidade de ver a base de dados SQLite bruta de qualquer utilizador registado e exportar para CSV.

🛠️ Tecnologias Utilizadas

Backend: Litestar (Framework ASGI de alta performance).

Base de Dados: SQLite (Uma base de dados principal para utilizadores e uma base de dados individual por jogador para máxima performance).

Frontend: Jinja2 Templates, Tailwind CSS e Chart.js para os gráficos de evolução.

API de Dados: OpenDota API.

Imagens: Steam CDN e Liquipedia MediaWiki.

📦 Estrutura de Ficheiros

app.py: Ponto de entrada da aplicação e configuração das rotas.

routes.py: Toda a lógica de controlo, autenticação e gestão de imagens.

services.py: O "coração" do sistema. Lida com a base de dados, chamadas à API e cálculos de MMR.

config.py: Definições de caminhos e URLs globais.

utils.py: Gerador automático de templates HTML e componentes UI.

databases/: Pasta que contém os ficheiros .sqlite de cada utilizador.

img_cache/: Armazenamento local de imagens para reduzir latência e consumo de API.

⚙️ Instalação e Execução

Requisitos: Python 3.11+ e ambiente virtual (venv).

Instalação de Dependências:

pip install litestar jinja2 httpx uvicorn


Iniciar o Servidor:

uvicorn app.app --host 0.0.0.0 --port 9000 --reload


Primeiro Acesso:

Aceda a http://localhost:9000.

Inicie sessão com a Steam.

Configure o seu MMR atual ou selecione "Calibrando".

🔒 Segurança Administrativa

Para aceder às funções de gestão:

Vá a /admin/login.

Introduza a senha: superadmin123.

O sistema redirecionará para /admin/change-password. Escolha uma senha forte.

A partir daí, poderá auditar todos os utilizadores que utilizam a sua instância do Tracker.

Nota: Este projeto é independente e utiliza dados públicos fornecidos pela API OpenDota. Certifique-se de que o seu perfil Steam está configurado como "Público" e com a opção "Expor Dados de Partidas Públicas" ativa nas definições do jogo Dota 2.
