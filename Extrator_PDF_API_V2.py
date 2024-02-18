from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import logging
import tempfile
import io

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

def preprocess_image(image_content):
    """
    Pré-processa a imagem para melhorar a qualidade da OCR.
    """
    # Converte o conteúdo binário para um objeto de imagem
    image = Image.open(io.BytesIO(image_content))
    
    # Redimensionamento (opcional, ajustar conforme necessário)
    base_width = 1500
    w_percent = (base_width / float(image.size[0]))
    h_size = int((float(image.size[1]) * float(w_percent)))
    image = image.resize((base_width, h_size), Image.ANTIALIAS)
    
    # Binarização
    image = image.convert('L')  # Convertendo para escala de cinza
    threshold = 200
    image = image.point(lambda p: p > threshold and 255)
    
    # Ajuste de contraste
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Ajustar o fator conforme necessário
    
    # Remoção de ruído
    image = image.filter(ImageFilter.MedianFilter())
    
    # Correção de rotação e alinhamento pode ser adicionada aqui se necessário
    
    return image

@app.route('/convert', methods=['POST'])
def convert():
    # Assume-se que a imagem chega em formato binário via request.files (ajustar conforme necessário)
    file_content = request.files['file'].read()
    
    paginas_param = request.form.get('paginas')
    paginas = parse_paginas_param(paginas_param)
    
    # Pré-processamento da imagem
    preprocessed_image = preprocess_image(file_content)
    
    # Salva a imagem pré-processada temporariamente para uso no pytesseract
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        preprocessed_image.save(temp, format="PNG")
        temp_path = temp.name
    
    # OCR usando pytesseract
    text = pytesseract.image_to_string(temp_path, lang='por')  # Ajustar o idioma conforme necessário
    
    # Limpeza do arquivo temporário
    os.remove(temp_path)
    
    return jsonify({"text": text})

if __name__ == '__main__':
    app.run(debug=True)
