FROM python:3.12-alpine

WORKDIR /app

RUN pip install "requests>=2.25.0" "protobuf>=3.19.0" "grpcio-tools<=1.78.0"

COPY . .

EXPOSE 50050
CMD [ "python3", "server.py" ]
