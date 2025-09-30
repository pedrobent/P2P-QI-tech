# core/risk_analysis.py
from datetime import date

def calcular_risco(usuario):
    """
    Calcula o score de risco de um usuário com base em suas informações.
    Retorna uma tupla: (NÍVEL_DE_RISCO, score)
    """
    score = 0
    hoje = date.today()

    # 1. Análise baseada na Idade
    if usuario.data_nascimento:
        idade = hoje.year - usuario.data_nascimento.year - \
                ((hoje.month, hoje.day) < (usuario.data_nascimento.month, usuario.data_nascimento.day))
        
        if 18 <= idade < 25:
            score += 10 # Risco maior
        elif 25 <= idade < 45:
            score += 30 # Risco menor (estabilidade)
        elif idade >= 45:
            score += 25 # Risco moderado

    # 2. Análise baseada na Renda Mensal
    renda = float(usuario.renda_mensal)
    if renda <= 2000:
        score += 5  # Risco muito alto
    elif 2000 < renda <= 5000:
        score += 20 # Risco médio
    elif renda > 5000:
        score += 40 # Risco baixo

    # 3. (Simulação) Análise baseada em histórico de crédito
    # Em um sistema real, aqui você consultaria um bureau de crédito (Serasa, etc.).
    # Vamos simular com base no tempo de cadastro no nosso sistema.
    dias_de_cadastro = (hoje - usuario.date_joined.date()).days
    if dias_de_cadastro > 365:
        score += 15 # Usuário antigo é mais confiável

    # --- Definição do Nível de Risco com base no Score Final ---
    if score <= 30:
        risco = 'ALTO'
    elif 30 < score <= 60:
        risco = 'MEDIO'
    else: # score > 60
        risco = 'BAIXO'
        
    return (risco, score)