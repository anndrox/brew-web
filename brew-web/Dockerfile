FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

RUN mkdir -p /app/instance
RUN mkdir -p /app/logs

COPY . .

RUN chmod +x /app/entrypoint.sh
ENV PYTHONPATH=/app
ENTRYPOINT ["/app/entrypoint.sh"]
