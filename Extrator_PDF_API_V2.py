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

def extrair_texto_ocr_de_pagina_com_imagem(pagina):
    texto_ocr = ''
    pix = pagina.get_pixmap()
    imagem_original = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Redimensionamento da imagem - Reduz para 1500px de largura mantendo a proporção
    base_width = 1500
    w_percent = (base_width / float(imagem_original.size[0]))
    h_size = int((float(imagem_original.size[1]) * float(w_percent)))
    imagem_redimensionada = imagem_original.resize((base_width, h_size), Image.ANTIALIAS)

    # Ajuste de contraste
    enhancer = ImageEnhance.Contrast(imagem_redimensionada)
    imagem_contraste = enhancer.enhance(2)  # Ajuste o fator conforme necessário

    texto_ocr += pytesseract.image_to_string(imagem_contraste, lang='por')
    return texto_ocr

def extrair_texto_ocr_da_imagem_aperfeicoada(doc, pagina):
    texto_ocr = ''
    texto_selecionavel = pagina.get_text("text")
    if texto_selecionavel.strip():  # Verifica se o texto selecionável é apenas espaço em branco
        return texto_selecionavel
    else:
        # Processa a página como imagem se não houver texto selecionável
        return extrair_texto_ocr_de_pagina_com_imagem(pagina)

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

    # Tratamento de arquivos recebidos tanto como arquivos binários quanto como strings base64
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
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
