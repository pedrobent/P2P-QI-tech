import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.shortcuts import render, redirect
from .kyc_service import processar_kyc_automatico
import re

from .models import CustomUser, Emprestimo
from .validators import validar_cpf
from .risk_analysis import calcular_risco


@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({'mensagem': 'Login bem-sucedido!'})
        else:
            return JsonResponse({'erro': 'Usuário ou senha inválidos.'}, status=400)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard(request):
    return render(request, 'dashboard.html')

def login_page(request):
    return render(request, 'login.html')

def cadastro_page(request):
    return render(request, 'cadastro.html')
    
def pedir_emprestimo_page(request):
    return render(request, 'pedir_emprestimo.html')
    
def meus_emprestimos_page(request):
    return render(request, 'meus_emprestimos.html')


@csrf_exempt
@transaction.atomic
def cadastro(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if not validar_cpf(data['cpf']):
            return JsonResponse({'erro': 'CPF inválido'}, status=400)

        cpf_limpo = re.sub(r'[^\d]', '', data['cpf'])

        novo_usuario = CustomUser.objects.create(
            username=data['username'],
            password=make_password(data['password']),
            email=data['email'],
            cpf=cpf_limpo,
            data_nascimento=data['data_nascimento'],
            renda_mensal=Decimal(data['renda_mensal']),
            kyc_status='PENDENTE'
        )
        return JsonResponse(
            {'mensagem': f'Usuário {novo_usuario.username} criado com sucesso! Aguardando aprovação do KYC.'},
            status=201)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
@transaction.atomic
def analise_e_pedido_emprestimo(request):
    # --- Em um sistema real, a autenticação seria feita via tokens (JWT, etc.) ---
    # Para simplificar, vamos assumir que o ID do usuário é enviado no corpo da requisição.
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            user_id = data['user_id']
            tomador = CustomUser.objects.get(pk=user_id)
        except (CustomUser.DoesNotExist, KeyError):
            return JsonResponse({'erro': 'Usuário não encontrado'}, status=404)

        if tomador.kyc_status != 'APROVADO':
            return JsonResponse({'erro': 'KYC não aprovado. Não é possível pedir empréstimo.'}, status=403)

        risco, score = calcular_risco(tomador)
        tomador.risco = risco
        tomador.save()

        taxas = {'ALTO': Decimal('15.0'), 'MEDIO': Decimal('10.0'), 'BAIXO': Decimal('5.0')}
        taxa_juros = taxas[risco]

        valor_solicitado = Decimal(data['valor_solicitado'])
        meses_parcelamento = int(data['meses_parcelamento'])

        juros_total = valor_solicitado * (taxa_juros / 100)
        valor_total = valor_solicitado + juros_total
        valor_parcela = valor_total / meses_parcelamento
        
        novo_emprestimo = Emprestimo.objects.create(
            tomador=tomador,
            valor_solicitado=valor_solicitado,
            taxa_juros=taxa_juros,
            meses_parcelamento=meses_parcelamento,
            valor_total_pagamento=valor_total,
            valor_parcela=valor_parcela,
            status='AGUARDANDO'
        )
        
        return JsonResponse({
            'mensagem': 'Pedido de empréstimo criado com sucesso!',
            'id_emprestimo': novo_emprestimo.id,
            'risco_calculado': risco,
            'score': score,
            'taxa_juros_aplicada': f'{taxa_juros}%',
            'valor_total_a_pagar': f'{valor_total:.2f}',
            'valor_da_parcela': f'{valor_parcela:.2f}'
        }, status=201)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def listar_emprestimos_disponiveis(request):
    if request.method == 'GET':
        emprestimos = Emprestimo.objects.filter(status='AGUARDANDO').order_by('-data_criacao')

        lista_emprestimos = []
        for emp in emprestimos:
            lista_emprestimos.append({
                'id_emprestimo': emp.id,
                'tomador_username': emp.tomador.username,
                'risco_tomador': emp.tomador.risco,
                'valor_pedido': f'{emp.valor_solicitado:.2f}',
                'taxa_juros': f'{emp.taxa_juros}%',
                'parcelas': emp.meses_parcelamento,
                'valor_total_retorno': f'{emp.valor_total_pagamento:.2f}'
            })
            
        return JsonResponse({'emprestimos_disponiveis': lista_emprestimos}, status=200)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
@transaction.atomic
def financiar_emprestimo(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            emprestimo_id = data['emprestimo_id']
            investidor_id = data['investidor_id']
            
            emprestimo = Emprestimo.objects.get(pk=emprestimo_id)
            investidor = CustomUser.objects.get(pk=investidor_id)

        except (Emprestimo.DoesNotExist, CustomUser.DoesNotExist, KeyError):
            return JsonResponse({'erro': 'Empréstimo ou Investidor não encontrado.'}, status=404)

        if emprestimo.status != 'AGUARDANDO':
            return JsonResponse({'erro': 'Este empréstimo não está mais disponível para investimento.'}, status=400)

        if investidor.kyc_status != 'APROVADO':
            return JsonResponse({'erro': 'Ação não permitida. O KYC do investidor não está aprovado.'}, status=403)

        if emprestimo.tomador == investidor:
            return JsonResponse({'erro': 'Você não pode financiar seu próprio empréstimo.'}, status=400)
        
        emprestimo.investidor = investidor
        emprestimo.status = 'FINANCIADO'
        emprestimo.save()
        
        return JsonResponse({
            'mensagem': 'Empréstimo financiado com sucesso!',
            'emprestimo_id': emprestimo.id,
            'status_novo': emprestimo.status
        }, status=200)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
def iniciar_kyc_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        if not user_id:
            return JsonResponse({'erro': 'user_id é obrigatório'}, status=400)

        resultado = processar_kyc_automatico(user_id)

        return JsonResponse(resultado, status=200)
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def perfil_page(request):
    try:
        user = CustomUser.objects.get(pk=1)
        context = {'user': user}
    except CustomUser.DoesNotExist:
        context = {'user': None}

    return render(request, 'perfil.html', context)


@csrf_exempt
def upload_documentos_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        foto_documento_frente = request.FILES.get('foto_documento_frente')  # Modificado
        foto_documento_verso = request.FILES.get('foto_documento_verso')  # Adicionado
        selfie = request.FILES.get('selfie')

        if not all([user_id, foto_documento_frente, foto_documento_verso, selfie]):  # Modificado
            return JsonResponse({'erro': 'Todos os campos são obrigatórios.'}, status=400)

        try:
            usuario = CustomUser.objects.get(pk=user_id)
            usuario.foto_documento_frente = foto_documento_frente  # Modificado
            usuario.foto_documento_verso = foto_documento_verso  # Adicionado
            usuario.selfie = selfie
            usuario.save()
            return JsonResponse({'mensagem': 'Documentos enviados com sucesso!'}, status=200)
        except CustomUser.DoesNotExist:
            return JsonResponse({'erro': 'Usuário não encontrado.'}, status=404)

    return JsonResponse({'erro': 'Método não permitido'}, status=405)