from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import requests
import io
import tempfile

app = Flask(__name__)

def baixar_arquivo_pdf(url):
    """Baixa um arquivo PDF do URL fornecido e retorna o caminho do arquivo temporário."""
    resposta = requests.get(url)
    if resposta.status_code == 200:
        # Cria um arquivo temporário para o PDF
        arquivo_temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        arquivo_temp.write(resposta.content)
        arquivo_temp.close()
        return arquivo_temp.name
    else:
        raise Exception(f"Erro ao baixar o arquivo PDF: Status {resposta.status_code}")

def extrair_texto_ocr_da_imagem(doc, pagina):
    texto_ocr = ''
    imagens = pagina.get_images(full=True)
    for img_index in imagens:
        xref = img_index[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        imagem = Image.open(io.BytesIO(image_bytes))
        texto_ocr += pytesseract.image_to_string(imagem)
    return texto_ocr

def ocrizar_pdf(caminho_pdf):
    texto_ocr = ''
    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto_ocr += pagina.get_text()
            texto_ocr += extrair_texto_ocr_da_imagem(doc, pagina)
    return texto_ocr

@app.route('/extrair_texto', methods=['POST'])
def extrair_texto():
    data = request.json
    url_pdf = data.get('url')
    if not url_pdf:
        return jsonify({"erro": "URL não fornecida"}), 400

    try:
        caminho_pdf = baixar_arquivo_pdf(url_pdf)
        texto_ocr = ocrizar_pdf(caminho_pdf)
        return jsonify({"texto": texto_ocr})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    #app.run(debug=True)
