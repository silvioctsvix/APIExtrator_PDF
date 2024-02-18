from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import logging
import tempfile
import os

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def parse_paginas_param(paginas_param):
    logging.info("Parsing páginas param")
    paginas = []
    if paginas_param:
        for parte in paginas_param.split(','):
            if '-' in parte:
                inicio, fim = map(int, parte.split('-'))
                paginas.extend(range(inicio, fim + 1))
            else:
                paginas.append(int(parte))
    return paginas

def preprocess_image(imagem_original):
    logging.info("Preprocessando imagem para OCR")
    # Aplicação de filtros para melhorar o OCR
    imagem = ImageEnhance.Contrast(imagem_original).enhance(2.0)  # Aumentar contraste
    imagem = imagem.convert('L').point(lambda x: 0 if x < 128 else 255, '1')  # Binarização
    imagem = imagem.filter(ImageFilter.MedianFilter())  # Remoção de ruído
    
    return imagem

def extrair_texto_ocr_de_pagina_com_imagem(pagina):
    logging.info("Extraindo texto OCR da página")
    texto_ocr = ''
    pix = pagina.get_pixmap()
    imagem_original = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Preprocessamento da imagem
    imagem_preprocessada = preprocess_image(imagem_original)

    custom_config = '--oem 1 --psm 3'
    texto_ocr += pytesseract.image_to_string(imagem_preprocessada, lang='por', config=custom_config)
    return texto_ocr

def ocrizar_pdf(caminho_pdf, paginas_param):
    logging.info("Iniciando OCRização do PDF")
    texto_ocr = ''
    paginas_a_processar = parse_paginas_param(paginas_param)
    with fitz.open(caminho_pdf) as doc:
        for num_pagina in paginas_a_processar:
            if num_pagina - 1 < len(doc):
                pagina = doc.load_page(num_pagina - 1)
                texto_ocr += extrair_texto_ocr_de_pagina_com_imagem(pagina)
            else:
                logging.warning(f"Página {num_pagina} não encontrada no documento.")
    return texto_ocr

@app.route('/convert', methods=['POST'])
def convert_pdf():
    logging.info("Iniciando conversão do PDF")
    paginas_param = request.args.get('paginas', '')

    if 'application/pdf' not in request.headers['Content-Type']:
        return jsonify({"error": "Formato de arquivo não suportado"}), 400

    file_content = request.data
    if len(file_content) == 0:
        return jsonify({"error": "Arquivo recebido está vazio"}), 400

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "uploaded_file.pdf")

    with open(temp_path, 'wb') as f:
        f.write(file_content)

    try:
        texto_ocr = ocrizar_pdf(temp_path, paginas_param)
    except Exception as e:
        logging.error(f"Erro ao processar PDF: {e}")
        return jsonify({"error": f"Falha ao processar PDF: {str(e)}"}), 500
    finally:
        os.remove(temp_path)
        os.rmdir(temp_dir)

    if texto_ocr:
        return jsonify({"texto": texto_ocr}), 200
    else:
        return jsonify({"error": "Nenhum texto extraído do PDF"}), 200

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
