import socket
import select
import sys
import datetime
import errno

SERVER = 'localhost'
PORT = 58900

#test
def log(message):
    with open('client_log.txt', 'a') as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")


def receive_messages(client_socket):
    try:
        message = client_socket.recv(1024).decode('utf-8')
        if not message:
            print(f'Message does not exist')
            #break
        print(message)
    except ConnectionResetError:
        print("Server closed the connection.")
        print(f"{client_socket}")
        client_socket.close()
        #break
    except Exception as e:
        print(f"Error receiving message: {e}")
        #break

def handle_opcode(opcode):
    match opcode:
        case 1:
            #Code to send message to room
            message = input("Message: ")
            payload = {'header': 1}
            pass
        case 2:
            #Code to join/create room
            pass
        case 3:
            #Code to leave room
            pass
        case 4:
            #Code to list all rooms
            pass
        case 5:
            #Returns -1 to indicate user wants to quit 
            return (-1)

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
        print(f'\nPlease Select an action:')
        print(f'[1]: Send a message to a room\n[2]: Join/Create a room\n[3]: Leave a room\n[4]: List all rooms\n[5]: Exit Program\n')
        while not connection_closed:
            #Really hard to get anything to print when you want an input cause select doesnt like that
            readable, _, _ = select.select(inputs, [], [])
            for sock in readable:
                if sock == client:
                    try:
                        receive_messages(sock)
                    except ConnectionResetError:
                        print("Server closed the connection.")
                        connection_closed = True
                        break
                else:
                    print(f'\nPlease Select an action:')
                    print(f'[1]: Send a message to a room\n[2]: Join/Create a room\n[3]: Leave a room\n[4]: List all rooms\n[5]: Exit Program\n')
                    #opcode = input()
                    message = input()
                    client.send(f'{channel}: {message}'.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClient shutting down.")
        client.close()

if __name__ == "__main__":
    start_client()
