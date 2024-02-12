from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import requests
import io
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)

def baixar_arquivo_pdf(url):
    """Baixa um arquivo PDF do URL fornecido e retorna o objeto BytesIO."""
    resposta = requests.get(url)
    if resposta.status_code == 200:
        return io.BytesIO(resposta.content)
    else:
        raise Exception(f"Erro ao baixar o arquivo PDF: Status {resposta.status_code}")

def aplicar_ocr_se_necessario(doc):
    """Aplica OCR em todas as páginas de um documento PDF se o texto não for selecionável."""
    for numero_pagina in range(len(doc)):
        pagina = doc.load_page(numero_pagina)
        # Verifica se a página já tem texto selecionável
        if not pagina.get_text("text"):
            imagens = pagina.get_images(full=True)
            for img_index in imagens:
                xref = img_index[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                imagem = Image.open(io.BytesIO(image_bytes))
                texto_ocr = pytesseract.image_to_string(imagem)
                # Insere o texto OCRizado de volta na página de maneira simplificada
                pagina.insert_text((0, 0), texto_ocr, fontsize=11)  # Ajustar conforme necessário

def extrair_texto_ocr_da_imagem(doc, pagina_numero):
    """Extrai o texto usando OCR da imagem em uma página específica do documento."""
    texto_ocr = ''
    pagina = doc.load_page(pagina_numero)
    imagens = pagina.get_images(full=True)
    for img_index in imagens:
        xref = img_index[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        imagem = Image.open(io.BytesIO(image_bytes))
        texto_ocr += pytesseract.image_to_string(imagem)
    return texto_ocr

def processar_pagina(doc, pagina_numero):
    """Processa uma única página do documento, extraindo texto diretamente e via OCR se necessário."""
    texto_pagina = ''
    pagina = doc.load_page(pagina_numero)
    texto_pagina += pagina.get_text("text")
    texto_pagina += extrair_texto_ocr_da_imagem(doc, pagina_numero)
    return texto_pagina

def ocrizar_pdf(arquivo_pdf):
    """Realiza OCR no documento PDF, tornando-o selecionável, e extrai o texto."""
    texto_ocr = ''
    with fitz.open(stream=arquivo_pdf, filetype="pdf") as doc:
        aplicar_ocr_se_necessario(doc)  # Aplica OCR se necessário
        with ThreadPoolExecutor() as executor:
            resultados = executor.map(lambda pagina: processar_pagina(doc, pagina), range(len(doc)))
            texto_ocr = ''.join(resultados)
    return texto_ocr

@app.route('/extrair_texto', methods=['POST'])
def extrair_texto():
    """Endpoint para extrair texto de um PDF fornecido através de uma URL."""
    data = request.json
    url_pdf = data.get('url')
    if not url_pdf:
        return jsonify({"erro": "URL não fornecida"}), 400

    try:
        arquivo_pdf = baixar_arquivo_pdf(url_pdf)
        texto_ocr = ocrizar_pdf(arquivo_pdf)
        return jsonify({"texto": texto_ocr})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
