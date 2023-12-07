import socket
import select
import sys
import pickle

SERVER = 'localhost'
PORT = 58900

#Prints the user menu
def print_menu():
    print(f'\nPlease Select an action:\n*************************')
    print(f'[1]: Send a message to a room\n[2]: Join/Create a room\n[3]: Leave a room')
    print(f'[4]: List all rooms\n[5]: List Rooms you are in\n[6]: List Members in a room')
    print(f'[-1]: Exit Program\n*************************')

#Interprets the messages back from the server and prints to the screen
def receive_messages(client_socket):
    message = client_socket.recv(1024).decode('utf-8')
    if not message:
        raise ValueError()
    print(message)

#Handles the opcode passed in. 
# NOTE: opcode is a string here, but we pass to server as an int
def handle_opcode(opcode, client):
    match opcode:
        case '1':
            #Code to send message to room
            channel = input("Select a channel: ")
            message = input("Message: ")
            payload = {'header': 1, 'channel': channel, 'message': message}
            return payload
        case '2':
            #Code to join/create room
            channel = input("Choose a channel to join: ")
            payload = {'header': 2, 'channel': channel}
            return payload
        case '3':
            #Code to leave room
            channel = input("Choose a channel to leave: ")
            payload = {'header': 3, 'channel': channel}
            return payload
        case '4':
            #Code to list all rooms
            payload = {'header': 4, 'message': None}
            return payload
        case '5':
            #Code to list rooms a member is part of
            payload = {'header': 5, 'message': None}
            return payload
        case '6':
            #Code to list members of a room
            channel = input("Choose a channel to list its members: ")
            payload = {'header': 6, 'channel': channel}
            return payload
        case '-1':
            #Returns -1 to indicate user wants to quit
            client.close()
            payload = {'header': -1, 'message': None} 
            return payload

#Handles most of the client
#Establishes a connection with the server, 
#Allows nickname and initial channel to join/create
#Continues with interactive user loop
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
        print_menu()
        while not connection_closed:
            readable, _, _ = select.select(inputs, [], [])
            for sock in readable:
                if sock == client:
                    try:
                        receive_messages(sock)
                    except Exception as e:
                        print("Server closed the connection.")
                        connection_closed = True
                        break

                else:
                    valid_options = {'1', '2', '3', '4', '5', '6', '-1'}
                    opcode = input()
                    while opcode not in valid_options:
                        print("Thats not a valid input, please enter a number 1-6 or -1 to exit.")
                        opcode = input()
                    payload = handle_opcode(opcode, client)
                    
                    if payload['header'] == -1:
                        connection_closed = True
                        break
                    
                    pickle_payload = pickle.dumps(payload)
                    client.send(pickle_payload)
                    print_menu()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClient shutting down.")
        client.close()

if __name__ == "__main__":
    start_client()