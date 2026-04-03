FROM python:3.11-slim

# Creiamo una cartella di lavoro dentro il container
WORKDIR /app

# Copiamo prima solo requirements.txt (ottimizzazione cache Docker)
COPY requirements.txt .

# Installiamo le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copiamo tutto il resto del progetto
COPY . .

RUN mkdir -p /app/cache && chmod 777 /app/cache

# Esponiamo la porta su cui gira Streamlit
EXPOSE 8501

# Comando che parte quando il container si avvia
CMD ["streamlit", "run", "Home.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
