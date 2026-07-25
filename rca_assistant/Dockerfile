FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/dependencies -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/dependencies /usr/local/lib/python3.11/site-packages
COPY main.py .

RUN useradd -m rcauser && chown -R rcauser /app
USER rcauser

EXPOSE 8001

ENV GEMINI_API_KEY=""
ENV OPENAI_API_KEY=""

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
