# Multi-stage build for lean image size
FROM python:3.11-slim as builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/dependencies -r requirements.txt

# Final lean image
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/dependencies /usr/local/lib/python3.11/site-packages
COPY main.py .

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

ENV APP_VERSION=v1.0.0
ENV SIMULATE_FAILURE=false

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
