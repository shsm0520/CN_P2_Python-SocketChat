import socket
import threading
import Message
import Group
import datetime
from typing import Optional 

# Global Configuration and Concurrency Control
ENCODE = 'UTF-8'

# Global dictionary mapping username (str) -> client socket object (socket.socket)
# Tracks all active users. Access MUST be protected by the global LOCK
ALL_USERS: dict[str, socket.socket] = {} 

# Global lock for thread synchronization. Used to protect shared resources 
LOCK = threading.Lock() 

# Global dictionary holding all Group instances. Key is the group ID/name
ALL_GROUPS: dict[str, Group.Group] = {}
ALL_GROUPS['main'] = Group.Group() 
ALL_GROUPS['general'] = Group.Group() 
print(f"Initialized Groups: {list(ALL_GROUPS.keys())}")


def main():
    """Initializes the server socket, binds, listens, and enters the main connection loop."""

    # Create a TCP/IP socket
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow address reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind and listen configuration
    host = '0.0.0.0'  
    port = 6789 
    th = 5 # Backlog size

    try:
        server_socket.bind((host, port)) 
        server_socket.listen(th) 
        print(f"Server listening on {host}:{port}")

        # Main loop to accept new client connections
        while True:   
            client_socket, client_address = server_socket.accept() 
            
            # Start a new thread for each client to handle their requests concurrently
            new_t = threading.Thread(target=thread_main, args=(client_socket, client_address)) 
            new_t.daemon = True # Daemon threads won't block the server from exiting
            new_t.start() 
            print(f"[SERVER] Accepted connection from {client_address}")
            
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
    finally:
        server_socket.close()


def thread_main(client_socket: socket.socket, client_address):
    """
    The main execution function for each client's dedicated server thread.
    Handles command parsing and response logic.
    """
    username = None
    # Tracks the join time for each group (group_id: datetime) for history visibility
    user_group_join_time: dict[str, datetime.datetime] = {} 
    
    try:
        # Connect User and validate/get username
        username = user_connect(client_socket)
        
        # Main Command Loop
        while True:
            # Polling: Check and send any pending notifications before waiting for the next command
            send_notifications(client_socket, username)
            
            # Blocks here waiting for data (command) from the client
            data = client_socket.recv(4096)
            if not data: # Client disconnected cleanly
                break 
            
            client_input = data.decode(ENCODE).strip()
            print(f"[{username}] Received: {client_input}")
            
            # Parse command, handling complex arguments
            command_parts = client_input.split(' ', 3) 
            command = command_parts[0].lower().replace('%', '')
            response = ""

            # Command Handling
            if command == "groups":
                response = get_all_groups()

            elif command == "groupjoin" and len(command_parts) == 2:
                group_id = command_parts[1]
                response, join_time = group_join(group_id, username)
                # On successful join, record time, send success, AND display history immediately
                if "[SUCCESS]" in response:
                    user_group_join_time[group_id] = join_time
                    client_socket.send(response.encode(ENCODE))
                    display_messages(group_id, user_group_join_time[group_id], client_socket)
                    continue # Skip sending the response at the end of the loop

            elif command == "grouppost" and len(command_parts) >= 4:
                group_id = command_parts[1]
                subject = command_parts[2]
                content = command_parts[3] 
                response = group_post(group_id, username, subject, content)
                
            elif command == "groupusers" and len(command_parts) == 2:
                group_id = command_parts[1]
                response = group_view_users(group_id)

            elif command == "groupleave" and len(command_parts) == 2:
                group_id = command_parts[1]
                response = group_leave(group_id, username)
                # Remove join time from tracker if leave was successful
                if "[SUCCESS]" in response and group_id in user_group_join_time:
                    del user_group_join_time[group_id]
                
            elif command == "groupmessage" and len(command_parts) == 3:
                group_id = command_parts[1]
                message_id = command_parts[2]
                response = group_request_message(group_id, username, message_id)

            # Command Aliases (Map to 'main' group)
            elif command == "join": # %join -> %groupjoin main
                response, join_time = group_join('main', username)
                if "[SUCCESS]" in response:
                    user_group_join_time['main'] = join_time
                    client_socket.send(response.encode(ENCODE))
                    display_messages('main', user_group_join_time['main'], client_socket)
                    continue

            elif command == "post" and len(client_input.split(' ', 2)) == 3: # %post subject content -> %grouppost main subject content
                parts = client_input.split(' ', 2)
                subject = parts[1]
                content = parts[2]
                response = group_post('main', username, subject, content)

            elif command == "users": # %users -> %groupusers main
                response = group_view_users('main')

            elif command == "leave": # %leave -> %groupleave main
                response = group_leave('main', username)
                if "[SUCCESS]" in response and 'main' in user_group_join_time:
                    del user_group_join_time['main']
            
            elif command == "message" and len(command_parts) == 2: # %message ID -> %groupmessage main ID
                message_id = command_parts[1]
                response = group_request_message('main', username, message_id)
            
            # General Commands
            elif command == "exit": 
                response = "[INFO] Disconnecting..."
                client_socket.send(response.encode(ENCODE))
                break # Exit the while loop

            elif command == "connect":
                response = "[INFO] Already connected to server. Use '%groups' to see available groups."

            else:
                response = f"[ERROR] Unknown command or incorrect format: {client_input}"
            
            # Send the final response back to the client
            client_socket.send(response.encode(ENCODE))

    except ConnectionResetError:
        print(f"[DISCONNECT] Client {username if username else client_address} forcefully closed the connection.")
    except Exception as e:
        print(f"[THREAD ERROR] An error occurred for {username}: {e}")
    finally:
        # Final cleanup: remove user from global state and all groups
        user_exit(client_socket, username)

