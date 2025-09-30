# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal

# --- Modelo de Usuário Customizado ---
class CustomUser(AbstractUser):
    # Opções para os campos de status
    STATUS_KYC_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
    ]
    RISCO_CHOICES = [
        ('BAIXO', 'Baixo'),
        ('MEDIO', 'Médio'),
        ('ALTO', 'Alto'),
        ('NAO_CALCULADO', 'Não Calculado'),
    ]

    # Campos adicionais ao usuário padrão do Django
    cpf = models.CharField(max_length=14, unique=True) # Ex: 123.456.789-00
    data_nascimento = models.DateField(null=True, blank=True)
    renda_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Campos para o processo de KYC
    foto_documento_frente = models.ImageField(upload_to='documentos/frente/', null=True, blank=True)
    foto_documento_verso = models.ImageField(upload_to='documentos/verso/', null=True, blank=True)

    selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    kyc_status = models.CharField(max_length=10, choices=STATUS_KYC_CHOICES, default='PENDENTE')
    
    # Campo para o resultado da análise de risco
    risco = models.CharField(max_length=15, choices=RISCO_CHOICES, default='NAO_CALCULADO')

    def __str__(self):
        return self.username

# --- Modelo de Empréstimo ---
class Emprestimo(models.Model):
    STATUS_EMPRESTIMO_CHOICES = [
        ('AGUARDANDO', 'Aguardando Investidor'),
        ('FINANCIADO', 'Financiado'),
        ('FINALIZADO', 'Finalizado'),
    ]

    # Relacionamento: Quem está pedindo o empréstimo
    tomador = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emprestimos_pedidos')
    
    # Relacionamento: Quem está investindo no empréstimo
    investidor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='emprestimos_investidos')

    valor_solicitado = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    taxa_juros = models.DecimalField(max_digits=5, decimal_places=2) # Ex: 5.00 para 5%
    meses_parcelamento = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Campos calculados para facilitar a visualização
    valor_total_pagamento = models.DecimalField(max_digits=10, decimal_places=2)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_EMPRESTIMO_CHOICES, default='AGUARDANDO')

    def __str__(self):
        return f"Empréstimo de R$ {self.valor_solicitado} para {self.tomador.username}"