from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import requests
import io
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os

app = Flask(__name__)

def baixar_arquivo_pdf(url):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        return io.BytesIO(resposta.content)
    else:
        raise Exception(f"Erro ao baixar o arquivo PDF: Status {resposta.status_code}")

def interpretar_sequencia_paginas(sequencia):
    paginas = []
    partes = sequencia.split(',')
    for parte in partes:
        if '-' in parte:
            inicio, fim = map(int, parte.split('-'))
            paginas.extend(range(inicio, fim + 1))
        else:
            paginas.append(int(parte))
    return paginas

def extrair_texto_ocr_da_imagem(doc, pagina_numero):
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
    texto_pagina = ''
    pagina = doc.load_page(pagina_numero)
    texto_pagina += pagina.get_text()
    texto_pagina += extrair_texto_ocr_da_imagem(doc, pagina_numero)
    return texto_pagina

def ocrizar_pdf(arquivo_pdf, sequencia_paginas):
    texto_ocr = ''
    paginas_a_processar = interpretar_sequencia_paginas(sequencia_paginas)
    with fitz.open(stream=arquivo_pdf, filetype="pdf") as doc:
        with ThreadPoolExecutor() as executor:
            resultados = executor.map(lambda pagina: processar_pagina(doc, pagina) if pagina in paginas_a_processar else '', range(len(doc)))
            texto_ocr = ''.join(resultados)
    return texto_ocr

@app.route('/extrair_texto', methods=['POST'])
def extrair_texto():
    data = request.json
    url_pdf = data.get('url')
    sequencia_paginas = data.get('paginas')  # Novo parâmetro de entrada
    if not url_pdf or sequencia_paginas is None:
        return jsonify({"erro": "URL ou sequência de páginas não fornecida"}), 400

    try:
        arquivo_pdf = baixar_arquivo_pdf(url_pdf)
        texto_ocr = ocrizar_pdf(arquivo_pdf, sequencia_paginas)
        return jsonify({"texto": texto_ocr})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