# Core Concurrency and Communication Helpers

def get_group_by_id(group_id: str) -> Optional[Group.Group]:
    """Retrieves a Group object safely using the global lock."""
    with LOCK:
        return ALL_GROUPS.get(group_id)


def user_connect(client_socket: socket.socket):
    """Handles the initial username exchange and validates for duplicates."""
    while True:
        try:
            client_socket.send("What is your username?".encode(ENCODE))
            username = client_socket.recv(1024).decode(ENCODE).strip() 
            
            if not username: continue

            # Check and add username to ALL_USERS
            LOCK.acquire()
            if username in ALL_USERS:
                LOCK.release()
                client_socket.send("[ERROR] Username already in use. Please try another.".encode(ENCODE))
                continue
            
            ALL_USERS[username] = client_socket
            LOCK.release()

            client_socket.send(f"[INFO] Welcome {username}\n[INFO] Use '%groups' to see available groups, and '%groupjoin id/name' to enter.".encode(ENCODE))
            return username
        except Exception:
            if LOCK.locked():
                 LOCK.release()
            raise


def user_exit(client_socket: socket.socket, username: str):
    """Cleans up the user's connection, removing them from all groups and notifying members."""
    if username:
        with LOCK:
            # Remove from global users dict
            ALL_USERS.pop(username, None)
            
            # Remove from all groups they were a member of
            for group_id, group_obj in ALL_GROUPS.items():
                if group_obj.validate_user(username):
                    group_obj.remove_user(username)
                    
                    # Queue notification for remaining users
                    notification = f"[NOTIFY] User {username} left the group."
                    for user in group_obj.group_users:
                        group_obj.add_notification(user, notification)

        print(f"[DISCONNECT] User {username} exited gracefully.")

    try:
        client_socket.close()
    except:
        pass


def send_notifications(client_socket: socket.socket, username: str):
    """
    Polling Function: Retrieves and sends all pending notifications from ALL groups 
    the user belongs to.
    """
    all_notifications: list[str] = []
    
    with LOCK:
        for group_id, group_obj in ALL_GROUPS.items():
            # Check if user is a member of the group
            if group_obj.validate_user(username):
                # Retrieves and CLEARS the queue for this user in this group
                group_notifications = group_obj.get_notifications(username)
                
                # Prefix notification with group ID for client context
                prefixed_notifications = [f"[GROUP:{group_id}] {n}" for n in group_notifications]
                all_notifications.extend(prefixed_notifications)
    
    if all_notifications:
        notification_block = "\n".join(all_notifications)
        client_socket.send(f"\n--- New Notifications ---\n{notification_block}\n-------------------------\n".encode(ENCODE))
    
    return


def display_messages(group_id: str, user_join_time: datetime.datetime, client_socket: socket.socket):
    """Formats and sends the visible message history to the client upon joining a group."""
    group_obj = get_group_by_id(group_id)
    
    if not group_obj:
        client_socket.send(f"[ERROR] Cannot display history. Group '{group_id}' not found.".encode(ENCODE))
        return

    # Logic relies on the Group.get_visible_messages() method to enforce history rules
    message_list: list[Message.Message] = group_obj.get_visible_messages(user_join_time)
    
    if not message_list:
        client_socket.send(f"[INFO] Group '{group_id}' is empty.".encode(ENCODE))
        return

    history_output = [f"--- Group: {group_id} History ---"]
    for message in message_list:
        history_output.append(
            f"ID: {message.id} | Sender: {message.username} | Date: {message.datetime.strftime('%A, %d %B %Y, %I:%M:%S%p')} | Subject: {message.subject}"
        )
    history_output.append("--------------------------------")
    
    client_socket.send("\n".join(history_output).encode(ENCODE))

