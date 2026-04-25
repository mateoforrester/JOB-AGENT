FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY daily_search.py .
COPY candidato_perfil.md .
COPY cv_completo.md .

CMD ["python", "daily_search.py"]
