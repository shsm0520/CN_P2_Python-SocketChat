# CN_P2_Python-SocketChat-

Homework  
Developed by: Seunghun Lee, Luke Pham, Connor Slutsky

# Requirements

- Python 3.7 or higher
- Standard library only (no external packages required)

# Steps for Execution:

1. Run server.py.
   ```bash
       python server.py
   ```
2. In a separate terminal, run client.py and %connect to address 127.0.0.1 and port 6789.

   ```bash
       python client.py

   ```

   ```
   %connect 127.0.0.1 6789
   ```

3. Enter a unique username when prompted

4. Use commands below to interact with the bulletin board

# List of Commands

%connect  
 &emsp;params: address, port  
 &emsp;function: connects to server at IP address [address] and port [port].

%groups  
 &emsp;no params  
 &emsp;function: display list of groups that user can connect to.

%groupjoin  
 &emsp;params: group_name  
 &emsp;function: joins inputted group.

%grouppost  
 &emsp;params: group_name, subject, content  
 &emsp;function: posts message of subject [subject] and content [content] to inputted group.  
 &emsp;NOTE: subject can only be one word.

%groupusers  
 &emsp;params: group_name  
 &emsp;function: displays list of users in inputted group .

%groupleave  
 &emsp;params: group_name  
 &emsp;function: leaves inputted group.

%groupmessage  
 &emsp;params: group_name, message_id  
 &emsp;function: accesses contents of message corresponding to [message_id].

%grouplist  
 &emsp;params: group_name  
 &emsp;function: lists group of visible messages in inputted group.

%join  
 &emsp;no params  
 &emsp;function: joins main group

%post  
 &emsp;params: subject, content  
 &emsp;function: posts message with subject [subject] and content [content] in main group.  
 &emsp;NOTE: have to be a member of main group to be able to do this.

%users  
 &emsp;no params  
 &emsp;function: sees list of users in main group  
 &emsp;NOTE: user has to be a member of main group to be able to use this command.

%leave  
 &emsp;no params  
 &emsp;function: leaves main group, if users is already a member of main group.

%message  
 &emsp;params: message_id  
 &emsp;function: accesses contents of message of inputted [message_id] in main group.  
 &emsp;NOTE: user has to be a member of main group to use this command.

%list  
 &emsp;no params  
 &emsp;function: lists visible messages to user.  
 &emsp;NOTE: user has to be a member of main group to be able to use this command.

%exit  
 &emsp;no params  
 &emsp;function: disconnects user from server.

# Major Issues Encountered and Solutions

## 1. Thread Synchronization

**Issue**: Multiple client threads accessing shared data structures (user lists, message dictionaries) simultaneously caused race conditions. For example, two clients joining a group at the same time could corrupt the group_users list.

**Solution**: Implemented a global `threading.Lock()` to protect all critical sections where shared data is read or modified. All operations on `ALL_USERS` and Group objects are wrapped in `with LOCK:` blocks, ensuring atomic operations and preventing data corruption.

## 2. Real-time Asynchronous Notifications

**Issue**: Clients need to receive notifications (user join/leave events, new message alerts) while they are blocked waiting for user input at the command prompt. Standard blocking I/O doesn't allow the server to "push" messages to clients mid-input.

**Solution**: Implemented a dual-thread architecture on the client side:

- Main thread: Handles user input (blocking on `input()`)
- Listener thread: Continuously listens for server messages (blocking on `recv()`)

On the server side, notifications are queued in each Group's notification dictionary (username -> list of pending notifications). A polling function checks and sends all queued notifications at the start of each command loop iteration before blocking on the next command.

## 3. Message Visibility Rules Implementation

**Issue**: Implementing the rule "show last 2 messages posted before join time + all messages posted after join time" required efficient datetime-based retrieval and sorting. Simple iteration through all messages would be inefficient.

**Solution**: Maintained two parallel dictionaries in the Group class:

- `message_dict`: Maps message_id -> Message for O(1) lookup by ID
- `datetime_message_dict`: Maps datetime -> Message, kept sorted for chronological operations

The `get_visible_messages()` method uses the sorted datetime keys to find the split point, then slices the appropriate range for efficient retrieval.
