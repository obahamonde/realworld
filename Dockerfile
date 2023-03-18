FROM python:3.7

ARG LOCAL_PATH

WORKDIR /app

COPY ${LOCAL_PATH} /app

RUN pip install --upgrade pip \
    pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]