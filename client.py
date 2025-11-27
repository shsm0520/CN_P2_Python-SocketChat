import socket
import threading
import sys
import time
import re # Added for parsing the %connect command

# Global variables for connection state
ENCODE = 'UTF-8'
is_connected = False
client_socket: socket.socket = None
# Added global for username to allow the listener to reference it if needed for context
USERNAME = None 

def receive_handler(sock: socket.socket):
    """
    Listener thread: Stays blocked on sock.recv() to continuously listen 
    for and print server-sent messages and notifications.
    """
    global is_connected
    while is_connected:
        try:
            # The .recv() call will block, waiting for server data
            data = sock.recv(8192).decode(ENCODE) 
            
            if data:
                # Print the server's message/notification/response
                # Use sys.stdout.write to print above the current input prompt
                sys.stdout.write(f"\n{data.strip()}\n")
                
                # Redraw the input prompt line
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
            # Handle other errors (like socket closure from main thread)
            if is_connected:
                print("\n[ERROR] An unknown receive error occurred.")
            is_connected = False
            break
        
def cli_handler(sock: socket.socket):
    """
    Main thread: Handles user command input and sends commands to the server.
    """
    global is_connected
    while is_connected:
        try:
            # The input() call will block, waiting for user input
            command_line = input("> ")
            
            if not command_line:
                continue

            # Handle commands locally before sending (e.g., the initial %connect is handled in main)
            command_parts = command_line.split(' ', 1)
            command = command_parts[0].lower()
            
            if command == '%connect':
                 # Already handled in main() before the loop starts
                 print("[INFO] Already connected. Use '%join' or other commands.")
                 continue

            # Send commands to server
            sock.send(command_line.encode(ENCODE))
            
            # Check for the exit command to gracefully close
            if command == '%exit':
                # Give server a moment to send the final response
                time.sleep(0.5) 
                is_connected = False
                break
                
        except EOFError:
            # User hit Ctrl+D/Ctrl+Z
            print("\n[INFO] Exiting client.")
            is_connected = False
            # Send exit command to server to trigger cleanup
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
    
    # Handle %connect command before main loop
    while not is_connected:
        connect_command = input("Enter connection command (e.g., %connect 127.0.0.1 6789): ")
        
        # Use regex to validate and parse the command
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

    # Handle username exchange if connected
    if is_connected:
        try:
            # Handle the initial username prompt from the server
            initial_prompt = client_socket.recv(1024).decode(ENCODE).strip()
            # Loop until a valid/unique username is accepted
            while True:
                USERNAME = input(initial_prompt)
                client_socket.send(USERNAME.encode(ENCODE))

                # Receive server's response (either welcome or error)
                response = client_socket.recv(4096).decode(ENCODE)
                if "[ERROR] Username already in use" in response:
                    print(response)
                else:
                    print(f"\n{response.strip()}")
                    break
            
            # Start the listener thread (runs in background)
            listener_thread = threading.Thread(target=receive_handler, args=(client_socket,))
            listener_thread.daemon = True 
            listener_thread.start()

            # Run the command handler in the main thread
            cli_handler(client_socket)
            
            # Wait for the listener thread to pick up any final messages/exit confirmations
            listener_thread.join(timeout=1.0) 

        except KeyboardInterrupt:
            print("\nClient terminated by user.")
            if client_socket and is_connected:
                 client_socket.send(f"%exit".encode(ENCODE))
        except Exception as e:
            print(f"[FATAL ERROR] Client failed during operation: {e}")
        finally:
            # Cleanup
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
            print("[INFO] Client disconnected. Program exit.")

if __name__ == '__main__':
    main()