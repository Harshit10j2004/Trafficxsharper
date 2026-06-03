FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update -y && \
    apt-get install gcc -y && \
    apt-get clean -y && \
    apt-get install make -y && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --system --uid 1001 --group appuser

RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

RUN mkdir -p /home/ubuntu/alert/logs && \
    chown -R appuser:appuser /home/ubuntu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]

