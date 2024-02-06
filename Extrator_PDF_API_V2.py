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

def extrair_texto_ocr_da_imagem(doc, pagina):
    texto_ocr = ''
    imagens = pagina.get_images(full=True)
    for img_index in imagens:
        xref = img_index[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        # Convertendo bytes da imagem para um objeto PIL Image
        imagem = Image.open(io.BytesIO(image_bytes))
        texto_ocr += pytesseract.image_to_string(imagem)
    return texto_ocr

def ocrizar_pdf(caminho_pdf):
    texto_ocr = ''
    try:
        with fitz.open(caminho_pdf) as doc:
            for pagina in doc:
                # Extrai texto selecionável
                texto = pagina.get_text()
                texto_ocr += texto
                # Extrai texto de imagens usando OCR
                texto_ocr += extrair_texto_ocr_da_imagem(doc, pagina)
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
    app.run(debug=True)
