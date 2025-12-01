FROM python:3.11-slim

WORKDIR /app
COPY app.py .

ENV PORT=8080 \
    APP_VERSION=1.0.0 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import http.client; http.client.HTTPConnection('localhost:8080').request('GET', '/health'); exit(0)"

CMD ["python", "app.py"]
