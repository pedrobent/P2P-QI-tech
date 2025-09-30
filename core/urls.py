# core/urls.py
from django.urls import path
from . import views

# URLs que servem nossas páginas HTML
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_page, name='login'),
    path('cadastro/', views.cadastro_page, name='cadastro'),
    path('pedir-emprestimo/', views.pedir_emprestimo_page, name='pedir_emprestimo'),
    path('meus-emprestimos/', views.meus_emprestimos_page, name='meus_emprestimos'),
    path('perfil/', views.perfil_page, name='perfil'),
    path('logout/', views.logout_view, name='logout'),
]

# URLs da nossa API
# (Vamos separar para melhor organização no futuro, por enquanto está OK)
urlpatterns += [
    path('api/cadastro/', views.cadastro, name='api_cadastro'),
    path('api/pedir-emprestimo/', views.analise_e_pedido_emprestimo, name='api_pedir_emprestimo'),
    path('api/emprestimos/', views.listar_emprestimos_disponiveis, name='api_listar_emprestimos'),
    path('api/financiar/', views.financiar_emprestimo, name='api_financiar_emprestimo'),
    path('api/iniciar-kyc/', views.iniciar_kyc_view, name='api_iniciar_kyc'),
    path('api/upload-documentos/', views.upload_documentos_view, name='api_upload_documentos'),
    path('api/login/', views.login_api, name='api_login'),
]