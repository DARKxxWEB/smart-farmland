FROM python:3.14-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY apps/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto /proto
COPY apps/gateway/ .
COPY tools/fake-data /app/tools/fake-data

RUN mkdir -p gen && python -m grpc_tools.protoc \
    -I /proto --python_out=gen --grpc_python_out=gen \
    /proto/auth/v1/auth.proto \
    /proto/telemetry/v1/telemetry.proto \
    /proto/bi/v1/bi.proto \
    /proto/notification/v1/notification.proto \
    && find gen -type d -exec touch {}/__init__.py \;

EXPOSE 8000
CMD ["python", "main.py"]
