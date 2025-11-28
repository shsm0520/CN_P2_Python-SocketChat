import socket
import threading
import sys
import time
import re 
from typing import Optional 

# Global configuration and state
ENCODE = 'UTF-8'
is_connected = False
client_socket: Optional[socket.socket] = None
USERNAME: Optional[str] = None 

def receive_handler(sock: socket.socket):
    """
    Listener Thread (Background): Stays blocked on sock.recv() to continuously listen 
    for and print server-sent messages and asynchronous notifications.
    """
    global is_connected
    while is_connected:
        try:
            # Blocks here waiting for data (response or notification block) from the server
            data = sock.recv(8192).decode(ENCODE) 
            
            if data:
                # Print the server output on a new line
                sys.stdout.write(f"\n{data.strip()}\n")
                
                # Redraw the input prompt ("> ") so it appears after the output
                sys.stdout.write("> ")
                sys.stdout.flush() 
            else:
                # Server closed the connection cleanly (recv returns empty data)
                print("\n[INFO] Server closed the connection. Exiting.")
                is_connected = False
                break
        except ConnectionResetError:
            print("\n[ERROR] Connection lost unexpectedly (Server may have crashed).")
            is_connected = False
            break
        except Exception:
            if is_connected:
                print("\n[ERROR] An unknown receive error occurred.")
            is_connected = False
            break
        
def cli_handler(sock: socket.socket):
    """
    Main Thread (Foreground): Handles user command input and sends commands to the server.
    This thread is blocked whenever the program waits for user input.
    """
    global is_connected
    while is_connected:
        try:
            # Blocks here until the user types a command and presses Enter
            command_line = input("> ")
            
            if not command_line:
                continue

            command_parts = command_line.split(' ', 1)
            command = command_parts[0].lower()
            
            if command == '%connect':
                 print("[INFO] Already connected. Use '%groups' to see available groups.")
                 continue

            # Send the raw command string to the server
            sock.send(command_line.encode(ENCODE))
            
            if command == '%exit':
                time.sleep(0.5) 
                is_connected = False
                break
                
        except EOFError:
            print("\n[INFO] Exiting client.")
            is_connected = False
            if sock:
                sock.send(f"%exit".encode(ENCODE))
            break
        except Exception as e:
            print(f"[ERROR] An error occurred in CLI: {e}")
            is_connected = False
            break

def main():
    global is_connected, client_socket, USERNAME
    host = '127.0.0.1'
    port = 6789
    
    # Handle %connect command and socket initialization
    while not is_connected:
        connect_command = input("Enter connection command (e.g., %connect 127.0.0.1 6789): ")
        
        match = re.match(r"%connect\s+(\S+)\s+(\d+)", connect_command)

        if match:
            host = match.group(1)
            try:
                port = int(match.group(2))
            except ValueError:
                print("[ERROR] Invalid port number.")
                continue

            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))
                is_connected = True
                print(f"[SUCCESS] Attempting connection to {host}:{port}...")
                break
            except ConnectionRefusedError:
                print(f"[ERROR] Connection refused. Is the server running on {host}:{port}?")
            except Exception as e:
                print(f"[ERROR] Could not connect: {e}")
        else:
            print("[ERROR] Invalid command format. Use: %connect address port")

    # Handle initial username exchange and validation
    if is_connected and client_socket:
        try:
            initial_prompt = client_socket.recv(1024).decode(ENCODE).strip()
            while True:
                USERNAME = input(initial_prompt)
                client_socket.send(USERNAME.encode(ENCODE))

                # Wait for server response (validation or error)
                response = client_socket.recv(4096).decode(ENCODE)
                if "[ERROR] Username already in use" in response:
                    print(response)
                else:
                    print(f"\n{response.strip()}")
                    break
            
            # Start the non-blocking listener thread
            listener_thread = threading.Thread(target=receive_handler, args=(client_socket,))
            listener_thread.daemon = True 
            listener_thread.start()

            # Run the main command handler
            cli_handler(client_socket)
            
            # Wait for the listener thread to clean up
            listener_thread.join(timeout=1.0) 

        except KeyboardInterrupt:
            print("\nClient terminated by user.")
            if client_socket and is_connected:
                 client_socket.send(f"%exit".encode(ENCODE))
        except Exception as e:
            print(f"[FATAL ERROR] Client failed during operation: {e}")
        finally:
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
            print("[INFO] Client disconnected. Program exit.")

if __name__ == '__main__':
    main()