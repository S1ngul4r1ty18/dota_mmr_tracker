// LOCAL DO ARQUIVO: static/js/historico.js
document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('historico-partidas');
    const gameModes = { 22: "Ranked", 23: "Turbo", 1: "All Pick", 3: "Random Draft" };

    try {
        const res = await fetch('/api/recent_matches');
        if(res.status === 401) return window.location.href = '/';
        const matches = await res.json();

        if(matches.length === 0) {
            container.innerHTML = "<p>Nenhuma partida encontrada.</p>";
            return;
        }

        let html = `<table>
            <thead><tr><th>Herói</th><th>Resultado</th><th>KDA</th><th>Modo</th><th>+</th></tr></thead>
            <tbody>`;
            
        matches.forEach(m => {
            const win = (m.player_slot < 128 && m.radiant_win) || (m.player_slot >= 128 && !m.radiant_win);
            html += `<tr class="${win ? 'vitoria' : 'derrota'}">
                <td><img src="${m.hero_image}" class="hero-icon"> ${m.hero_name}</td>
                <td>${win ? 'Vitória' : 'Derrota'}</td>
                <td>${m.kills}/${m.deaths}/${m.assists}</td>
                <td>${gameModes[m.game_mode] || 'Normal'}</td>
                <td><button class="details-btn" data-id="${m.match_id}">+</button></td>
            </tr>`;
        });
        html += `</tbody></table>`;
        container.innerHTML = html;

        // Listener para Detalhes
        container.addEventListener('click', async e => {
            if(!e.target.classList.contains('details-btn')) return;
            const btn = e.target;
            const row = btn.closest('tr');
            
            // Toggle
            if(row.nextSibling && row.nextSibling.classList && row.nextSibling.classList.contains('details-row')) {
                row.nextSibling.remove();
                btn.textContent = '+';
                return;
            }

            btn.textContent = '...';
            const res = await fetch(`/api/match_details/${btn.dataset.id}`);
            const data = await res.json();
            
            if(data.success) {
                const newRow = document.createElement('tr');
                newRow.className = 'details-row';
                const teamHtml = (team, name) => `
                    <div style="width:48%"><strong>${name}</strong>
                    ${team.map(p => `
                        <div class="player-details">
                            <img src="${p.hero_image}" class="hero-icon-small">
                            ${p.personaname} (${p.hero_name})
                            <span class="kda">${p.kills}/${p.deaths}/${p.assists}</span>
                        </div>
                    `).join('')}</div>`;

                newRow.innerHTML = `<td colspan="5">
                    <div class="details-content">
                        ${teamHtml(data.radiant, 'Radiant')}
                        ${teamHtml(data.dire, 'Dire')}
                    </div>
                </td>`;
                row.after(newRow);
                btn.textContent = '-';
            } else {
                btn.textContent = 'Err';
            }
        });

    } catch(e) {
        container.innerHTML = "<p>Erro ao carregar.</p>";
    }
});