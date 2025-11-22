FROM python:3.11-slim

WORKDIR /srv/mesop-app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8080

# Correct mesop flags: --port instead of --host and --port
CMD ["mesop", "src/main.py", "--port=8080"]
