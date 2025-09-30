document.addEventListener('DOMContentLoaded', () => {
    fetchLoans();
});

        // Função para mapear o texto do risco para a classe CSS correta
const getRiskClass = (riskText) => {
    switch (riskText) {
        case 'ALTO':
            return 'risk-high';
        case 'MEDIO':
            return 'risk-medium';
        case 'BAIXO':
            return 'risk-low';
        default:
            return '';
    }
};

        // Função principal que busca os dados da API e constrói a interface
async function fetchLoans() {
    const container = document.getElementById('loan-list-container');
    const apiUrl = 'http://127.0.0.1:8000/api/emprestimos/';

            // Mostra uma mensagem de carregamento enquanto busca os dados
    container.innerHTML = '<h2>Empréstimos disponíveis para financiar</h2><p>Carregando oportunidades...</p>';

    try {
        const response = await fetch(apiUrl);

                // Verifica se a requisição foi bem-sucedida
        if (!response.ok) {
            throw new Error(`Erro na rede: ${response.statusText}`);
            }

        const data = await response.json();
                
                // Limpa a mensagem de carregamento
        container.innerHTML = '<h2>Empréstimos disponíveis para financiar</h2>';
                
        if (data.emprestimos_disponiveis && data.emprestimos_disponiveis.length > 0) {
                    // Itera sobre cada empréstimo recebido da API
            data.emprestimos_disponiveis.forEach(loan => {
                const riskClass = getRiskClass(loan.risco_tomador);

                        // Cria o HTML para o card do empréstimo usando os dados da API
                const loanCardHTML = `
                    <div class="loan-card" data-loan-id="${loan.id_emprestimo}">
                        <div class="loan-card__header">
                            <h3>Pedido de Empréstimo #${String(loan.id_emprestimo).padStart(3, '0')}</h3>
                            <span class="risk-tag ${riskClass}">${loan.risco_tomador.replace('_', ' ')}</span>
                        </div>
                        <div class="loan-card__body">
                            <div class="info-group">
                                <span class="label">Valor Pedido</span>
                                <span class="value">R$ ${loan.valor_pedido}</span>
                            </div>
                            <div class="info-group">
                                <span class="label">Juros (Retorno)</span>
                                <span class="value">${loan.taxa_juros}</span>
                            </div>
                            <div class="info-group">
                                <span class="label">Parcelas</span>
                                <span class="value">${loan.parcelas}x</span>
                            </div>
                            <div class="info-group">
                                <span class="label">Retorno Total</span>
                                <span class="value principal">R$ ${loan.valor_total_retorno}</span>
                            </div>
                        </div>
                        <div class="loan-card__footer">
                            <button class="btn btn-primary">Financiar Agora</button>
                        </div>
                    </div>
                `;

                        // Insere o HTML do novo card no final do container
                container.insertAdjacentHTML('beforeend', loanCardHTML);
            });
        }
        
        else {
                    // Mostra uma mensagem se não houver empréstimos disponíveis
            container.innerHTML += '<p>Nenhuma oportunidade de investimento no momento.</p>';
        }

    }
    
    catch (error) {
        console.error('Falha ao buscar empréstimos:', error);
        container.innerHTML = '<h2>Oops!</h2><p>Não foi possível carregar as oportunidades. Verifique se o servidor está rodando e tente novamente.</p>';
    }
}

async function financiarEmprestimo(loanId, investorId, cardElement) {
    const apiUrl = '/api/financiar/';
            
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                emprestimo_id: loanId,
                investidor_id: investorId
            })
        });

        if (response.ok) {
            const data = await response.json();
            alert(data.mensagem); // Exibe "Empréstimo financiado com sucesso!"
            cardElement.remove(); // Remove o card da tela
        } 
        
        else {
            // Se a API retornar um erro (ex: "você não pode financiar seu próprio empréstimo")
            const errorData = await response.json();
            alert(`Erro: ${errorData.erro}`);
        }
    }
    catch (error) {
        console.error('Falha ao financiar empréstimo:', error);
        alert('Ocorreu um erro de conexão. Tente novamente.');
    }
}