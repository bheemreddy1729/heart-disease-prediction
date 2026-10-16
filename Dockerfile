FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements-serving.txt .
RUN python -m pip install --no-cache-dir -r requirements-serving.txt \
    && useradd --create-home --uid 10001 app

COPY --chown=app:app src/ ./src/
COPY --chown=app:app models/heart_pipeline.joblib ./models/heart_pipeline.joblib

USER app
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.infer.api:app", "--host", "0.0.0.0", "--port", "8000"]
