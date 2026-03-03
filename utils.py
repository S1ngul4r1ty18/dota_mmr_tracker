from config import TEMPLATES_DIR

def create_templates():
    
    with open(TEMPLATES_DIR / "base.html", "w", encoding="utf-8") as f:
        f.write("""
<!DOCTYPE html>
<html lang="pt-PT" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tracker de MMR - Dota 2</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚔️</text></svg>">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: { extend: { colors: { dota: '#C23C2A', darkbg: '#121212', panel: '#1E1E1E' } } }
        }
    </script>
    <style> body { background-color: #121212; color: #E0E0E0; } </style>
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="bg-panel border-b border-gray-800 p-4 overflow-x-auto">
        <div class="max-w-7xl mx-auto flex justify-between items-center whitespace-nowrap gap-4">
            <a href="/dashboard" class="text-xl font-bold flex items-center gap-2 flex-shrink-0">
                <span class="text-dota">⚔️ Dota 2</span> MMR Tracker
            </a>
            <div class="flex gap-2 sm:gap-4 items-center flex-shrink-0">
                {% if request.cookies.get("account_id") %}
                    <a href="/dashboard" class="text-gray-300 hover:text-white px-2 py-2 rounded text-sm transition">Painel</a>
                    <a href="/profile" class="text-gray-300 hover:text-white px-2 py-2 rounded text-sm transition">Perfil</a>
                    <a href="/matches" class="text-gray-300 hover:text-white px-2 py-2 rounded text-sm transition">Partidas</a>
                    <a href="/heroes" class="text-gray-300 hover:text-white px-2 py-2 rounded text-sm transition">Heróis</a>
                    <a href="/records" class="text-gray-300 hover:text-white px-2 py-2 rounded text-sm transition">Recordes</a>
                    
                    {% if profile %}
                    <div class="flex items-center gap-2 sm:ml-4 sm:border-l border-gray-700 sm:pl-4">
                        <img src="{{ profile.avatarfull }}" class="w-8 h-8 rounded-full border border-gray-600">
                        <span class="text-sm font-bold text-white hidden sm:block">{{ profile.personaname }}</span>
                    </div>
                    {% endif %}
                    
                    <a href="/logout" class="bg-red-900 hover:bg-red-800 text-white px-3 py-1.5 rounded text-sm transition sm:ml-2">Sair</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <main class="flex-grow max-w-7xl w-full mx-auto p-4 sm:p-6">
        {% block content %}{% endblock %}
    </main>
    <footer class="bg-panel text-center p-4 text-sm text-gray-500 border-t border-gray-800 mt-auto">
        Criado via API OpenDota. Este projeto não é afiliado à Valve.
    </footer>
</body>
</html>
        """)

    with open(TEMPLATES_DIR / "login.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto mt-20 bg-panel p-8 rounded-xl border border-gray-800 shadow-2xl text-center">
    <h2 class="text-2xl font-bold mb-6 text-white">Iniciar Sessão</h2>
    <p class="text-gray-400 text-sm mb-6">Inicie sessão com segurança usando a autenticação oficial da Steam para acompanhar o seu MMR.</p>
    {% if error %}
    <div class="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-6 text-sm">Falha na autenticação da Steam.</div>
    {% endif %}
    <a href="/login/steam" class="inline-flex items-center gap-3 bg-[#171a21] hover:bg-[#2a475e] border border-gray-700 text-white font-bold py-3 px-6 rounded transition">
        <img src="https://raw.githubusercontent.com/CodeVirtualZ/SteamGameBooster/refs/heads/master/steam-icon.ico" class="h-6" alt="Steam Logo">
        Entrar com a Steam
    </a>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "setup.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto mt-20 bg-panel p-8 rounded-xl border border-gray-800 shadow-2xl text-center">
    <div class="text-4xl mb-4">📈</div>
    <h2 class="text-2xl font-bold mb-4 text-white">Configuração Inicial</h2>
    
    <form action="/setup-mmr" method="post" class="flex flex-col gap-4 text-left">
        <div id="mmrInputBox">
            <label class="block text-sm font-medium text-gray-400 mb-1">O seu MMR Atual</label>
            <input type="number" name="mmr" id="mmrInput" placeholder="Ex: 3500" 
                   class="w-full bg-darkbg border border-gray-700 rounded p-3 text-white text-center text-xl focus:outline-none focus:border-dota">
        </div>
        
        <label class="flex items-center gap-2 mt-2 cursor-pointer bg-darkbg p-3 border border-gray-700 rounded">
            <input type="checkbox" name="is_calibrating" id="calibratingCheckbox" onchange="toggleMMR()" class="w-5 h-5 accent-dota">
            <span class="text-gray-300 font-medium">Ainda estou a calibrar o meu MMR</span>
        </label>
        
        <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded transition mt-2">
            Guardar e Continuar
        </button>
    </form>
</div>
<script>
    function toggleMMR() {
        const isChecked = document.getElementById('calibratingCheckbox').checked;
        const mmrInputBox = document.getElementById('mmrInputBox');
        const mmrInput = document.getElementById('mmrInput');
        if (isChecked) {
            mmrInputBox.classList.add('opacity-50', 'pointer-events-none');
            mmrInput.required = false;
        } else {
            mmrInputBox.classList.remove('opacity-50', 'pointer-events-none');
            mmrInput.required = true;
        }
    }
    toggleMMR();
</script>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "profile.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- Left: Profile Info -->
    <div class="bg-panel rounded-xl border border-gray-800 p-6 flex flex-col items-center text-center">
        <img src="{{ profile.avatarfull }}" class="w-32 h-32 rounded-full border-4 border-[#2a475e] shadow-lg mb-4">
        <h2 class="text-2xl font-bold text-white">{{ profile.personaname }}</h2>
        <p class="text-xs font-mono text-gray-500 mt-1">ID: {{ account_id }}</p>
        
        <div class="mt-6 w-full space-y-3 text-left">
            <div class="bg-darkbg p-4 rounded border border-gray-700 flex justify-between items-center h-24">
                <span class="text-xs text-gray-400 uppercase tracking-widest font-bold">Medalha Oficial</span>
                <div class="flex items-center gap-3">
                    <span class="text-lg font-bold text-yellow-500">{{ profile.rank_name }}</span>
                    <img src="{{ profile.rank_url }}" class="h-20 drop-shadow-lg object-contain" alt="Rank Medal">
                </div>
            </div>
            <div class="bg-darkbg p-4 rounded border border-blue-900 flex justify-between items-center relative overflow-hidden h-16">
                <div class="absolute inset-0 bg-blue-900/10"></div>
                <span class="text-xs text-blue-300 uppercase tracking-widest font-bold z-10">Estimativa MMR Ranked</span>
                <span class="text-xl font-bold text-blue-400 z-10">{{ profile.computed_mmr or 'Indisponível' }}</span>
            </div>
            <div class="bg-darkbg p-4 rounded border border-orange-900 flex justify-between items-center relative overflow-hidden h-16">
                <div class="absolute inset-0 bg-orange-900/10"></div>
                <span class="text-xs text-orange-300 uppercase tracking-widest font-bold z-10">Estimativa MMR Turbo</span>
                <span class="text-xl font-bold text-orange-400 z-10">{{ profile.computed_mmr_turbo or 'Indisponível' }}</span>
            </div>
        </div>
    </div>

    <!-- Right: Peers -->
    <div class="md:col-span-2 flex flex-col gap-6">
        <div class="bg-panel rounded-xl border border-gray-800 p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">🤝 Aliados Frequentes</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-gray-400 border-b border-gray-700">
                            <th class="pb-2 font-medium">Jogador</th>
                            <th class="pb-2 font-medium text-center">Partidas Juntas</th>
                            <th class="pb-2 font-medium text-center">Vitórias</th>
                            <th class="pb-2 font-medium text-center">Winrate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in allies %}
                        <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                            <td class="py-2 flex items-center gap-3">
                                <img src="{{ p.avatar or '/static/default.jpg' }}" class="w-8 h-8 rounded border border-gray-700">
                                <span class="text-gray-200 font-bold">{{ p.personaname or 'Desconhecido' }}</span>
                            </td>
                            <td class="py-2 text-center text-gray-300 font-mono">{{ p.with_games }}</td>
                            <td class="py-2 text-center text-green-500 font-mono font-bold">{{ p.with_win }}</td>
                            <td class="py-2 text-center text-gray-400 font-mono">{{ "%.1f"|format((p.with_win/p.with_games)*100) if p.with_games > 0 else 0 }}%</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="py-8 text-center text-gray-500">Ainda não há dados suficientes de aliados. Jogue mais partidas!</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="bg-panel rounded-xl border border-gray-800 p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">⚔️ Inimigos Frequentes</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-gray-400 border-b border-gray-700">
                            <th class="pb-2 font-medium">Jogador</th>
                            <th class="pb-2 font-medium text-center">Enfrentados</th>
                            <th class="pb-2 font-medium text-center">Vitórias (Suas)</th>
                            <th class="pb-2 font-medium text-center">Winrate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in enemies %}
                        <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                            <td class="py-2 flex items-center gap-3">
                                <img src="{{ p.avatar or '/static/default.jpg' }}" class="w-8 h-8 rounded border border-gray-700">
                                <span class="text-gray-200 font-bold">{{ p.personaname or 'Desconhecido' }}</span>
                            </td>
                            <td class="py-2 text-center text-gray-300 font-mono">{{ p.against_games }}</td>
                            <td class="py-2 text-center text-green-500 font-mono font-bold">{{ p.against_win }}</td>
                            <td class="py-2 text-center text-gray-400 font-mono">{{ "%.1f"|format((p.against_win/p.against_games)*100) if p.against_games > 0 else 0 }}%</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="py-8 text-center text-gray-500">Ainda não há dados suficientes de adversários.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "dashboard.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2 flex flex-col gap-6">
        <div class="bg-panel rounded-xl border border-gray-800 p-6 relative overflow-hidden">
            <div class="flex justify-between items-end mb-4 relative z-20">
                <div>
                    <h2 class="text-lg font-bold text-gray-300">Evolução de MMR</h2>
                    <p class="text-sm text-gray-500">A sua curva de progressão desde o registo</p>
                </div>
                <div class="text-left lg:text-right hidden sm:block">
                    <p class="text-sm text-gray-500">MMR Atual</p>
                    <p class="text-3xl font-black {% if is_calibrating %}text-yellow-500{% else %}text-white{% endif %}">
                        {{ current_mmr }}
                    </p>
                </div>
            </div>
            
            {% if is_calibrating %}
            <div class="h-72 w-full flex flex-col items-center justify-center border-2 border-dashed border-gray-700 rounded-lg bg-darkbg/50">
                <span class="text-5xl mb-4">⏳</span>
                <p class="text-gray-400 mb-4 text-center px-4">Jogue as suas partidas de calibração tranquilamente. O gráfico começará a ser gerado após inserir o valor final.</p>
                
                <form action="/calibrate-mmr" method="post" class="flex gap-2">
                    <input type="number" name="mmr" required placeholder="Novo MMR" class="w-32 bg-panel border border-gray-600 rounded p-2 text-white focus:outline-none focus:border-dota">
                    <button type="submit" class="bg-yellow-600 hover:bg-yellow-500 text-white font-bold px-4 py-2 rounded transition">
                        Calibrado!
                    </button>
                </form>
            </div>
            {% else %}
            <div class="relative h-72 w-full">
                <canvas id="mmrChart"></canvas>
            </div>
            {% endif %}
        </div>
    </div>

    <div class="bg-panel rounded-xl border border-gray-800 p-6 overflow-hidden flex flex-col h-[32rem]">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-bold text-gray-300">Últimas Partidas</h2>
            <a href="/matches" class="text-xs text-blue-400 hover:underline">Ver Todas</a>
        </div>
        
        <div class="overflow-y-auto flex-grow pr-2 space-y-3 custom-scrollbar">
            {% if recent_matches %}
                {% for match in recent_matches %}
                <div class="bg-darkbg border border-gray-800 rounded p-3 flex items-center justify-between group">
                    <div class="flex items-center gap-3">
                        <img src="{{ match.hero_img }}" alt="Hero" class="w-12 h-8 object-cover rounded shadow">
                        <div>
                            <p class="text-xs text-gray-500">{{ match.played_at }}</p>
                            <a href="/matches/{{ match.match_id }}" class="text-sm font-medium hover:text-blue-400 transition">ID: {{ match.match_id }}</a>
                        </div>
                    </div>
                    <div class="flex items-center gap-4">
                        {% if not is_calibrating %}
                            {% if match.lobby_type == 7 %}
                                <div class="flex flex-col items-end">
                                    <span class="font-bold text-lg {% if match.mmr_change > 0 %}text-green-500{% else %}text-red-500{% endif %}" title="MMR Total">
                                        {{ match.total_mmr }}
                                    </span>
                                    <span class="text-xs text-gray-500" title="Variação">
                                        {% if match.mmr_change > 0 %}+{% endif %}{{ match.mmr_change }}
                                    </span>
                                </div>
                                <button onclick="toggleEdit('{{ match.match_id }}')" class="text-gray-500 hover:text-white transition opacity-0 group-hover:opacity-100" title="Ajustar MMR Total">
                                    ✏️
                                </button>
                            {% else %}
                                <div class="flex flex-col items-end">
                                    {% if match.game_mode == 23 %}
                                        <span class="text-orange-500 text-[10px] font-bold uppercase tracking-widest bg-orange-900/30 border border-orange-800 px-2 py-0.5 rounded mb-1">Turbo</span>
                                    {% else %}
                                        <span class="text-gray-400 text-[10px] font-bold uppercase tracking-widest bg-gray-800 border border-gray-700 px-2 py-0.5 rounded mb-1">Casual</span>
                                    {% endif %}
                                    <span class="font-bold text-sm {% if match.is_win %}text-green-500{% else %}text-red-500{% endif %}">
                                        {% if match.is_win %}Vitória{% else %}Derrota{% endif %}
                                    </span>
                                </div>
                            {% endif %}
                        {% else %}
                            <div class="flex flex-col items-end">
                                {% if match.lobby_type == 7 %}
                                    <span class="text-blue-400 text-[10px] font-bold uppercase tracking-widest bg-blue-900/30 border border-blue-800 px-2 py-0.5 rounded mb-1">Ranked</span>
                                {% elif match.game_mode == 23 %}
                                    <span class="text-orange-500 text-[10px] font-bold uppercase tracking-widest bg-orange-900/30 border border-orange-800 px-2 py-0.5 rounded mb-1">Turbo</span>
                                {% else %}
                                    <span class="text-gray-400 text-[10px] font-bold uppercase tracking-widest bg-gray-800 border border-gray-700 px-2 py-0.5 rounded mb-1">Casual</span>
                                {% endif %}
                                <span class="font-bold {% if match.is_win %}text-green-500{% else %}text-red-500{% endif %}">{% if match.is_win %}W{% else %}L{% endif %}</span>
                            </div>
                        {% endif %}
                    </div>
                </div>
                
                {% if not is_calibrating and match.lobby_type == 7 %}
                <form id="edit-form-{{ match.match_id }}" action="/update-match" method="post" class="hidden bg-gray-800 p-2 rounded mt-1 flex gap-2 items-center justify-end">
                    <input type="hidden" name="match_id" value="{{ match.match_id }}">
                    <input type="hidden" name="prev_mmr" value="{{ match.prev_mmr }}">
                    <label class="text-xs text-gray-400">Total MMR:</label>
                    <input type="number" name="total_mmr" value="{{ match.total_mmr }}" class="w-20 bg-darkbg text-white border border-gray-600 rounded p-1 text-sm">
                    <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-xs text-white px-2 py-1 rounded">Guardar</button>
                    <button type="button" onclick="toggleEdit('{{ match.match_id }}')" class="bg-gray-600 hover:bg-gray-500 text-xs text-white px-2 py-1 rounded">Cancelar</button>
                </form>
                {% endif %}
                {% endfor %}
            {% else %}
                <div class="text-center text-gray-500 py-10">
                    <p>Nenhuma partida encontrada após o seu registo.</p>
                </div>
            {% endif %}
        </div>
    </div>
