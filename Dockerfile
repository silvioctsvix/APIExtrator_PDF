# Use uma imagem base oficial do Python como ponto de partida
FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos do projeto para o contêiner
COPY . /app

# Instala o Tesseract
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instala as dependências do projeto Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para executar sua aplicação
CMD ["python", "Extrator_PDF_API_V2.py"]
