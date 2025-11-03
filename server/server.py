import socket
#import threading

##later on add multithreading for handling multiple clients (project-2 1.Overview mentions it)
## because of that this code will be change form into class based structure


# def handle_client(client_socket, client_address):
#     print(f"Connection from {client_address}")



# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Set socket options to allow address reuse
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the address and port
host = '0.0.0.0'  # Listen on all interfaces
port = 8080 # Port to listen on
th = 5
encode = 'UTF-8'


server_socket.bind((host, port))

server_socket.listen(th)
print(f"Server listening on {host}:{port}")


while True:    # Wait for a connection
    client_socket, client_address = server_socket.accept()
    try:
        print(f"Connection from {client_address}")
        # Receive the data in small chunks and retransmit it
        while True:
            data = client_socket.recv(1024).decode(encode)
            if data:
                print(f"Received: {data}")
                client_socket.sendall(data.encode(encode))  # Echo back the received data
            else:
                print("No more data from", client_address)
                break
    finally:
        # Clean up the connection
        client_socket.close()
