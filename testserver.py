import socket
import select
import datetime
import pickle

# Server configuration
SERVER = 'localhost'
PORT = 58900
CHANNEL = '#mychannel'

# Dictionary to store client connections
clients = {}
channels = {}

#Broadcast now looks for where the sender is sending a message
#It then sends the message to all members of a room EXCLUDING itself
#If the channel the sender is attempting to broadcast to does not exist, an error is thrown
#--------#
# @PARAM: message - the client message to be broadcast
# @PARAM: channel - the channel to broadcast to
# @PARAM: sender - the client nickname who sent the message
def broadcast(message, channel, sender):
    if channel in channels:
        for client in channels[channel]:
            try:
                if client != sender:
                    clients[client].send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error broadcasting: {e}")
    else:
        for client in clients:
            if client == sender:
                errmsg = f'Apologies, {channel} does not exist!'
                clients[client].send(errmsg.encode('utf-8'))

#Adds a member to the channel they specifiy with a notification they have joined
#If the room did not exist, they are notified that they created the room
#--------#
# @PARAM: channel - the channel to be added to, or created and added to
# @PARAM: member - the client nickname to be added to the channel
def add_member(channel, member):
    if channel in channels:
        channels[channel].add(member)
        for client in clients:
            if client == member:
                clients[client].send(f'You have joined {channel}!'.encode('utf-8'))
    else:
        channels[channel] = {member}
        for client in clients:
            if client == member:
                clients[client].send(f'{channel} has been created!'.encode('utf-8'))

#Removing a member is now done by checking whether the channel exists, and if the client is a member of the channel
#If the room does not exist, or the client is not a member, they get a notification of failure to leave
#--------#
# @PARAM: member - the client nickname
# @PARAM channel - the channel to be removed from
def remove_member(member, channel):
    if channel in channels and member in channels[channel]:
        channels[channel].remove(member)
        broadcast(f'{member} has left {channel}', channel, None)
        if not channels[channel]:
            del channels[channel]
    else:
        for client in clients:
            if client == member:
                clients[client].send(f'Unable to remove you from {channel}'.encode('utf-8'))

#Returns a list of all channels a member is a part of
#--------#
# @PARAM: member - the client nickname whos list of channels will be returned
def get_member_channels(member):
    member_channels = []
    for channel, members in channels.items():
        if member in members:
            member_channels.append(channel)
    return member_channels

#Returns a list of all members in a given channel
#--------#
# @PARAM: channel - channel to display all members of

#NOTE MY BRAIN IS SLOW RN, cant figure out how to list members of a room
def get_channel_members(channel):
    channel_members = []
    if channel in channels:
        for member in channel:
            channel_members.append(member)
        return channel_members
    else:
        return None


#Removes the client from all channels they are currently in
#and severs their connection to the server
#-------#
# @PARAM: client_socket - the socket connection of the client
# @PARAM nickname - the client nickname to be removed
def remove_client(client_socket, nickname):
    for channel in get_member_channels(nickname):
            remove_member(nickname, channel)
    if client_socket in clients.values():
        del clients[nickname]
        print(f"Connection with {nickname} closed.")

#Case handling for the unserialized payload 
#Handles:
#       -Broadcasting to a channel
#       -Joining/Creating a channel
#       -Leaving a channel
#       -Listing all channels
#       -Listing all member joined channels
#       -Listing all members of a channel
#--------#
# @PARAM: client_socket - the client connection to the server
# @PARAM: nickname - client nickname 
# @PARAM data - the unserialized payload containing various fields
#               (See handle_opcode() in testclient.py)
def handle_post_pickle(client_socket, nickname, data):
    match data['header']:
        #Send a message to a specific channel
        case 1:
            broadcast(f'{nickname}: {data["message"]}', data['channel'], nickname)
        
        #Join/Create a channel
        case 2:
            add_member(data['channel'], nickname)
        
        #Leave a channel
        case 3:
            remove_member(nickname, data['channel'])
        
        #List all channels
        case 4:
            client_socket.send(f'All Available Channels:\n'.encode('utf-8'))
            for channel in channels:
                client_socket.send(f'-{channel}\n'.encode('utf-8'))
        
        #List all channels client is part of
        case 5:
            client_socket.send(f'You are currently part of:\n'.encode('utf-8'))
            for channel in get_member_channels(nickname):
                client_socket.send(f'-{channel}\n'.encode('utf-8'))
        
        #List all members of a selected channel
        case 6:
            if channels[data['channel']]:
                client_socket.send(f'Members in {data["channel"]}:\n'.encode('utf-8'))
                for member in channel:
                    client_socket.send(f'-{member}\n'.encode('utf-8')) 
            else:
                client_socket.send(f'{data["channel"]} does not exist...')

def handle_pickle(client_socket, nickname, pickle_chunk):
    try:
        unpickled_payload = pickle.loads(pickle_chunk)
        handle_post_pickle(client_socket, nickname, unpickled_payload)

    except Exception as e:
        print(f"Error: {e}")
        remove_client(client_socket, nickname)


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

                    broadcast(f"{nickname} has joined the chat.\n", channel, None)

                    client_socket.send(f"Connected to {SERVER}:{PORT} as {nickname} in {channel}\n".encode('utf-8'))

                else:
                    try:
                        pickle_chunk = b""
                        data = sock.recv(1024)
                        if not data:
                            for nickname, client_socket in clients.items():
                                if client_socket == sock:
                                    remove_client(sock, nickname)
                                    break
                        else:
                            pickle_chunk += data
                            for nickname, client_socket in clients.items():
                                if client_socket == sock:
                                    handle_pickle(sock, nickname, pickle_chunk)
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