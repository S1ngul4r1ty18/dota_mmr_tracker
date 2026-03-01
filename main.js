// LOCAL DO ARQUIVO: static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const mmrEl = document.getElementById('mmr-atual');
    const ctx = document.getElementById('mmrChart').getContext('2d');
    let chart;

    const loadData = async () => {
        try {
            const res = await fetch('/api/mmr_data');
            // Redireciona se não estiver logado
            if(res.status === 401) return window.location.href = '/';
            
            const data = await res.json();
            const hist = data.historico_mmr;
            
            if(hist.length > 0) {
                mmrEl.textContent = `MMR Atual: ${hist[hist.length-1].mmr}`;
                
                const labels = hist.map((_, i) => i === 0 ? 'Início' : i);
                const values = hist.map(h => h.mmr);
                const colors = hist.map(h => h.diferenca >= 0 ? '#28a745' : '#dc3545');

                if(chart) chart.destroy();
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Evolução MMR',
                            data: values,
                            borderColor: '#007bff',
                            pointBackgroundColor: colors,
                            fill: false,
                            tension: 0.1
                        }]
                    }
                });
            } else {
                mmrEl.textContent = "Sem dados ainda.";
            }
        } catch(e) { console.error(e); }
    };

    document.getElementById('update-mmr-form').addEventListener('submit', async e => {
        e.preventDefault();
        const msg = document.getElementById('update-message');
        const val = document.getElementById('mmr_atualizado').value;
        
        const res = await fetch('/api/update_mmr', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ mmr_atualizado: val })
        });
        const json = await res.json();
        
        if(json.success) {
            msg.textContent = "MMR Atualizado!";
            msg.className = "message success";
            document.getElementById('mmr_atualizado').value = '';
            loadData();
        } else {
            msg.textContent = json.message;
            msg.className = "message error";
        }
    });

    loadData();
});