from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance
import os
import tempfile
import io
import base64

app = Flask(__name__)

def parse_paginas_param(paginas_param):
    """
    Converte o parâmetro de páginas em uma lista de números de página.
    Aceita formatos como '1-5', '7,9,15' ou uma combinação '1-3,5'.
    """
    paginas = []
    for parte in paginas_param.split(','):
        if '-' in parte:
            inicio, fim = map(int, parte.split('-'))
            paginas.extend(range(inicio, fim + 1))
        else:
            paginas.append(int(parte))
    return paginas

# Funções extrair_texto_ocr_de_pagina_com_imagem e extrair_texto_ocr_da_imagem_aperfeicoada permanecem inalteradas

def ocrizar_pdf(caminho_pdf, paginas_param):
    texto_ocr = ''
    paginas_a_processar = parse_paginas_param(paginas_param)
    try:
        with fitz.open(caminho_pdf) as doc:
            for num_pagina in paginas_a_processar:
                if num_pagina <= len(doc):  # Verifica se o número da página é válido
                    pagina = doc.load_page(num_pagina - 1)  # PyMuPDF usa indexação base 0
                    texto_ocr += extrair_texto_ocr_da_imagem_aperfeicoada(doc, pagina)
    except Exception as e:
        return str(e)
    return texto_ocr

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'paginas' not in request.form:
        return jsonify({"error": "Parâmetro de páginas não enviado"}), 400
    paginas = request.form['paginas']

    # Verifica se o arquivo foi enviado como arquivo binário
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    # Verifica e trata se o arquivo foi enviado como string codificada em base64
    elif 'file' in request.form:
        file_content = request.form['file']
        file = io.BytesIO(base64.b64decode(file_content))
    else:
        return jsonify({"error": "Arquivo não enviado ou formato não suportado"}), 400

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "uploaded_file.pdf")  # Nome genérico para arquivo temporário
    with open(temp_path, 'wb') as f:
        f.write(file.read()) if isinstance(file, io.BytesIO) else file.save(temp_path)
    
    texto_ocr = ocrizar_pdf(temp_path, paginas)
    
    os.remove(temp_path)
    os.rmdir(temp_dir)
    
    if texto_ocr:
        return jsonify({"texto": texto_ocr}), 200
    else:
        return jsonify({"error": "Falha ao extrair texto do PDF"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
