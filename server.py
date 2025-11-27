import socket
import threading
import Message
import Group
import datetime

# user has to receive data when server sends data
# all caps comments are kinda for review from others
# exceptions are weird
# do we even need to worry about critical sections? users do not cause threads to interfere...

##later on add multithreading for handling multiple clients (project-2 1.Overview mentions it)
## because of that this code will be change form into class based structure


# def handle_client(client_socket, client_address):
#     print(f"Connection from {client_address}")

ENCODE = 'UTF-8'
ALL_USERS: dict[str, socket.socket] = {} # dict of users, of form username: client_socket, CRITICAL SECTION
LOCK = threading.Lock() # lock for multithreading synchronization
MAIN_GROUP = Group.Group() # initialize group

def main():

    # Create a TCP/IP socket
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set socket options to allow address reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the address and port
    host = '0.0.0.0'  # Listen on all interfaces
    port = 6789 # Port to listen on
    th = 5 # backlog, "number of unaccepted connections that the system will allow before refusing new connections"

    try:
        server_socket.bind((host, port)) # bind to port
        server_socket.listen(th) # open server socket for listening
        print(f"Server listening on {host}:{port}")

        while True:    # Wait for a connection
            client_socket, client_address = server_socket.accept() # accept connection
            # FIX: Pass client_address for logging purposes
            new_t = threading.Thread(target=thread_main, args=(client_socket, client_address)) # create thread
            new_t.daemon = True # Make thread daemon so it doesn't prevent server exit
            new_t.start() # start thread
            print(f"[SERVER] Accepted connection from {client_address}")
            
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
    finally:
        server_socket.close()

def thread_main(client_socket: socket.socket, client_address):
    """
    thread_main()
    socket parameter, client_address
    user_connect()
    while socket.recv(2048)
        split message
        match case structure to respond to commands
            exit - user_exit()
            message - user_request_message()
            post - user_post()
            join - user_join()
            leave - user_leave()
            view - user_view()
    """
    username = None
    user_join_time = None 
    
    try:
        # Connect User and get username
        username = user_connect(client_socket)
        
        # Main Command Loop
        while True:
            # Send notifications (if any) before waiting for new command
            send_notifications(client_socket, username)
            
            # get a command from client (blocking call)
            # FIX: Check for no data, which means a clean disconnect
            data = client_socket.recv(4096)
            if not data:
                break 
            
            client_input = data.decode(ENCODE).strip()
            print(f"[{username}] Received: {client_input}")
            
            # FIX: Robust command parsing using split(maxsplit=2)
            command_parts = client_input.split(' ', 2)
            command = command_parts[0].lower().replace('%', '') # strip '%' and make lowercase
            response = ""

            # Command Handling (Original match case structure now implemented with if/elif)
            if command == "exit": # user disconnect
                response = "[INFO] Disconnecting..."
                client_socket.send(response.encode(ENCODE))
                break # Exit loop, trigger cleanup
            
            elif command == "message" and len(command_parts) == 2: # user request message contents
                # command format: %message ID
                message_id = command_parts[1]
                if MAIN_GROUP.validate_user(username):
                    response = user_request_message(message_id)
                else: 
                    response = "[ERROR] You must join the group before requesting a message."

            elif command == "post" and len(command_parts) >= 3: # user post message
                # command format: %post subject content
                subject = command_parts[1]
                content = command_parts[2]
                if MAIN_GROUP.validate_user(username):                
                    response = user_post(username, subject, content)
                else:
                    response = "[ERROR] You must join the group before posting."
                
            elif command == "join": # user join group
                # FIX: Record join time *only* if the join is successful
                join_result = user_join(username)
                if "[SUCCESS]" in join_result:
                    user_join_time = datetime.datetime.now()
                    # Send initial visible messages immediately after joining success message
                    client_socket.send(join_result.encode(ENCODE))
                    display_messages(user_join_time, client_socket)
                    continue # Skip sending join_result again at the end
                response = join_result

            elif command == "leave": # user leave group
                # command format: %leave
                response = user_leave(username)
                if "[SUCCESS]" in response:
                    user_join_time = None
            
            elif command == "users": # user wants to view group
                # command format: %users
                if MAIN_GROUP.validate_user(username):
                    response = user_view()
                else:
                    response = "[ERROR] You are not part of the group!"
            
            # FIX: %connect is client-side logic handled before sending to server
            elif command == "connect":
                response = "[INFO] Already connected to server. Use '%join' to enter the main group."

            else:
                response = f"[ERROR] Unknown command or incorrect format: {client_input}"
            
            # Send the command response back to the client
            client_socket.send(response.encode(ENCODE))

    except ConnectionResetError:
        print(f"[DISCONNECT] Client {username if username else client_address} forcefully closed the connection.")
    except Exception as e:
        print(f"[THREAD ERROR] An error occurred for {username}: {e}")
    finally:
        user_exit(client_socket, username)


