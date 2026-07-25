FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY run.py .

# Run as non-root user
RUN useradd -m loaduser && chown -R loaduser /app
USER loaduser

ENV TARGET_URL=http://demo-app.default.svc.cluster.local
ENV REQUEST_INTERVAL=0.2

CMD ["python", "run.py"]
