from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance
import os
import tempfile
import io
import base64
from functools import lru_cache
import hashlib

app = Flask(__name__)

def generate_cache_key(file_content, pages):
    md5 = hashlib.md5(file_content).hexdigest()
    key = f"{md5}_{pages}"
    return key

def parse_paginas_param(paginas_param):
    paginas = []
    for parte in paginas_param.split(','):
        if '-' in parte:
            inicio, fim = map(int, parte.split('-'))
            paginas.extend(range(inicio, fim + 1))
        else:
            paginas.append(int(parte))
    return paginas

@lru_cache(maxsize=100)
def extrair_texto_ocr_de_pagina_com_imagem(pagina):
    texto_ocr = ''
    pix = pagina.get_pixmap()
    imagem_original = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Reduzindo a base_width para minimizar o uso de recursos
    base_width = 800
    w_percent = (base_width / float(imagem_original.size[0]))
    h_size = int((float(imagem_original.size[1]) * float(w_percent)))
    imagem_redimensionada = imagem_original.resize((base_width, h_size), Image.ANTIALIAS)

    # Reduz o fator de ajuste de contraste para minimizar o processamento
    enhancer = ImageEnhance.Contrast(imagem_redimensionada)
    imagem_contraste = enhancer.enhance(1.5)

    texto_ocr += pytesseract.image_to_string(imagem_contraste, lang='por')
    return texto_ocr

def ocrizar_pdf(caminho_pdf, paginas_param):
    texto_ocr = ''
    paginas_a_processar = parse_paginas_param(paginas_param)
    with fitz.open(caminho_pdf) as doc:
        for num_pagina in paginas_a_processar:
            if num_pagina <= len(doc):
                pagina = doc.load_page(num_pagina - 1)
                texto_ocr += extrair_texto_ocr_de_pagina_com_imagem(pagina)
    return texto_ocr

@app.route('/convert', methods=['POST'])
def convert_pdf():
    paginas = request.form.get('paginas', '')
    file_content = request.files['file'].read() if 'file' in request.files else base64.b64decode(request.form['file'])
    
    cache_key = generate_cache_key(file_content, paginas)
    cache_result = lru_cache(maxsize=100)(ocrizar_pdf)(cache_key, paginas)
    
    if cache_result:
        return jsonify({"texto": cache_result}), 200
    else:
        return jsonify({"error": "Falha ao extrair texto do PDF"}), 500

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
