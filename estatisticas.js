// LOCAL DO ARQUIVO: static/js/estatisticas.js
document.addEventListener('DOMContentLoaded', async () => {
    const localCont = document.getElementById('local-stats-container');
    const recentCont = document.getElementById('recent-stats-container');

    const card = (l, v) => `<div class="stat-card"><span class="stat-label">${l}</span><span class="stat-value">${v}</span></div>`;

    // 1. Estatísticas Manuais
    try {
        const res = await fetch('/api/local_stats');
        if(res.status === 401) window.location.href='/';
        const d = await res.json();
        
        localCont.innerHTML = `<div class="stats-grid">
            ${card('Vitórias', d.vitorias)}
            ${card('Derrotas', d.derrotas)}
            ${card('Total', d.total_partidas)}
            ${card('Winrate', d.winrate + '%')}
        </div>`;
    } catch(e) { localCont.textContent = "Erro."; }

    // 2. Estatísticas Recentes (baseado no cache + api)
    try {
        const res = await fetch('/api/recent_matches');
        const matches = await res.json();
        
        if(matches.length === 0) {
            recentCont.textContent = "Sem partidas recentes.";
            return;
        }

        let wins = 0, kills = 0, deaths = 0, assists = 0;
        matches.forEach(m => {
            const win = (m.player_slot < 128 && m.radiant_win) || (m.player_slot >= 128 && !m.radiant_win);
            if(win) wins++;
            kills += m.kills; deaths += m.deaths; assists += m.assists;
        });

        const count = matches.length;
        recentCont.innerHTML = `<div class="stats-grid">
            ${card('Partidas Analisadas', count)}
            ${card('Winrate Recente', Math.round(wins/count*100) + '%')}
            ${card('Média Kills', (kills/count).toFixed(1))}
            ${card('Média Mortes', (deaths/count).toFixed(1))}
            ${card('Média Assists', (assists/count).toFixed(1))}
        </div>`;

    } catch(e) { recentCont.textContent = "Erro ao calcular."; }
});