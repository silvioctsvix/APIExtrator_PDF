# Use uma imagem base oficial do Python como ponto de partida
FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Atualiza o sistema e instala o Tesseract OCR e o pacote de idioma português
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-por && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia os arquivos do projeto para o contêiner
COPY . /app

# Instala as dependências do projeto Python
RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Define a variável de ambiente TESSDATA_PREFIX
# Isso é necessário apenas se o pytesseract não conseguir encontrar os arquivos de dados do Tesseract por si só.
# A localização padrão após a instalação do Tesseract-OCR pelo apt-get geralmente não requer essa etapa,
# mas ela está aqui para referência.
# ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Comando para executar sua aplicação
CMD ["python", "Extrator_PDF_API_V2.py"]
