import socket
import select

# Server configuration
SERVER = 'localhost'
PORT = 58900
CHANNEL = '#mychannel'

# Dictionary to store client connections
clients = {}
channels = {}

def handle_client(client_socket, nickname, channel):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                broadcast(nickname + ": " + message, channel)
        except Exception as e:
            print(f"Error: {e}")
            remove_member()
            remove_client(client_socket, nickname)
            break

def broadcast(message, channel):
    if channel in channels:
        for client in channels[channel]:
            try:
                clients[client].send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error broadcasting: {e}")

def add_member(channel_name, member):
    if channel_name in channels:
        channels[channel_name].add(member)
    else:
        channels[channel_name] = {member}

# Removing a member from a channel
def remove_member(channel_name, member):
    if channel_name in channels and member in channels[channel_name]:
        channels[channel_name].remove(member)
        if not channels[channel_name]:  # Remove the channel if it becomes empty
            del channels[channel_name]

def remove_client(client_socket, nickname, channel):
    if client_socket in clients.values():
        del clients[nickname]
        print(f"Connection with {nickname} closed.")
        broadcast(f"{nickname} has left the chat.", channel)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, PORT))
    server.listen()

    print(f"[*] Listening on {SERVER}:{PORT}")

    inputs = [server]

    try:
        while True:
            readable, _, _ = select.select(inputs, [], [])
            for sock in readable:
                if sock == server:
                    client_socket, addr = server.accept()
                    nickname = client_socket.recv(1024).decode('utf-8')
                    channel = client_socket.recv(1024).decode('utf-8')
                    clients[nickname] = client_socket
                    add_member(channel, nickname)
                    inputs.append(client_socket)

                    print(f"[*] Accepted connection from {addr[0]}:{addr[1]} as {nickname}")

                    broadcast(f"{nickname} has joined the chat.", channel)

                    client_socket.send(f"Connected to {SERVER}:{PORT} as {nickname} in {channel}\n".encode('utf-8'))

                else:
                    data = sock.recv(1024)
                    if not data:
                        for nickname, client_socket in clients.items():
                            if client_socket == sock:
                                remove_client(sock, nickname, channel)
                                break
                    else:
                        for nickname, client_socket in clients.items():
                            if client_socket == sock:
                                handle_client(sock, nickname, channel)
                                break

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")

        # Close all client sockets
        for client_socket in list(clients.values()):
            try:
                client_socket.send("Server is shutting down. Goodbye!".encode('utf-8'))
                client_socket.close()
            except Exception as e:
                print(f"Error closing connection: {e}")

        # Close the server socket
        server.close()
        print("Server shut down.")

if __name__ == "__main__":
    start_server()
