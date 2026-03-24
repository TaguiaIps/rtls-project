FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/apps/api

COPY apps/api /workspace/apps/api

RUN python -m pip install --upgrade pip && \
    python -m pip install -e .[dev]

CMD ["uvicorn", "rtls_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
