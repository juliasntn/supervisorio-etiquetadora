function atualizarRelogio() {
    const agora = new Date();
    const horas = agora.getHours().toString().padStart(2, '0');
    const minutos = agora.getMinutes().toString().padStart(2, '0');
    const segundos = agora.getSeconds().toString().padStart(2, '0');
    document.getElementById('relogio').textContent = `${horas}:${minutos}:${segundos}`;
}

setInterval(atualizarRelogio, 1000);
atualizarRelogio(); // Atualizar imediatamente ao carregar

function atualizarRelogio() {
    const agora = new Date();
    const horas = agora.getHours().toString().padStart(2, '0');
    const minutos = agora.getMinutes().toString().padStart(2, '0');
    const segundos = agora.getSeconds().toString().padStart(2, '0');
    document.getElementById('relogio').textContent = `${horas}:${minutos}:${segundos}`;
}

setInterval(atualizarRelogio, 1000);
atualizarRelogio();

function funcoesBotoes() {
    document.addEventListener('DOMContentLoaded', () => {
        const modal = document.getElementById('modalEdicaoHora'); // Corrigido o ID
        const closeBtn = document.querySelector('.close');
        const cancelarBtn = document.getElementById('cancelarEdicao');
        const salvarBtn = document.getElementById('salvarEdicao');

        document.querySelectorAll('.btnAcao.editar').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                modal.style.display = 'block';
            });
        });

        closeBtn.onclick = () => modal.style.display = 'none';
        cancelarBtn.onclick = () => modal.style.display = 'none';

        salvarBtn.onclick = () => {
            const novaHora = document.getElementById('novaHora').value;
            const comentario = document.getElementById('comentario').value;

            if (!novaHora || !comentario) {
                alert('Por favor, preencha todos os campos.');
                return;
            }

            // Aqui você pode tratar a lógica da atualização no backend ou na tela
            console.log('Hora editada para:', novaHora);
            console.log('Motivo:', comentario);

            modal.style.display = 'none';
        };

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    });
}

funcoesBotoes();
