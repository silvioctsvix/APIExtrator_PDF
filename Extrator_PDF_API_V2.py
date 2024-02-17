from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import tempfile
import base64
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def parse_paginas_param(paginas_param):
    logging.info("Parsing páginas param")
    paginas = []
    for parte in paginas_param.split(','):
        if '-' in parte:
            inicio, fim = map(int, parte.split('-'))
            paginas.extend(range(inicio, fim + 1))
        else:
            paginas.append(int(parte))
    return paginas

def extrair_texto_ocr_de_pagina_com_imagem(pagina):
    logging.info("Extraindo texto OCR da página")
    texto_ocr = ''
    pix = pagina.get_pixmap()
    imagem_original = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Configurações customizadas do Tesseract podem ser ajustadas conforme a necessidade
    custom_config = '--oem 1 --psm 3'
    texto_ocr += pytesseract.image_to_string(imagem_original, lang='por', config=custom_config)
    return texto_ocr

def ocrizar_pdf(caminho_pdf, paginas_param):
    logging.info("Iniciando OCRização do PDF")
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
    if 'application/pdf' not in request.headers['Content-Type']:
        return jsonify({"error": "Formato de arquivo não suportado"}), 400
    
    file_content = request.data  # Lê o conteúdo binário do PDF diretamente do corpo da requisição

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "uploaded_file.pdf")
    
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    # Processamento do arquivo, ocrizar_pdf(temp_path), etc.

    os.remove(temp_path)
    os.rmdir(temp_dir)

    # Retorne uma resposta apropriada
    return jsonify({"mensagem": "Arquivo recebido e processado"}), 200

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
