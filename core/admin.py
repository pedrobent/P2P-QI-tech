# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Emprestimo

class CustomUserAdmin(UserAdmin):
    # Adicionamos os campos customizados ao painel de edição do usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            # AQUI ESTÁ A CORREÇÃO:
            'fields': ('cpf', 'data_nascimento', 'renda_mensal',
                       'foto_documento_frente', 'foto_documento_verso',
                       'selfie', 'kyc_status', 'risco'),
        }),
    )
    # Adicionamos campos à lista de visualização de usuários
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'kyc_status', 'risco')
    # Permite editar o status do KYC diretamente na lista
    list_editable = ('kyc_status',)
    # Adiciona um filtro por status do KYC
    list_filter = ('kyc_status', 'risco')

# Registra os modelos no admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Emprestimo)