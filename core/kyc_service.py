import face_recognition
from django.core.files.storage import default_storage
from .models import CustomUser
import pandas as pd
import requests
import io
import cv2
import re
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocessar_imagem_para_ocr(caminho_imagem):
    try:
        img = cv2.imread(caminho_imagem)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        cv2.imwrite('debug_ocr_image.png', thresh)
        print("DEBUG: Imagem pré-processada salva como 'debug_ocr_image.png'")

        return thresh
    except Exception as e:
        print(f"Erro no pré-processamento: {e}")
        return cv2.imread(caminho_imagem)

def extrair_cpf_de_imagem(caminho_imagem):
    try:
        imagem_processada = preprocessar_imagem_para_ocr(caminho_imagem)
        if imagem_processada is None:
            imagem_processada = caminho_imagem

        texto_extraido = pytesseract.image_to_string(imagem_processada, lang='por')

        padrao_cpf = r'\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}|\d{9}/\d{2}'
        matches = re.findall(padrao_cpf, texto_extraido)

        if matches:
            cpf_encontrado = re.sub(r'[^\d]', '', matches[0])
            if len(cpf_encontrado) == 11:
                return cpf_encontrado
    except Exception as e:
        print(f"Erro no OCR: {e}")
    return None

def verificar_faces(caminho_doc, caminho_selfie):
    try:
        img_doc = face_recognition.load_image_file(caminho_doc)
        img_selfie = face_recognition.load_image_file(caminho_selfie)

        encodings_doc = face_recognition.face_encodings(img_doc)
        encodings_selfie = face_recognition.face_encodings(img_selfie)

        if len(encodings_doc) == 1 and len(encodings_selfie) == 1:
            encoding_doc = encodings_doc[0]
            encoding_selfie = encodings_selfie[0]

            resultado = face_recognition.compare_faces([encoding_doc], encoding_selfie)
            return resultado[0]
    except Exception as e:
        print(f"Erro na verificação facial: {e}")
    return False

def consultar_base_publica_restritiva(cpf_usuario):
    """Verifica se um CPF está na lista de sanções do CEIS."""
    try:
        url_ceis = 'https://www.portaltransparencia.gov.br/pessoa-fisica/busca/lista?output=csv'

        print("Baixando dados do Portal da Transparência...")
        response = requests.get(url_ceis, stream=True)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), sep=';', encoding='utf-8')

        coluna_cpf_cnpj = 'CPF OU CNPJ DO SANCIONADO'
        if coluna_cpf_cnpj not in df.columns:
            print(f"AVISO: A coluna '{coluna_cpf_cnpj}' não foi encontrada no CSV.")
            return False

        cpf_formatado = f"{cpf_usuario[:3]}.{cpf_usuario[3:6]}.{cpf_usuario[6:9]}-{cpf_usuario[9:]}"

        if df[coluna_cpf_cnpj].str.contains(cpf_formatado).any():
            print(f"ALERTA: CPF {cpf_usuario} encontrado na lista restritiva do CEIS.")
            return True
            
    except Exception as e:
        print(f"Erro ao consultar base pública: {e}")

    return False


def processar_kyc_automatico(user_id):
    """Executa o pipeline completo de verificação de KYC para um usuário."""
    try:
        usuario = CustomUser.objects.get(pk=user_id)
        if not all([usuario.foto_documento_frente, usuario.foto_documento_verso, usuario.selfie]):
            return {'status': 'FALHA', 'motivo': 'Documentos não enviados.'}

        caminho_doc_frente = usuario.foto_documento_frente.path
        caminho_doc_verso = usuario.foto_documento_verso.path
        caminho_selfie = usuario.selfie.path

        print(f"Iniciando KYC para o usuário: {usuario.username}")

        cpf_documento = None

        print("Executando OCR na frente do documento...")
        cpf_documento = extrair_cpf_de_imagem(caminho_doc_frente)

        if not cpf_documento:
            print("CPF não encontrado na frente. Executando OCR no verso do documento...")
            cpf_documento = extrair_cpf_de_imagem(caminho_doc_verso)

        cpf_usuario_limpo = re.sub(r'[^\d]', '', usuario.cpf)

        print(f"DEBUG: Comparando OCR ('{cpf_documento}') com DB ('{cpf_usuario_limpo}')")

        ocr_ok = (cpf_documento is not None and cpf_documento == cpf_usuario_limpo)
        print(f"Verificação OCR: {'OK' if ocr_ok else 'FALHA'}")

        face_match_ok = verificar_faces(caminho_doc_frente, caminho_selfie)
        print(f"Verificação Facial: {'OK' if face_match_ok else 'FALHA'}")

        tem_restricao = consultar_base_publica_restritiva(usuario.cpf)
        base_publica_ok = not tem_restricao
        print(f"Consulta Base Pública: {'OK' if base_publica_ok else 'FALHA'}")

        if ocr_ok and face_match_ok and base_publica_ok:
            usuario.kyc_status = 'APROVADO'
            print("Resultado KYC: APROVADO")
        else:
            usuario.kyc_status = 'REPROVADO'
            print("Resultado KYC: REPROVADO")

        usuario.save()

        return {'status': usuario.kyc_status, 'detalhes': {
            'ocr_match': ocr_ok,
            'face_match': face_match_ok,
            'sem_restricoes_publicas': base_publica_ok
        }}

    except CustomUser.DoesNotExist:
        return {'status': 'FALHA', 'motivo': 'Usuário não encontrado.'}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'FALHA', 'motivo': str(e)}