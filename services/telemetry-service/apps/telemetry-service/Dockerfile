FROM python:3.14-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY apps/telemetry-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto /proto
COPY apps/telemetry-service/ .

RUN mkdir -p gen && python -m grpc_tools.protoc \
    -I /proto --python_out=gen --grpc_python_out=gen \
    /proto/telemetry/v1/telemetry.proto \
    && find gen -type d -exec touch {}/__init__.py \;

EXPOSE 50052
CMD ["python", "main.py"]
