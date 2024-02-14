from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance
import os
import tempfile
import io

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
                pagina = doc.load_page(num_pagina - 1)  # PyMuPDF usa indexação base 0
                texto_ocr += extrair_texto_ocr_da_imagem_aperfeicoada(doc, pagina)
    except Exception as e:
        return str(e)
    return texto_ocr

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'file' not in request.files or 'paginas' not in request.form:
        return jsonify({"error": "Arquivo ou parâmetro de páginas não enviado"}), 400
    
    file = request.files['file']
    paginas = request.form['paginas']  # Exemplo: "1-5,7,9,15"
    
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
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
