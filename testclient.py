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

def handle_returncode(data):
    match data['opcode']:
        case 10:
            print(f'{data["payload"]}')
        
        #Handles joining a channel
        case 20:
            print(f'Successfully joined {data["channel"]}')
        
        #Handles creating a channel
        case 21:
            print(f'Successfully created {data["channel"]}')

        #Handles general errors from server if a serious error occurs
        #server will terminate connection and server will close
        case 404:
            print(f'{data["payload"]}')
        
        #Handles Listing all channels
        case 40:
            print(f'All Available Channels:')
            for room in data['channels']:
                print(f'-{room}')
        
        #Handles Listing channels a client is part of
        case 50:    
            print(f'You are currently part of:')
            for channel in data['channels']:
                print(f'-{channel}')
        
        #Handles Listing all members of a channel
        case 60:
            if isinstance(data['members'], str):
                print(f"{data['members']}")
            else:
                for member in data['members']:
                    print(f'-{member}')

#Interprets the messages back from the server and prints to the screen
def receive_messages(client_socket):
    message = client_socket.recv(1024)
    message = pickle.loads(message)
    if not message:
        raise ValueError()
    handle_returncode(message)
        

#Handles the opcode passed in. 
# NOTE: opcode is a string here, but we pass to server as an int
def handle_opcode(opcode, client):
    match opcode:
        case '1':
            #Code to send message to room
            channel = input("Select a channel: ")
            payload = input("Message: ")
            message = {'opcode': 1, 'channel': channel, 'payload': payload}
            return message
        case '2':
            #Code to join/create room
            channel = input("Choose a channel to join: ")
            message = {'opcode': 2, 'channel': channel}
            return message
        case '3':
            #Code to leave room
            channel = input("Choose a channel to leave: ")
            message = {'opcode': 3, 'channel': channel}
            return message
        case '4':
            #Code to list all rooms
            message = {'opcode': 4, 'payload': None}
            return message
        case '5':
            #Code to list rooms a member is part of
            message = {'opcode': 5, 'payload': None}
            return message
        case '6':
            #Code to list members of a room
            channel = input("Choose a channel to list its members: ")
            message = {'opcode': 6, 'channel': channel}
            return message
        case '0':
            #Code to handle initial client connection
            nickname = input("Enter your nickname: ")
            channel = input("Enter the channel you would like to join: ")
            message = {'opcode': 0, 'nickname': nickname, 'channel': channel}
            return message
        case '-1':
            #Returns -1 to indicate user wants to quit
            client.close()
            message = {'opcode': -1, 'payload': None} 
            return message

#Handles most of the client
#Establishes a connection with the server, 
#Allows nickname and initial channel to join/create
#Continues with interactive user loop
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))

    inputs = [client, sys.stdin]
    #Handles initial client connection 
    pickle_payload = pickle.dumps(handle_opcode('0', client))
    client.send(pickle_payload)
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
                    message = handle_opcode(opcode, client)
                    
                    if message['opcode'] == -1:
                        connection_closed = True
                        break
                    
                    pickle_payload = pickle.dumps(message)
                    client.send(pickle_payload)
                    print_menu()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClient shutting down.")
        client.close()

if __name__ == "__main__":
    start_client()