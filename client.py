import socket

"""
read messages from board
unicast sockets - one sender, one receiver
join a group, post messages that can only be seen by users in that gruop
extra cred if lang for client diff than server

do part 1 then part 2

part 1
all clients to one group
connect to server
enter user name, no authentication
server keeps track of all people that join/leave
when someone joins/leaves, everyone gets notified
when someone joins, can only see last 2 messages from people that were there already
when someone posts a message, all people can see it
Message Id, Sender, Post Date, Subject
can retrieve content of message by contacting server and providing message ID
also can leave the group

part 2
multiple groups
displays 5 at most
gives group id if want to join
can join multiple

example comamnds
part 1
%connect address port, connect to bulletin board
%join, connect to single message board
%post subject content
%users, list of users in same group
%leave, leave the group
%message ID, get content of message
%exit, disconnect and exit clients

part 2
%groups - all groups that can be joined
%groupjoin id/name
%grouppost id/name subject, content
%groupusers, id
%groupleave
%groupmessage groupID, DI

extra cred if GUI

Makefile if compilation has a lot of steps
and README, instructions for how to compile/run server/client, what packages needed, etc., usability instructions (if diff from above), major issues come across and how handled them
we probably dont need a makefile

submission
all names at top of README, client and server source cod, README, Makefile(i don't think we need it), in one directory
Project2-Lee-Pham-Slutsky, zipped and submitted on canvas






part 1 pseudo

server
main()
    create socket
    bind
    listen
    while loop
        accept socket
        create thread
        run thread with thread_main and socket as parameter
        thread.start
        no join
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
user_exit()
    (exit command)
    socket.close()
    for user in users
        user_notify() user that username left
user_request_message(line)
    (message command)
    get message_id from line
    socket.send(message_dict[id].encode())
user_post(line)
    (post command)
    create message id
    create datetime
    create Message object
    lock acquire
    message_dict[message_id] = Message - CRITICAL SECTION
    lock release
user_join()
    (join a group)
    lock acquire
    Group.group_users[username] = Socket - critical section
    lock release
user_leave()
    (leave a group)
    lock acquire
    Group.group_users.pop(username, None)
    lock release
user_notify(user, notification)
    (send a notification to be displayed to users)
    users[user].send(notification.encode())
user_send_message(id)
    (send a message from the bulletin to user)
    socket.send(messages[id].encode())
user_view_users()
    (view users command)
    string
    for user in gruop_user
        append string with user\nuser\n
    send string to user
...
data structures
    all_users: dict user->socket
    Message: class 
        id
        user
        datetime posted
        subject
        content
    Group: class
        list of group_users: dict user->socket
        message_dict: dict message_id->Message object


sending messages may be real time? how will that work with the shell...
    maybe they'll just have to be posted after each command
    or i can while input OR socket recv

client
shell loop
    while input or recv
        split line
        match case first word to proper function to execution
            connect
            exit
            message
            post
            join
            leave
            view_users
view message list command
    view the list of accessible messages 
connect command
    display all visible messages
exit command
    disconnect from server and end client program
message command
    request and display contents of message
post command
    post message to server
join group command
    connect to the single group
leave command
    leave the single group
view users command
    view list of users in current group
...
data structures
    list of known message_ids
    nuffer of notifications

    
protocol


how do sockets and multithreading work
sockets from reference TCPClient
import threading
threading.Thread(target=func, args=(args,))
t1.start()
t1.join()
threading.Lock() for a lock
lock.acquire() and lock.release()
how does .recv work? does it wait until it gets something 

how did proj 1 work?
server
    accept socket
    turn socket into HttpRequest
    create a thread from HttpRequest
    run the thread
        calls HttpRequest.run()
            calls processRequest()
                does processing stuff
                disconnect socket after request?
"""