# Group Command Implementations

def get_all_groups() -> str:
    """Returns a list of all available group IDs."""
    with LOCK:
        group_list = list(ALL_GROUPS.keys())
    
    # Display up to 5 groups (or all if less than 5)
    display_groups = group_list[:5]
    remaining_count = len(group_list) - len(display_groups)
    
    response = f"[INFO] Available Groups ({len(group_list)} total): {', '.join(display_groups)}"
    if remaining_count > 0:
        response += f" (+{remaining_count} more not displayed)"
        
    return response


def group_join(group_id: str, username: str) -> tuple[str, datetime.datetime]:
    """Adds a user to a group, records join time, and queues notifications for other members."""
    group_obj = get_group_by_id(group_id)
    join_time = datetime.datetime.now()

    if not group_obj:
        return (f"[ERROR] Group '{group_id}' not found.", join_time)

    with LOCK:
        success = group_obj.add_user(username)

    if success:
        # Notify all OTHER members of the group
        notification = f"[NOTIFY] User {username} joined the group."
        with LOCK:
            for user in group_obj.group_users:
                if user != username:
                    group_obj.add_notification(user, notification)
        
        return (f"[SUCCESS] You have successfully joined group '{group_id}'.", join_time)
    else:
        return (f"[INFO] You are already a member of group '{group_id}'.", join_time)


def group_post(group_id: str, username: str, subject: str, content: str) -> str:
    """Creates a new message in a group and notifies all current members."""
    group_obj = get_group_by_id(group_id)
    
    if not group_obj:
        return f"[ERROR] Group '{group_id}' not found."

    # Validation Check: User must be a member of the group to post
    if not group_obj.validate_user(username):
        return f"[ERROR] You must join group '{group_id}' before posting."

    curr_datetime = datetime.datetime.now()
    user_message = Message.Message(username, curr_datetime, subject, content)

    # Add message to group
    with LOCK:
        message_id = group_obj.add_message(user_message)
        
        # Notify all users in the group (excluding the sender)
        notification = f"[NOTIFY] New message from {username} (ID: {message_id}, Subject: {subject})"
        for user in group_obj.group_users:
            if user != username:
                group_obj.add_notification(user, notification)

    return f"[SUCCESS] Message posted to group '{group_id}' with ID: {message_id}"


def group_view_users(group_id: str) -> str:
    """Retrieves and formats the list of users in a group."""
    group_obj = get_group_by_id(group_id)

    if not group_obj:
        return f"[ERROR] Group '{group_id}' not found."

    user_list = group_obj.get_users()
    if not user_list:
        return f"[INFO] No users currently in group '{group_id}'."
        
    return f"[INFO] Users in group '{group_id}':\n{user_list}"


def group_leave(group_id: str, username: str) -> str:
    """Removes a user from a group and notifies remaining members."""
    group_obj = get_group_by_id(group_id)

    if not group_obj:
        return f"[ERROR] Group '{group_id}' not found."

    with LOCK:
        success = group_obj.remove_user(username)

    if success:
        # Queue notification for remaining members
        notification = f"[NOTIFY] User {username} left the group."
        with LOCK:
            for user in group_obj.group_users:
                group_obj.add_notification(user, notification)
        
        return f"[SUCCESS] You have successfully left group '{group_id}'."
    else:
        return f"[ERROR] You are not currently a member of group '{group_id}'."


def group_request_message(group_id: str, username: str, message_id: str) -> str:
    """Retrieves and formats a message's content from a specific group."""
    group_obj = get_group_by_id(group_id)

    if not group_obj:
        return f"[ERROR] Group '{group_id}' not found."
    
    # Validation Check: User must be a member of the group to retrieve the message
    if not group_obj.validate_user(username):
        return f"[ERROR] You must join group '{group_id}' to retrieve messages."


    if group_obj.validate_message_id(message_id):
        message: Message.Message = group_obj.retrieve_message(message_id)
        
        message_str = (
            f"--- Message ID: {message.id} (Group: {group_id}) ---\n"
            f"Sender: {message.username}\n"
            f"Date: {message.datetime.strftime('%A, %d %B %Y, %I:%M:%S%p')}\n"
            f"Subject: {message.subject}\n"
            f"---------------------------------------------------\n"
            f"{message.content}\n"
            f"---------------------------------------------------"
        )
        return message_str
    else:
        return f"[ERROR] Message ID '{message_id}' not found in group '{group_id}'."


if __name__ == "__main__":
   main()