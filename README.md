# CN_P2_Python-SocketChat-
Homework

# Steps for Execution:
1) Run server.py.
2) In a separate terminal, run client.py and %connect to address 127.0.0.1 and port 6789.

# List of Commands
%connect
    params:     address, port
    function:   connects to server at IP address [address] and port [port].
%groups
    no params
    function:   display list of groups that user can connect to.
%groupjoin
    params:     group_name
    function:   joins inputted group.
%grouppost
    params:     group_name, subject, content
    function:   posts message of subject [subject] and content [content] to inputted group.
                NOTE: subject can only be one word.
%groupusers
    params:     group_name
    function:   displays list of users in inputted group .
%groupleave
    params:     group_name
    function:   leaves inputted group.
%groupmessage
    params:     group_name, message_id
    function:   accesses contents of message corresponding to [message_id].
%grouplist
    params:     group_name
    function:   lists group of visible messages in inputted group.
%join
    no params
    function:   joins main group 
%post
    params:     subject, content
    function:   posts message with subject [subject] and content [content] in main group.
                NOTE: have to be a member of main group to be able to do this.
%users
    no params
    function:   sees list of users in main group
                NOTE: user has to be a member of main group to be able to use this command.
%leave
    no params
    function:   leaves main group, if users is already a member of main group.
%message
    params:     message_id
    function:   accesses contents of message of inputted [message_id] in main group.
                NOTE: user has to be a member of main group to use this command.
%list
    no params
    function:   lists visible messages to user.
                NOTE: user has to be a member of main group to be able to use this command.
%exit
    no params
    function:   disconnects user from server.
