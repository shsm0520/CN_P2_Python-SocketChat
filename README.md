# CN_P2_Python-SocketChat-
Homework  
Developed by: Seunghun Lee, Luke Pham, Connor Slutsky  

# Steps for Execution:
1) Run server.py.
2) In a separate terminal, run client.py and %connect to address 127.0.0.1 and port 6789.

# List of Commands
%connect  
    &emsp;params:     address, port  
    &emsp;function:   connects to server at IP address [address] and port [port].  
      
%groups  
    &emsp;no params  
    &emsp;function:   display list of groups that user can connect to.  
      
%groupjoin  
    &emsp;params:     group_name  
    &emsp;function:   joins inputted group.  
  
%grouppost  
    &emsp;params:     group_name, subject, content  
    &emsp;function:   posts message of subject [subject] and content [content] to inputted group.  
                &emsp;NOTE: subject can only be one word.  
                  
%groupusers  
    &emsp;params:     group_name  
    &emsp;function:   displays list of users in inputted group . 
      
%groupleave  
    &emsp;params:     group_name  
    &emsp;function:   leaves inputted group.  
      
%groupmessage  
    &emsp;params:     group_name, message_id  
    &emsp;function:   accesses contents of message corresponding to [message_id].  
      
%grouplist  
    &emsp;params:     group_name  
    &emsp;function:   lists group of visible messages in inputted group.  
      
%join  
    &emsp;no params  
    &emsp;function:   joins main group   
      
%post  
    &emsp;params:     subject, content  
    &emsp;function:   posts message with subject [subject] and content [content] in main group.  
                &emsp;NOTE: have to be a member of main group to be able to do this.  
                  
%users  
    &emsp;no params  
    &emsp;function:   sees list of users in main group  
                &emsp;NOTE: user has to be a member of main group to be able to use this command.  
                  
%leave  
    &emsp;no params  
    &emsp;function:   leaves main group, if users is already a member of main group.  
      
%message  
    &emsp;params:     message_id  
    &emsp;function:   accesses contents of message of inputted [message_id] in main group.  
                &emsp;NOTE: user has to be a member of main group to use this command.  
                  
%list  
    &emsp;no params  
    &emsp;function:   lists visible messages to user.  
                &emsp;NOTE: user has to be a member of main group to be able to use this command. 
                  
%exit  
    &emsp;no params  
    &emsp;function:   disconnects user from server.  
