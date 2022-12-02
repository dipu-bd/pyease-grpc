rm abc_pb2*
python -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. abc.proto
python ../.. -I . abc.proto > abc_fds.json
