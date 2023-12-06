import socket
import select
import datetime

# Server configuration
SERVER = 'localhost'
PORT = 58900
CHANNEL = '#mychannel'

# Dictionary to store client connections
clients = {}
channels = {}

def log(message):
    with open('server_log.txt', 'a') as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")

def handle_client(client_socket, nickname, channel, data):
    try:
        message = data.decode('utf-8')
        if message:
            log(f"Received message from {nickname} in {channel}: {message}")
            broadcast(nickname + ": " + message, channel)
    except Exception as e:
        print(f"Error: {e}")
        remove_member()
        remove_client(client_socket, nickname)

def broadcast(message, channel):
    if channel in channels:
        for client in channels[channel]:
            try:
                clients[client].send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error broadcasting: {e}")

#add member to a channel
def add_member(channel_name, member):
    if channel_name in channels:
        channels[channel_name].add(member)
    else:
        channels[channel_name] = {member}

# Removing a member from a channel
def remove_member(member):
    for channel_name in get_member_channels(member):
        if channel_name in channels and member in channels[channel_name]:
            broadcast(f"{member} has left the chat.", channel_name)
            channels[channel_name].remove(member)
            if not channels[channel_name]:  # Remove the channel if it becomes empty
                del channels[channel_name]

#Finding what channels a member is apart of
def get_member_channels(member):
    member_channels = []
    for channel, members in channels.items():
        if member in members:
            member_channels.append(channel)
    return member_channels

def remove_client(client_socket, nickname):
    remove_member(nickname)
    if client_socket in clients.values():
        del clients[nickname]
        print(f"Connection with {nickname} closed.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, PORT))
    server.listen()
    server.setblocking(0)

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
                    try:
                        data = sock.recv(1024)
                        if not data:
                            for nickname, client_socket in clients.items():
                                if client_socket == sock:
                                    remove_client(sock, nickname)
                                    break
                        else:
                            for nickname, client_socket in clients.items():
                                if client_socket == sock:
                                    handle_client(sock, nickname, channel, data)
                                    break
                    except ConnectionResetError:
                        print("Connection reset by peer")

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
