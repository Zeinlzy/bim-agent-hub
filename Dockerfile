# ===== Build stage =====
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/build/deps -r requirements.txt

# ===== Runtime stage =====
FROM python:3.12-slim

ENV PORT=8000

COPY --from=builder /build/deps /usr/local

WORKDIR /app
COPY ./app ./app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/v1/health')"

EXPOSE ${PORT}
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
