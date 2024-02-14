from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance
import os
import tempfile
import io

app = Flask(__name__)

# Função otimizada para extrair texto de páginas com imagens
def extrair_texto_ocr_de_pagina_com_imagem(doc, pagina):
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
    if texto_selecionavel:
        return texto_selecionavel
    else:
        # Aplica a abordagem otimizada de OCR em toda a página para páginas sem texto selecionável
        return extrair_texto_ocr_de_pagina_com_imagem(doc, pagina)

def ocrizar_pdf(caminho_pdf):
    texto_ocr = ''
    try:
        with fitz.open(caminho_pdf) as doc:
            for pagina in doc:
                texto_ocr += extrair_texto_ocr_da_imagem_aperfeicoada(doc, pagina)
    except Exception as e:
        return str(e)
    return texto_ocr

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "Arquivo não enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
    texto_ocr = ocrizar_pdf(temp_path)
    
    os.remove(temp_path)
    os.rmdir(temp_dir)
    
    if texto_ocr:
        return jsonify({"texto": texto_ocr}), 200
    else:
        return jsonify({"error": "Falha ao extrair texto do PDF"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
