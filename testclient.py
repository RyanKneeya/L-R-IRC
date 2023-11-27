import socket
import select
import sys

SERVER = 'localhost'
PORT = 58900



def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(message)
        except ConnectionResetError:
            #print("Server closed the connection.")
            print(f"{client_socket}")
            client_socket.close()
            break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))

    nickname = input("Enter your nickname: ")
    client.send(nickname.encode('utf-8'))
    channel = input("Enter the channel you would like to join: ")
    client.send(channel.encode('utf-8'))
    inputs = [client, sys.stdin]
    connection_closed = False

    try:
        while not connection_closed:
            readable, _, _ = select.select(inputs, [], [])
            for sock in readable:
                if sock == client:
                    try:
                        message = sock.recv(1024).decode('utf-8')
                        if message:
                            print(message)
                    except ConnectionResetError:
                        print("Server closed the connection.")
                        connection_closed = True
                        break
                else:
                    message = input()
                    client.send(message.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClient shutting down.")
        client.close()

if __name__ == "__main__":
    start_client()
