FROM python:3.14-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY apps/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto /proto
COPY apps/notification-service/ .

RUN mkdir -p gen && python -m grpc_tools.protoc \
    -I /proto --python_out=gen --grpc_python_out=gen \
    /proto/notification/v1/notification.proto \
    && find gen -type d -exec touch {}/__init__.py \;

EXPOSE 50054
CMD ["python", "main.py"]