# Helper Functions

def user_exit(client_socket: socket.socket, username):
    """
    user_exit()
    (exit command)
    socket.close()
    for user in users
        user_notify() user that username left
    """
    if username:
        # Use LOCK for modifying shared data structures
        with LOCK:
            # Remove from global users dict
            ALL_USERS.pop(username, None)
            
            # Remove from group and notify others if they were in the group
            if MAIN_GROUP.validate_user(username):
                MAIN_GROUP.remove_user(username)
                
                # Notify all remaining users in the group
                notification = f"[NOTIFY] User {username} left the group."
                for user in MAIN_GROUP.group_users:
                    # FIX: Use add_notification instead of direct send
                    MAIN_GROUP.add_notification(user, notification) 

        print(f"[DISCONNECT] User {username} exited gracefully.")

    try:
        # close socket
        client_socket.close()
    except:
        pass
    return


def user_request_message(message_id: str) -> str:
    """
    (message command)
    socket.send(message_dict[id].encode())
    """
    # validate message id
    if MAIN_GROUP.validate_message_id(message_id):
        # grab message from Group.message_dict
        message: Message.Message = MAIN_GROUP.retrieve_message(message_id)

        # FIX: Send message with full format as required by project
        message_str = (
            f"--- Message ID: {message.id} ---\n"
            f"Sender: {message.username}\n"
            f"Date: {message.datetime.strftime('%A, %d %B %Y, %I:%M:%S%p')}\n"
            f"Subject: {message.subject}\n"
            f"Content: {message.content}"
        )
        return message_str
    else: # if message doesn't exist
        return f"[ERROR] Message with ID {message_id} does not exist!"


def user_post(username: str, subject: str, content: str) -> str:
    """
    (post command)
    create Message object
    lock acquire
    message_dict[message_id] = Message - CRITICAL SECTION
    lock release
    """
    
    # create datetime of post
    curr_datetime = datetime.datetime.now()

    # create message object
    user_message = Message.Message(username, curr_datetime, subject, content)

    # add message to group - CRITICAL SECTION
    LOCK.acquire()
    message_id = MAIN_GROUP.add_message(user_message)
    
    # Notify all users in the group (excluding the sender)
    notification = f"[NOTIFY] New message from {username} (ID: {message_id}, Subject: {subject})"
    for user in MAIN_GROUP.group_users:
        if user != username:
            MAIN_GROUP.add_notification(user, notification)
            
    LOCK.release()

    return f"[SUCCESS] Message posted with ID: {message_id}"


def user_join(username: str) -> str:
    """
    (join a group)
    lock acquire
    Group.group_users[username] = Socket - critical section
    lock release
    """

    # add user to group - CRITICAL SECTION
    LOCK.acquire()
    success = MAIN_GROUP.add_user(username)
    LOCK.release()

    if success:
        # notify users that new user has joined
        notification = f"[NOTIFY] User {username} joined the group."
        LOCK.acquire()
        for user in MAIN_GROUP.group_users:
            if user != username:
                MAIN_GROUP.add_notification(user, notification)
        LOCK.release()
        
        return "[SUCCESS] You have successfully joined the main group. You will now see the last 2 messages and all subsequent ones."
    else:
        return "[ERROR] You were unable to join the group: You are already part of the group!"


