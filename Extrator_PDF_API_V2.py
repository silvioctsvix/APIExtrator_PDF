from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import requests
import io
import gc
import os

app = Flask(__name__)

def baixar_arquivo_pdf(url):
    """Baixa um arquivo PDF do URL fornecido e retorna o objeto BytesIO."""
    try:
        resposta = requests.get(url, timeout=10)  # Adiciona um timeout
        resposta.raise_for_status()  # Garante que erros sejam capturados
        return io.BytesIO(resposta.content)
    except requests.RequestException as e:
        raise Exception(f"Erro ao baixar o arquivo PDF: {e}")

def aplicar_ocr_se_necessario(doc):
    """Aplica OCR em todas as páginas de um documento PDF se o texto não for selecionável."""
    for numero_pagina in range(len(doc)):
        pagina = doc.load_page(numero_pagina)
        if not pagina.get_text("text"):
            imagens = pagina.get_images(full=True)
            for img_index in imagens:
                xref = img_index[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                imagem = Image.open(io.BytesIO(image_bytes))
                texto_ocr = pytesseract.image_to_string(imagem)
                pagina.insert_text((0, 0), texto_ocr, fontsize=11)  # Ajustar conforme necessário
                imagem.close()  # Libera recursos da imagem
        gc.collect()  # Força a coleta de lixo após o processamento de cada página

def ocrizar_pdf(arquivo_pdf):
    """Realiza OCR no documento PDF, tornando-o selecionável, e extrai o texto."""
    texto_ocr = ''
    with fitz.open(stream=arquivo_pdf, filetype="pdf") as doc:
        aplicar_ocr_se_necessario(doc)
        for pagina in range(len(doc)):
            pagina_doc = doc.load_page(pagina)
            texto_ocr += pagina_doc.get_text("text")
            gc.collect()  # Força a coleta de lixo após o processamento de cada página
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
    app.run(host='0.0.0.0', port=port, threaded=False)  # Limita a execução a um único thread
