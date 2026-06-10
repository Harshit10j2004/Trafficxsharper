FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update -y && \
    apt-get install gcc -y && \
    apt-get clean -y && \
    apt-get install make -y && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --system --uid 1001 --group --home /home/appuser appuser

RUN mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

ENV HOME=/home/appuser

RUN mkdir -p /app/logs /app/base_file && \
    chown -R appuser:appuser /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]

