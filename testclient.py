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
    except socket.error as e:
        # Handle specific error codes, such as EAGAIN or EWOULDBLOCK, indicating no data is available
        if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
            print("No data available. Continuing...")
            #c#ontinue
        else:
            print(f"Socket error: {e}")
            #break
    except ConnectionResetError:
        #print("Server closed the connection.")
        print(f"{client_socket}")
        client_socket.close()
        #break
    except Exception as e:
        print(f"Error receiving message: {e}")
        #break

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
                #print(f'\nPlease Select an action:')
                #print(f'[1]: Send a message to a room\n[2]: Join/Create a room\n[3]: Leave a room\n[4]: List all rooms\n')
                if sock == client:
                    try:
                        receive_messages(sock)
                    except ConnectionResetError:
                        print("Server closed the connection.")
                        connection_closed = True
                        break
                else:
                    
                    message = input()
                    log(f"Sending message: {message}")
                    client.send(f'{channel}: {message}'.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClient shutting down.")
        client.close()

if __name__ == "__main__":
    start_client()
