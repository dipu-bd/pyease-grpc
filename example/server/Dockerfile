FROM python:3.8-alpine

WORKDIR /app

RUN pip3 install requests>=2.25.0 protobuf>=3.19.0 grpcio-tools

COPY . .

EXPOSE 50050
CMD [ "python3", "server.py" ]
