import grpc
import messages_pb2
import messages_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = messages_pb2_grpc.MessageServiceStub(channel)

    mensaje = input("Escribe tu mensaje para enviar al servidor: ")
    response = stub.SendMessage(messages_pb2.MessageRequest(message=mensaje))
    print("Respuesta del servidor:", response.response)

if __name__ == '__main__':
    run()
