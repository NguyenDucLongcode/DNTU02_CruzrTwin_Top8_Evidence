FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix /install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src ./src
ENV PYTHONPATH=/app
ENV LOG_DIR=/app/logs
RUN mkdir -p /app/logs
EXPOSE 5000
CMD ["python", "-m", "src.fiware.webhook_receiver"]
