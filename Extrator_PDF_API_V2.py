from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import tempfile
import io

app = Flask(__name__)

# Certifique-se de configurar o caminho para o executável do Tesseract OCR, se necessário.
# Exemplo: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extrair_texto_ocr_de_pagina_com_imagem(doc, pagina):
    texto_ocr = ''
    pix = pagina.get_pixmap()
    imagem = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    texto_ocr += pytesseract.image_to_string(imagem, lang='por')
    return texto_ocr

def extrair_texto_ocr_da_imagem_aperfeicoada(doc, pagina):
    texto_ocr = ''
    # Verifica se há texto selecionável na página antes de tentar OCR nas imagens
    texto_selecionavel = pagina.get_text("text")
    if texto_selecionavel:
        return texto_selecionavel
    else:
        # Para páginas sem texto selecionável, aplica a abordagem otimizada de OCR em toda a página
        return extrair_texto_ocr_de_pagina_com_imagem(doc, pagina)

def ocrizar_pdf(caminho_pdf):
    texto_ocr = ''
    try:
        with fitz.open(caminho_pdf) as doc:
            for pagina in doc:
                # Utiliza a função aperfeiçoada para extrair texto, seja diretamente ou via OCR
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
    
    # Utiliza um diretório temporário para salvar o arquivo
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
    texto_ocr = ocrizar_pdf(temp_path)
    
    # Remove o arquivo temporário e o diretório
    os.remove(temp_path)
    os.rmdir(temp_dir)
    
    if texto_ocr:
        return jsonify({"texto": texto_ocr}), 200
    else:
        return jsonify({"error": "Falha ao extrair texto do PDF"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    #app.run(debug=True)