def user_leave(username: str) -> str:
    """
    (leave a group)
    lock acquire
    Group.group_users.pop(username, None)
    lock release
    """

    # remove user from group - CRITICAL SECTION
    LOCK.acquire()
    success = MAIN_GROUP.remove_user(username)
    LOCK.release()

    if success:
        # notify other users that user left
        notification = f"[NOTIFY] User {username} left the group."
        LOCK.acquire()
        for user in MAIN_GROUP.group_users:
            MAIN_GROUP.add_notification(user, notification)
        LOCK.release()
        
        # notify user success
        return "[SUCCESS] You have successfully left the group."
    else:
        # notify user failed to leave group
        return "[ERROR] You failed to leave group! You are not currently a member."


def user_connect(client_socket: socket.socket):
    """
    prompts user for username and adds them to ALL_USERS dictionary.
    """
    while True:
        try:
            # prompt username
            client_socket.send("What is your username?".encode(ENCODE))
            # receive username
            username = client_socket.recv(1024).decode(ENCODE).strip() 
            
            if not username: continue

            # add to USERS dictionary
            LOCK.acquire()
            if username in ALL_USERS:
                LOCK.release()
                client_socket.send("[ERROR] Username already in use. Please try another.".encode(ENCODE))
                continue
            
            ALL_USERS[username] = client_socket
            LOCK.release()

            # hello message
            client_socket.send(f"[INFO] Welcome {username}\n[INFO] Use '%join' to enter the main group.".encode(ENCODE))
            return username
        except Exception:
            LOCK.release()
            raise


def user_view() -> str:
    """get list of current users in group"""
    with LOCK:
        str_of_users = MAIN_GROUP.get_users() # get list of users as string delimited by '\n's
    
    return f"[INFO] Users in group:\n{str_of_users}"


def display_messages(user_join_time: datetime.datetime, client_socket: socket.socket):
    """
    display all messages that are visible to the user
    first gets list of them from MAIN_GROUP
    then builds a string and sends that string to the client
    """
    # get list of messages incl. 2 before join time
    message_list: list[Message.Message] = MAIN_GROUP.get_visible_messages(user_join_time)

    if not message_list:
        client_socket.send("[INFO] No visible messages found at time of join.".encode(ENCODE))
        return

    # send each message as a list to be displayed by user
    # in format of “Message ID, Sender, Post Date, Subject.”
    message_str = "\n--- Visible Messages (ID, Sender, Post Date, Subject) ---\n" # init message_str
    for message in message_list: # build message_str with list of visible messages
        message_str += (
            f"{message.id}, {message.username}, "
            f"{message.datetime.strftime('%A, %d %B %Y, %I:%M:%S%p')}, "
            f"{message.subject}\n"
        )
        # e.g. datetime is "Wednesday, 26 November 2025, 3:27:00PM"
        # format str for that is "%A, %d %B %Y, %I:%M:%S%p"
    message_str += "-----------------------------------------------------"
    
    client_socket.send(message_str.encode(ENCODE)) # send message str
    return 


def send_notifications(client_socket: socket.socket, username: str):
    """Retrieves and sends all pending notifications to the client."""
    notifications: list[str] = []
    
    # grab list of notifications from Group
    with LOCK:
        if MAIN_GROUP.validate_user(username):
            # FIX: get_notifications removes them from the group's dictionary
            notifications = MAIN_GROUP.get_notifications(username) 
    
    if notifications:
        # Combine all notifications into one message block for efficient sending
        notification_block = "\n".join(notifications)
        client_socket.send(f"\n--- New Notifications ---\n{notification_block}\n-------------------------\n".encode(ENCODE))
    
    return


if __name__ == "__main__":
   main()