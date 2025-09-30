# core/validators.py
import re

def validar_cpf(cpf):
    """
    Valida o formato e os dígitos verificadores de um CPF.
    Retorna True se for válido, False caso contrário.
    """
    # Remove caracteres não numéricos
    cpf = ''.join(re.findall(r'\d', str(cpf)))

    if not cpf or len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Validação do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    # Validação do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False

    return True