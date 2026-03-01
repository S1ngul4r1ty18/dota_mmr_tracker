// LOCAL DO ARQUIVO: static/js/recordes.js
document.addEventListener('DOMContentLoaded', async () => {
    const cont = document.getElementById('records-container');
    try {
        const res = await fetch('/api/records');
        if(res.status === 401) return window.location.href = '/';
        const json = await res.json();
        
        if(!json.data || json.data.length === 0) {
            cont.innerHTML = "<p>Sem dados suficientes.</p>";
            return;
        }

        let html = '<div class="stats-grid">';
        json.data.forEach(r => {
            let val = r.value;
            if(r.key === 'duration') val = Math.floor(val/60) + 'm';
            
            html += `<div class="stat-card">
                <span class="stat-label">${r.label}</span>
                <span class="stat-value">${val}</span>
                <div style="margin-top:5px; font-size:0.9em; display:flex; align-items:center;">
                    <img src="${r.hero_image}" class="hero-icon-small"> ${r.hero_name}
                </div>
            </div>`;
        });
        html += '</div>';
        cont.innerHTML = html;
    } catch(e) { cont.textContent = "Erro."; }
});