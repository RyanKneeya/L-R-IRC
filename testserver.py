import socket
import select
import pickle

# Server configuration
SERVER = 'localhost'
PORT = 58900
CHANNEL = '#mychannel'

# Dictionary to store client connections
clients = {}
#Dictionary to store active channels
channels = {}

#Broadcast now looks for where the sender is sending a message
#It then sends the message to all members of the room(s) EXCLUDING itself
#If the channel the sender is attempting to broadcast to does not exist, an error is thrown
#--------#
# @PARAM: message - the client message to be broadcast
# @PARAM: channel - the channel to broadcast to
# @PARAM: sender - the client nickname who sent the message
def broadcast(messageToBeSent, channel, sender):
    message = {'opcode': 10, 'payload': messageToBeSent}
    pickle_payload = pickle.dumps(message)
    if channel in channels:
        for client in channels[channel]:
            try:
                if client != sender:
                    clients[client].send(pickle_payload)
            except Exception as e:
                print(f"Error broadcasting: {e}")
    else:
        for client in clients:
            if client == sender:
                errmsg = f'Apologies, {channel} does not exist!'
                message = {'opcode': 10, 'payload': errmsg}
                pickle_payload = pickle.dumps(message)
                clients[client].send(pickle_payload)
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
                message = {'opcode': 20, 'channel': channel}
                pickle_payload = pickle.dumps(message)
                clients[client].send(pickle_payload)
    else:
        channels[channel] = {member}
        for client in clients:
            if client == member:
                message = {'opcode': 21, 'channel': channel}
                pickle_payload = pickle.dumps(message)
                clients[client].send(pickle_payload)

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
                payload = f'Error removing from {channel}'
                message = {'opcode': 404, 'payload': payload}
                pickle_payload = pickle.dumps(message)
                clients[client].send(pickle_payload)

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
def get_channel_members(channel):
    if channel in channels:
        members_list = channels[channel]
        members_string = ', '.join(members_list)
        return f'Members in {channel}: {members_string}'
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
    match data['opcode']:
        #Send a message to a specific channel
        case 1:
            for chan in data['channel'].split(','):
                broadcast(f'{nickname}: {data["payload"]}', chan, nickname)
        
        #Join/Create a channel
        case 2:
            add_member(data['channel'], nickname)
        
        #Leave a channel
        case 3:
            remove_member(nickname, data['channel'])
        
        #List all channels
        case 4:
            rooms = []
            for channel in channels:
                rooms.append(channel)
            message = {'opcode': 40, 'channels': rooms}
            pickle_payload = pickle.dumps(message)
            client_socket.send(pickle_payload)
        
        #List all channels client is part of
        case 5:
            mem_chan = get_member_channels(nickname)
            message = {'opcode': 50, 'channels': mem_chan}
            pickle_payload = pickle.dumps(message)
            client_socket.send(pickle_payload)
        
        #List all members of a selected channel
        case 6:
            members = get_channel_members(data['channel'])
            if not members:
                members = 'That channel does not exist.'
            message = {'opcode': 60, 'members': members}
            pickle_payload = pickle.dumps(message)
            client_socket.send(pickle_payload) 

#Handles the unserializing and pushing of the pickled data
#--------#
# @PARAM: client_socket - client's connection to the server
# @PARAM nickname - alias client goes by in the server
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
                    
                    pickle_chunk = b""
                    data = client_socket.recv(1024)
                    
                    if not data:
                        print(f'Error accepting connection from {addr[0]}:{addr[1]}...')
                        break
                    
                    pickle_chunk += data
                    unpickle = pickle.loads(pickle_chunk)
                    nickname = unpickle['nickname']
                    channel = unpickle['channel']
                    clients[nickname] = client_socket
                    add_member(channel, nickname)
                    inputs.append(client_socket)

                    print(f"[*] Accepted connection from {addr[0]}:{addr[1]} as {nickname}")

                    broadcast(f"{nickname} has joined the chat.\n", channel, None)

                    payload = f"Connected to {SERVER}:{PORT} as {nickname} in {channel}\n"
                    message = {'opcode': 10, 'payload': payload}
                    pickle_payload = pickle.dumps(message)
                    client_socket.send(pickle_payload)

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
                payload = "Server is shutting down. Goodbye!"
                message = {'opcode': 10, 'payload': payload}
                pickle_payload = pickle.dumps(message)
                client_socket.send(pickle_payload)
                client_socket.close()
            except Exception as e:
                print(f"Error closing connection: {e}")

        # Close the server socket
        server.close()
        print("Server shut down.")

if __name__ == "__main__":
    start_server()