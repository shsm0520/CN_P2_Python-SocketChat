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
ALL_USERS = {} # dict of users, of form username: client_socket, CRITICAL SECTION
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

    server_socket.bind((host, port)) # bind to port

    server_socket.listen(th) # open server socket for listening
    print(f"Server listening on {host}:{port}")

    while True:    # Wait for a connection
        client_socket, client_address = server_socket.accept() # accept connection
        new_t = threading.Thread(target=thread_main, args=(client_socket)) # create thread
        new_t.start() # start thread
        print("main")



def thread_main(client_socket: socket.socket):
    """
    thread_main()
    socket parameter
    user_connect()
    while socket.recv(2048) ????
        split message
        match case structure to respond to commands
            exit - user_exit()
            message - user_request_message()
            post - user_post()
            join - user_join()
            leave - user_leave()
    """
    # connect user
    username = user_connect(client_socket) # client should prepare to recv() two messages, one for prompt, one for hello
    # print(ALL_USERS) # test user_connect
    user_join_time = datetime.datetime.now()

    while True:
        # send messages that are visible to the user
        if MAIN_GROUP.validate_user(username): # if user is in the main group
            display_messages(user_join_time, client_socket) # client should adjust recv buffer because it might be a lot more than 1024

        # send notifications to user
        if MAIN_GROUP.validate_user(username): # if user is in the main gruop, send notifs for that user if there are any
            send_notifications(client_socket, username) # client should prepare to recv() many times, perhaps with a buffer larger than 1024
                                                        # but the beginning of each notif says how many remaining notifs there are so client
                                                        # can loop appropriately

        # get a command from client
        client_input = client_socket.recv(4096).decode(ENCODE)

        # split data
        command = client_input[:client_input.find[" "]] # command is everything in data until first space
        input_remainder = client_input[client_input.find[" "] + 1:] # remainder is everything in data after command, not including space

        # match case command
        match command:
            case "exit": # user disconnect
                user_exit(client_socket, username)
                return
            case "message": # user request message contents
                # client should be prepared to recv() once
                
                # validate if user is in group before they can request a message
                if MAIN_GROUP.validate_user(username):
                    user_request_message(client_socket, input_remainder)
                else: # if user not in the group
                    client_socket.send("You're not part of a group!\n".encode(ENCODE))
            case "post": # user post message
                # client should be prepared to recv() once for validation/error reporting
                
                # validate if user is in group before they can post a message
                if MAIN_GROUP.validate_user(username):                
                    user_post(username, input_remainder, client_socket)
                else:
                    client_socket.send("You're not part of a group!\n".encode(ENCODE))
            case "join": # user join group
                # client should be prepared to recv() once

                user_join(client_socket, username)
            case "leave": # user leave group
                # client should be prepare to recv() once

                user_leave(client_socket, username)
            case "view": # user wants to view group
                # client should be prepared to recv() once
                if MAIN_GROUP.validate_user(username):
                    user_view(client_socket)
                else:
                    client_socket.send("You are not part of the group!\n".encode(ENCODE))
            case _:
                client_socket.send(f"{command} is not a command\n".encode())



def user_exit(client_socket: socket.socket, username):
    """
    user_exit()
    (exit command)
    socket.close()
    for user in users
        user_notify() user that username left
    """

    # goodbye message? 

    # close socket
    client_socket.close()
    return



def user_request_message(client_socket: socket.socket, client_input: str):
    """
    pseudocode: 
    (message command)
    (command format: "message message_id")
    get message_id from line
    socket.send(message_dict[id].encode())
    """

    # FOR CONSISTENCY, SHOULD THE MESSAGE HAVE AN OPTION LIKE "message -i message_id"?

    # get message_id, should just be remainder of client input
    message_id = client_input

    # validate message id
    if MAIN_GROUP.validate_message_id(message_id):
        # grab message from Group.message_dict
        message: Message.Message = MAIN_GROUP.retrieve_message(message_id)

        # send message
        client_socket.send(f"Message {message.id}:]\nSubject: {message.subject}\nContent: {message.content}\n".encode(ENCODE))
    else: # if message doen't exist
        client_socket.send(f"Message {message_id} does not exist!\n".encode(ENCODE))
    return



