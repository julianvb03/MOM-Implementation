import grpc
from concurrent import futures
import messages_pb2
import messages_pb2_grpc

class MessageServiceServicer(messages_pb2_grpc.MessageServiceServicer):
    def SendMessage(self, request, context):
        print(f"Mensaje recibido del cliente: {request.message}")
        return messages_pb2.MessageReply(response=f"Mensaje '{request.message}' recibido correctamente")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_MessageServiceServicer_to_server(MessageServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC escuchando en puerto 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