</div>

{% if not is_calibrating %}
<script>
    function toggleEdit(matchId) { document.getElementById(`edit-form-${matchId}`).classList.toggle('hidden'); }
    document.addEventListener('DOMContentLoaded', function() {
        const ctx = document.getElementById('mmrChart').getContext('2d');
        const labels = {{ chart_labels | safe }};
        const data = {{ chart_data | safe }};
        const isPositive = data[data.length-1] >= data[0];
        const lineColor = isPositive ? '#10B981' : '#EF4444'; 
        const bgColor = isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

        new Chart(ctx, {
            type: 'line', data: { labels: labels, datasets: [{
                label: 'MMR Total', data: data, borderColor: lineColor, backgroundColor: bgColor,
                borderWidth: 3, pointBackgroundColor: '#1E1E1E', pointBorderColor: lineColor,
                pointRadius: 4, pointHoverRadius: 6, fill: true, tension: 0.3 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                scales: { x: { grid: { color: '#2D3748', drawBorder: false }, ticks: { color: '#718096', maxTicksLimit: 10 } },
                          y: { grid: { color: '#2D3748', drawBorder: false }, ticks: { color: '#718096' } } } }
        });
    });
</script>
{% endif %}
<style>
    .custom-scrollbar::-webkit-scrollbar { width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #374151; border-radius: 10px; }
</style>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "matches.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-6 rounded-xl border border-gray-800">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-gray-700 pb-4">
        <h2 class="text-2xl font-bold text-white">Todas as Partidas</h2>
        
        <div class="flex flex-wrap gap-2">
            <a href="/matches?mode=all" class="px-4 py-2 text-sm rounded transition {% if mode == 'all' %}bg-gray-700 text-white font-bold{% else %}bg-darkbg text-gray-400 hover:bg-gray-800{% endif %}">Todas</a>
            <a href="/matches?mode=ranked" class="px-4 py-2 text-sm rounded transition {% if mode == 'ranked' %}bg-blue-900 text-white font-bold{% else %}bg-darkbg text-gray-400 hover:bg-gray-800{% endif %}">Ranked</a>
            <a href="/matches?mode=turbo" class="px-4 py-2 text-sm rounded transition {% if mode == 'turbo' %}bg-orange-900 text-white font-bold{% else %}bg-darkbg text-gray-400 hover:bg-gray-800{% endif %}">Turbo</a>
            <a href="/matches?mode=other" class="px-4 py-2 text-sm rounded transition {% if mode == 'other' %}bg-gray-700 text-white font-bold{% else %}bg-darkbg text-gray-400 hover:bg-gray-800{% endif %}">Outros</a>
        </div>
    </div>
    
    <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="border-b border-gray-700 text-sm text-gray-400">
                    <th class="py-3 px-4 font-medium">Data/Hora</th>
                    <th class="py-3 px-4 font-medium">Match ID</th>
                    <th class="py-3 px-4 font-medium">Herói</th>
                    <th class="py-3 px-4 font-medium">Resultado</th>
                    <th class="py-3 px-4 font-medium">Modo</th>
                    <th class="py-3 px-4 font-medium">MMR (+/-)</th>
                </tr>
            </thead>
            <tbody class="text-sm">
                {% for match in matches %}
                <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                    <td class="py-3 px-4 text-gray-400">{{ match.played_at }}</td>
                    <td class="py-3 px-4 font-mono">
                        <a href="/matches/{{ match.match_id }}" class="text-blue-400 hover:underline">{{ match.match_id }}</a>
                    </td>
                    <td class="py-3 px-4">
                        <img src="{{ match.hero_img }}" alt="Hero" class="h-8 rounded">
                    </td>
                    <td class="py-3 px-4">
                        {% if match.is_win %}
                        <span class="text-green-500 font-bold">Vitória</span>
                        {% else %}
                        <span class="text-red-500 font-bold">Derrota</span>
                        {% endif %}
                    </td>
                    <td class="py-3 px-4">
                        {% if match.lobby_type == 7 %}
                            <span class="inline-flex items-center bg-blue-900/30 text-blue-400 border border-blue-800 text-[10px] uppercase tracking-widest px-2 py-0.5 rounded font-bold">Ranked</span>
                        {% elif match.game_mode == 23 %}
                            <span class="inline-flex items-center bg-orange-900/30 text-orange-500 border border-orange-800 text-[10px] uppercase tracking-widest px-2 py-0.5 rounded font-bold">Turbo</span>
                        {% else %}
                            <span class="inline-flex items-center bg-gray-800 text-gray-400 border border-gray-700 text-[10px] uppercase tracking-widest px-2 py-0.5 rounded font-bold">Casual</span>
                        {% endif %}
                    </td>
                    <td class="py-3 px-4 font-bold">
                        {% if match.lobby_type == 7 %}
                            <span class="{% if match.mmr_change > 0 %}text-green-500{% elif match.mmr_change < 0 %}text-red-500{% else %}text-gray-500{% endif %}">
                                {% if match.mmr_change > 0 %}+{{ match.mmr_change }}{% elif match.mmr_change < 0 %}{{ match.mmr_change }}{% else %}-{% endif %}
                            </span>
                        {% else %}
                            <span class="text-gray-600">-</span>
                        {% endif %}
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="6" class="py-6 text-center text-gray-500">Nenhuma partida encontrada neste filtro.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    {% if total_pages > 1 %}
    <div class="mt-6 flex justify-center gap-2 text-sm">
        {% if page > 1 %}
        <a href="/matches?mode={{ mode }}&page={{ page - 1 }}" class="bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded">&laquo; Anterior</a>
        {% endif %}
        <span class="bg-darkbg text-gray-400 px-4 py-1.5 rounded border border-gray-700">Página {{ page }} de {{ total_pages }}</span>
        {% if page < total_pages %}
        <a href="/matches?mode={{ mode }}&page={{ page + 1 }}" class="bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded">Próxima &raquo;</a>
        {% endif %}
    </div>
    {% endif %}
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "match_detail.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-6 rounded-xl border border-gray-800 overflow-x-auto">
    <div class="flex justify-between items-center mb-6 pb-4 border-b border-gray-700 min-w-[1000px]">
        <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                {% if radiant_win %}
                <span class="text-green-500">Vitória Radiant</span>
                {% else %}
                <span class="text-red-500">Vitória Dire</span>
                {% endif %}
            </h2>
            <p class="text-gray-400 text-sm mt-1">Partida ID: <span class="font-mono text-white">{{ match_id }}</span></p>
        </div>
        <div class="text-right">
            <p class="text-gray-400 text-sm">Duração</p>
            <p class="text-xl font-mono text-white">{{ duration }}</p>
        </div>
    </div>
    
    <div class="overflow-x-auto pb-4">
        <table class="w-full text-left border-collapse min-w-[1000px] whitespace-nowrap">
            <thead>
                <tr class="border-b border-gray-700 text-sm text-gray-400 bg-darkbg">
                    <th class="py-2 px-3">Jogador / Herói</th>
                    <th class="py-2 px-3 text-center">K / D / A</th>
                    <th class="py-2 px-3 text-center">LH / DN</th>
                    <th class="py-2 px-3 text-center">Dano (H/T)</th>
                    <th class="py-2 px-3 text-center">Cura</th>
                    <th class="py-2 px-3 text-center">GPM</th>
                    <th class="py-2 px-3 text-center">XPM</th>
                    <th class="py-2 px-3 text-center">Inventário / Buffs</th>
                </tr>
            </thead>
            <tbody class="text-sm">
                {% for p in players %}
                <tr class="border-b border-gray-800 transition {% if p.is_current_user %}bg-blue-900/20 hover:bg-blue-900/40{% else %}hover:bg-gray-800/50{% endif %}">
                    <td class="py-3 px-3 flex flex-col justify-center">
                        <div class="flex items-center gap-3">
                            <img src="{{ p.hero_img }}" alt="{{ p.hero_name }}" class="h-10 rounded shadow-md cursor-help" title="{{ p.hero_name }}">
                            <div>
                                <span class="text-white font-bold block">{% if p.is_current_user %}👤 {% endif %}{{ p.personaname }}</span>
                                {% if p.is_radiant %}
                                <span class="text-green-500 text-[10px] uppercase font-black tracking-widest">Radiant</span>
                                {% else %}
                                <span class="text-red-500 text-[10px] uppercase font-black tracking-widest">Dire</span>
                                {% endif %}
                            </div>
                        </div>
                    </td>
                    <td class="py-3 px-3 text-center font-mono">
                        <span class="text-green-400">{{ p.kills }}</span> / <span class="text-red-400">{{ p.deaths }}</span> / <span class="text-gray-400">{{ p.assists }}</span>
                    </td>
                    <td class="py-3 px-3 text-center font-mono">
                        <span class="text-blue-300">{{ p.lh }}</span> / <span class="text-gray-500">{{ p.dn }}</span>
                    </td>
                    <td class="py-3 px-3 text-center font-mono">
                        <span class="text-red-400" title="Dano a Heróis">{{ p.hero_dmg }}</span> / <span class="text-orange-400" title="Dano a Torres">{{ p.tower_dmg }}</span>
                    </td>
                    <td class="py-3 px-3 text-center font-mono text-green-400">{{ p.hero_heal }}</td>
                    <td class="py-3 px-3 text-center text-yellow-500 font-medium">{{ p.gpm }}</td>
                    <td class="py-3 px-3 text-center text-blue-400 font-medium">{{ p.xpm }}</td>
                    
                    <td class="py-3 px-3">
                        <div class="flex items-center justify-center gap-2">
                            <div class="grid grid-cols-3 gap-1">
                                {% for item in p.inventory %}
                                    {% if item.url %}
                                        <img src="{{ item.url }}" class="w-8 h-6 rounded shadow object-cover border border-gray-700 cursor-help" title="{{ item.name }}">
                                    {% else %}
                                        <div class="w-8 h-6 rounded bg-[#1e1e1e] border border-[#2d2d2d] cursor-help" title="{{ item.name }}"></div>
                                    {% endif %}
                                {% endfor %}
                            </div>
                            
                            <div class="flex items-center ml-2 border-l border-gray-700 pl-3 gap-2">
                                {% if p.neutral_item.url %}
                                    <img src="{{ p.neutral_item.url }}" class="w-7 h-7 rounded-full border-2 border-yellow-600 shadow object-cover cursor-help" title="{{ p.neutral_item.name }}">
                                {% else %}
                                    <div class="w-7 h-7 rounded-full bg-[#1e1e1e] border-2 border-[#2d2d2d] cursor-help" title="{{ p.neutral_item.name }}"></div>
                                {% endif %}
                                
                                <div class="flex flex-col gap-1">
                                    {% if p.scepter %}<img src="/img/item/108" class="w-4 h-4 rounded-full border border-blue-400 cursor-help" title="Aghanim's Scepter">{% endif %}
                                    {% if p.shard %}<img src="/img/item/609" class="w-4 h-4 rounded-full border border-blue-400 cursor-help" title="Aghanim's Shard">{% endif %}
                                    {% if p.moonshard %}<img src="/img/item/247" class="w-4 h-4 rounded-full border border-blue-400 cursor-help" title="Moon Shard">{% endif %}
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="mt-4 text-center">
        <a href="/matches" class="text-blue-400 hover:text-white transition text-sm">&larr; Voltar à Lista de Partidas</a>
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "heroes.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-6 rounded-xl border border-gray-800">
    <h2 class="text-2xl font-bold text-white mb-6">Desempenho por Herói (Vitalício)</h2>
    
    <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="border-b border-gray-700 text-sm text-gray-400">
                    <th class="py-3 px-4 font-medium">Herói</th>
                    <th class="py-3 px-4 font-medium text-center">Total de Partidas</th>
                    <th class="py-3 px-4 font-medium text-center">Vitórias / Derrotas</th>
                    <th class="py-3 px-4 font-medium text-center">Win Rate</th>
                </tr>
            </thead>
            <tbody class="text-sm">
                {% for hero in heroes %}
                <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                    <td class="py-3 px-4 flex items-center gap-3">
                        <img src="{{ hero.hero_img }}" alt="{{ hero.hero_name }}" class="h-8 rounded shadow">
                        <span class="text-white font-medium">{{ hero.hero_name }}</span>
                    </td>
                    <td class="py-3 px-4 text-center text-gray-300">{{ hero.total_games }}</td>
                    <td class="py-3 px-4 text-center">
                        <span class="text-green-500 font-bold">{{ hero.wins }}</span> <span class="text-gray-600 mx-1">/</span> <span class="text-red-500 font-bold">{{ hero.losses }}</span>
                    </td>
                    <td class="py-3 px-4 text-center">
                        <div class="w-full bg-gray-800 rounded-full h-2.5 mb-1 max-w-[120px] mx-auto overflow-hidden">
                            <div class="bg-blue-600 h-2.5 rounded-full" style="width: {{ hero.winrate }}%"></div>
                        </div>
                        <span class="text-xs text-gray-400">{{ hero.winrate }}%</span>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4" class="py-6 text-center text-gray-500">Nenhum dado disponível. Jogue algumas partidas!</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "records.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-6 rounded-xl border border-gray-800">
    <div class="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
        <h2 class="text-2xl font-bold text-white">Recordes Pessoais</h2>
        <div class="flex gap-4">
            <div class="bg-[#1c242d] border border-[#2d3844] rounded px-6 py-3 text-center shadow">
                <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Maior Win Streak</p>
                <p class="text-3xl font-black text-[#a3e635] drop-shadow">{{ win_streak }}</p>
            </div>
            <div class="bg-[#1c242d] border border-[#2d3844] rounded px-6 py-3 text-center shadow">
                <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Maior Lose Streak</p>
                <p class="text-3xl font-black text-red-500 drop-shadow">{{ lose_streak }}</p>
            </div>
        </div>
    </div>
    
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-6">
        {% for r in records %}
        <a href="/matches/{{ r.match_id }}" class="block relative bg-[#1c242d] rounded overflow-hidden border border-[#2d3844] hover:border-gray-400 transition shadow-lg group">
            <div class="absolute inset-0 bg-cover bg-center opacity-30 group-hover:opacity-40 transition duration-500" style="background-image: url('{{ r.hero_img }}'); filter: blur(2px);"></div>
            <div class="absolute inset-0 bg-gradient-to-t from-[#151a20] via-[#1c242d]/60 to-transparent"></div>
            
            <div class="relative z-10 flex flex-col items-center justify-center p-5 min-h-[160px]">
                <p class="text-gray-200 text-sm font-bold tracking-wide drop-shadow-md">{{ r.title }}</p>
                <p class="text-[#a3e635] text-4xl font-black my-2 drop-shadow-lg">{{ r.value }}</p>
                <p class="text-gray-300 text-sm font-medium mb-1 drop-shadow-md">{{ r.subtitle }}</p>
                
                <p class="text-gray-400 text-xs drop-shadow-md">
                    <span class="{% if r.is_win %}text-green-500{% else %}text-red-500{% endif %} font-bold">{% if r.is_win %}Won{% else %}Lost{% endif %}</span> 
                    {{ r.date_str }}, {{ r.lobby_name }}
                </p>
            </div>
        </a>
        {% else %}
        <div class="col-span-full py-10 text-center text-gray-500">
            Nenhum recorde local encontrado. Jogue algumas partidas para preencher esta página.
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "admin.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-8 rounded-xl border border-gray-800">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-white flex items-center gap-2">🛡️ Painel de Superadmin</h2>
        <span class="bg-red-900 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">Acesso Restrito</span>
    </div>
    
    <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="border-b border-gray-700 text-sm text-gray-400">
                    <th class="py-3 px-4 font-medium">Steam ID / Account ID</th>
                    <th class="py-3 px-4 font-medium">Nome (Steam)</th>
                    <th class="py-3 px-4 font-medium">Data de Registo</th>
                    <th class="py-3 px-4 font-medium">Partidas Monitorizadas</th>
                    <th class="py-3 px-4 font-medium text-right">Ações</th>
                </tr>
            </thead>
            <tbody class="text-sm">
                {% for user in users %}
                <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                    <td class="py-3 px-4 font-mono text-gray-300">{{ user.account_id }}</td>
                    <td class="py-3 px-4 text-white font-bold">{{ user.personaname }}</td>
                    <td class="py-3 px-4 text-gray-400">{{ user.registered_at }}</td>
                    <td class="py-3 px-4 text-blue-400 font-bold">{{ user.total_matches }}</td>
                    <td class="py-3 px-4 text-right flex justify-end gap-2">
                        <a href="/painel-admin-secreto-99/user/{{ user.account_id }}" class="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-xs transition">👁️ Auditar Dados</a>
                        <a href="/painel-admin-secreto-99/user/{{ user.account_id }}/export" class="bg-green-700 hover:bg-green-600 text-white px-3 py-1 rounded text-xs transition">📥 Exportar CSV</a>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" class="py-6 text-center text-gray-500">Nenhum utilizador registado ainda.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "admin_user.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="bg-panel p-6 rounded-xl border border-gray-800">
    <div class="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
        <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">Auditoria de SQLite</h2>
            <p class="text-gray-400 text-sm mt-1">Conta Analisada: <span class="font-mono text-blue-400">{{ account_id }}</span></p>
        </div>
        <div class="flex gap-3">
            <a href="/painel-admin-secreto-99/user/{{ account_id }}/export" class="bg-green-700 hover:bg-green-600 text-white px-4 py-2 rounded text-sm transition font-bold flex items-center gap-2">
                📥 Transferir Tudo (.csv)
            </a>
            <a href="/painel-admin-secreto-99" class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm transition">
                &larr; Voltar
            </a>
        </div>
    </div>
    
    <div class="overflow-x-auto h-[600px] border border-gray-700 rounded bg-[#121212]">
        <table class="w-full text-left border-collapse whitespace-nowrap text-xs">
            <thead class="sticky top-0 bg-gray-800 shadow">
                <tr class="text-gray-300">
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">match_id</th>
                    <th class="py-2 px-3 border-r border-gray-700 text-yellow-500 font-black bg-gray-900">lobby_type</th>
                    <th class="py-2 px-3 border-r border-gray-700 text-orange-500 font-black bg-gray-900">game_mode</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">played_at</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">hero_id</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">is_win</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">mmr_change</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">duration</th>
                    <th class="py-2 px-3 border-r border-gray-700 font-mono">kills/deaths/assists</th>
                </tr>
            </thead>
            <tbody>
                {% for m in matches %}
                <tr class="border-b border-gray-800 hover:bg-gray-800/80 transition">
                    <td class="py-2 px-3 border-r border-gray-800 text-blue-400">{{ m.match_id }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 font-bold bg-gray-900/30 text-center">{{ m.lobby_type }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 font-bold bg-gray-900/30 text-center">{{ m.game_mode }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-400">{{ m.played_at_str }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-300">{{ m.hero_id }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-300">{{ m.is_win }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-300">{{ m.mmr_change }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-300">{{ m.duration }}</td>
                    <td class="py-2 px-3 border-r border-gray-800 text-gray-400">{{ m.kills }}/{{ m.deaths }}/{{ m.assists }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="9" class="py-6 text-center text-gray-500">Nenhum registo encontrado na base de dados.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "admin_login.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto mt-20 bg-panel p-8 rounded-xl border border-gray-800 shadow-2xl text-center">
    <h2 class="text-2xl font-bold mb-6 text-white">🔒 Acesso Administrativo</h2>
    {% if error %}
    <div class="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-6 text-sm">Acesso Negado: Palavra-passe incorreta.</div>
    {% endif %}
    <form action="/admin/login" method="post" class="flex flex-col gap-4">
        <input type="password" name="password" placeholder="Palavra-passe de Segurança" required class="w-full bg-darkbg border border-gray-700 rounded p-3 text-white text-center focus:outline-none focus:border-red-500">
        <button type="submit" class="bg-red-800 hover:bg-red-700 text-white font-bold py-3 px-4 rounded transition">
            Autenticar
        </button>
    </form>
    <div class="mt-4"><a href="/" class="text-gray-500 text-xs hover:text-white">&larr; Voltar ao site principal</a></div>
</div>
{% endblock %}
        """)

    with open(TEMPLATES_DIR / "admin_change_password.html", "w", encoding="utf-8") as f:
        f.write("""
{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto mt-20 bg-panel p-8 rounded-xl border border-gray-800 shadow-2xl text-center">
    <h2 class="text-2xl font-bold mb-4 text-white">⚠️ Alteração Obrigatória</h2>
    <p class="text-sm text-gray-400 mb-6">Por motivos de segurança, é estritamente necessário alterar a palavra-passe predefinida antes de visualizar o painel.</p>
    
    <form action="/admin/change-password" method="post" class="flex flex-col gap-4">
        <input type="password" name="new_password" placeholder="Nova Palavra-passe" required minlength="6" class="w-full bg-darkbg border border-gray-700 rounded p-3 text-white text-center focus:outline-none focus:border-green-500">
        <button type="submit" class="bg-green-700 hover:bg-green-600 text-white font-bold py-3 px-4 rounded transition">
            Guardar Definitivamente
        </button>
    </form>
</div>
{% endblock %}
        """)