def user_post(username: str, client_input: str, client_socket: socket.socket):
    """
    pseudocode: 
    (post command)
    ("post -s subject -c content)
    create datetime
    create Message object
    lock acquire
    message_dict[message_id] = Message - CRITICAL SECTION
    lock release
    """

    # client_input should be
    # "-s subject -c content"

    # get subject and content
    first_option = client_input[:client_input.find(" ")] # should be "-s"
    remainder = client_input[client_input.find(" ") + 1:] # remainder of input after first option
    if first_option != "-s":
        raise TypeError(f"user_post: first option should be '-s' not {first_option}\n")
    # ITS POSSIBLE FOR A USER TO PUT A FAKE COMMAND BETWEEN -s AND -c, SHOULD WE VALDIATE THAT INPUT?
    if " -c " not in remainder:
        raise TypeError(f"user_post: can't find ' -c ' to indicate message content\n")
    subject = remainder[:remainder.find(" -c ")] # get subject (everything before -c)
    content = remainder[remainder.find(" -c ") + 4:] # rest should be content
                                                     # +4 because that's the length of ' -c '    

    # create datetime of post
    curr_datetime = datetime.datetime.now()

    # create message object
    user_message = Message.Message(username, curr_datetime, subject, content)

    # add message to group - CRITICAL SECTION
    LOCK.acquire()
    MAIN_GROUP.add_message(user_message)
    LOCK.release()

    # send message of confirmation to user?
    client_socket.send("Message posted\n".encode(ENCODE))

    return



def user_join(client_socket: socket.socket, username: str):
    """
    pseudo_code:
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
        for user in MAIN_GROUP.group_users:
            MAIN_GROUP.add_notification(user, f"User {username} joined\n")
        # send message to client that they joined the group
        client_socket.send("You succesfully joined!\n".encode(ENCODE))
    else:
        # notify user that they were unable to join
        client_socket.send("You were unable to join the group\n".encode(ENCODE))

    return



def user_leave(client_socket: socket.socket, username: str):
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
        for user in MAIN_GROUP.group_users:
            MAIN_GROUP.add_notification(user, f"User {username} disconnected\n")
        
        # notify user success
        client_socket.send("You succesfully left!\n".encode(ENCODE))
    else:
        # notify user failed to leave group
        client_socket.send("You failed to leave group!\n".encode(ENCODE))

    return



def user_connect(client_socket: socket.socket):
    """
    pseudocode: 
    user_connect()
        prompt user name
            socket.send("what is your username".encode())
            username = socket.recv(2048).decode()
        lock acquire
        add to users - CRITICAL SECTION
        lock release
        notify other users that someone connected
            for user in users:
                user_notify(user, "someone joined")
        send last 2 messages
    """
    # prompt username
    client_socket.send("What is your username?".encode(ENCODE))
    username = client_socket.recv(1024).decode(ENCODE) # receive username

    # add to USERS dictionary
    LOCK.acquire()
    ALL_USERS[username] = client_socket
    LOCK.release()

    # hello message
    client_socket.send(f"hello {username}\n".encode(ENCODE))
    return username



def user_view(client_socket: socket.socket):
    """get list of current users in group"""
    str_of_users = MAIN_GROUP.get_users() # get list of users as string delimited by '\n's
    client_socket.send(str_of_users.encode(ENCODE)) # set list to client



def display_messages(user_join_time: datetime.datetime, client_socket: socket.socket):
    """
    display all messages that are visible to the user
    first gets list of them from MAIN_GROUP
    then builds a string and sends that string to the client
    """
    # get list of messages incl. 2 before join time
    message_list: list[Message.Message] = MAIN_GROUP.get_visible_messages(user_join_time)

    # send each message as a list to be displayed by user
    # in format of “Message ID, Sender, Post Date, Subject.”
    message_str = "" # init message_str
    for message in message_list: # build message_str with list of visible messages
        message_str = message_str + message.id + ", " + message.username + ", " + message.datetime.strftime("%A, %d %B %Y, %I:%M:%S%p") + ", " + message.subject + "\n" 
        # e.g. datetime is "Wednesday, 26 November 2025, 3:27:00PM"
        # format str for that is "%A, %d %B %Y, %I:%M:%S%p"
    
    client_socket.send(message_str.encode(ENCODE)) # send message str
    return 



def send_notifications(client_socket: socket.socket, username: str):
    # grab list of notifications from Group
    notifications: list[str] = MAIN_GROUP.get_notifications(username)
    while notifications:
        curr_notif = notifications.pop(0)
        curr_notif = len(notifications) + " " + curr_notif # append len to beginning of notif
                                                           # to indicate how many remaining notifications there are
                                                           # so that client can time their .recv(1024)'s right
                                                           # so search for the first space in the string to separate
                                                           # the len and actual notif
        client_socket.send(curr_notif) # send notification
    return



def test_thread_main(client_socket: socket.socket, client_address):
    """
    testing to making sure the server and client can connect
    """
    try:
        print(f"Connection from {client_address}")
        # Receive the data in small chunks and retransmit it
        for i in range(5): # repeat 5 times, testing
            data = client_socket.recv(1024).decode(ENCODE) # receive data
            if data:
                print(f"Received: {data}")
                client_socket.sendall(data.encode(ENCODE))  # Echo back the received data
            print("while")
    finally:
        # Clean up the connection
        client_socket.close()



if __name__ == "__main__":
   main()