// LOCAL DO ARQUIVO: static/js/admin.js
document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('users-table-body');
    const msg = document.getElementById('admin-message');

    const showMsg = (txt, type) => {
        msg.textContent = txt;
        msg.className = `message ${type}`;
        setTimeout(() => msg.textContent='', 3000);
    };

    const loadUsers = async () => {
        try {
            const res = await fetch('/api/admin/users');
            if(!res.ok) throw new Error("Erro de acesso");
            const data = await res.json();
            
            tbody.innerHTML = '';
            data.users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${u.id}</td>
                    <td>${u.nickname}</td>
                    <td>
                        <input type="text" placeholder="Novo Nick" class="nick-in" style="width:100px">
                        <button class="upd-nick" data-id="${u.id}">OK</button>
                    </td>
                    <td>
                        <input type="password" placeholder="Nova Senha" class="pass-in" style="width:100px">
                        <button class="upd-pass" data-id="${u.id}">OK</button>
                    </td>
                    <td><button class="del-user logout" data-id="${u.id}">X</button></td>
                `;
                tbody.appendChild(tr);
            });
        } catch(e) { showMsg(e.message, 'error'); }
    };

    tbody.addEventListener('click', async e => {
        const t = e.target;
        const uid = t.dataset.id;
        if(!uid) return;
        const row = t.closest('tr');

        if(t.classList.contains('del-user')) {
            if(!confirm("Apagar usuário e todo histórico?")) return;
            await fetch('/api/admin/delete_user', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({user_id: uid})
            });
            loadUsers();
            showMsg("Usuário apagado", 'success');
        }

        if(t.classList.contains('upd-nick')) {
            const val = row.querySelector('.nick-in').value;
            if(!val) return;
            const res = await fetch('/api/admin/update_nickname', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({user_id: uid, new_nickname: val})
            });
            if(res.ok) { loadUsers(); showMsg("Nick alterado", 'success'); }
            else showMsg("Erro ou nick em uso", 'error');
        }

        if(t.classList.contains('upd-pass')) {
            const val = row.querySelector('.pass-in').value;
            if(!val) return;
            await fetch('/api/admin/update_password', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({user_id: uid, new_password: val})
            });
            showMsg("Senha alterada", 'success');
        }
    });

    loadUsers();
});