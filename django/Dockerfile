FROM python:3.11-slim

# Install system dependencies including CA certificates
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

WORKDIR /home/app/webapp

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
