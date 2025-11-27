"""
Group: class
    list of group_users: list of usernames in group
    message_dict: dict message_id->Message object
"""

import Message
import datetime
import threading # Added import for clarity, though not used in Group itself

class Group:
    def __init__(self):
        # FIX: Changed initialization from {} to [] as it is used with .append/.remove
        self.group_users: list[str] = [] # list of usernames in group
        self.message_dict: dict[str, Message.Message] = {} # dict of messages of form "message_id: Message"
        self.datetime_message_dict: dict[datetime.datetime, Message.Message] = {} # i know it's not memory efficient but it works and it's easier to code...
                                                                                   # dict of messages of form "datetime_of_message: Message"
        self.curr_message_id = 0 # initialize message id, used to keep track of message id's
                                 # message_id's are strings as they're stored in the message_dict  
                                 # and in the message object, but kept as int in Group so it can be incremented easier
        self.notifications: dict[str, list[str]] = {} # dict to organize how to distribute notifications
                                                      # usernames are keys, and list of notifications for that user are values
                               # username:str -> list[notifaction: str]

    def add_user(self, username: str): # CRITICAL SECTION (I think? Yes, when modifying the list)
        if username not in self.group_users: # check if user in group before appending
            self.group_users.append(username)
            return True
        return False

    def remove_user(self, username: str):
        if username in self.group_users: # check first if user is in group
            self.group_users.remove(username) # remove username
            self.notifications.pop(username, None) # Remove any pending notifications for the leaving user
            return True
        return False

    def validate_user(self, username: str):
        """
        check if user in group
        """
        return username in self.group_users
    
    def get_users(self):
        """return string of all users to be printed if user wants to view list of users in group"""

        str_of_users = ""
        for user in self.group_users:
            # FIX: Added newline to the end for cleaner printing on the client side
            str_of_users = str_of_users + user + "\n"
        return str_of_users

    def add_message(self, message: Message.Message): # CRITICAL SECTION (i think? Yes, when modifying dicts/id)
        # set message id
        message_id_str = str(self.curr_message_id) # Store ID before increment
        message.set_id(message_id_str) 

        # add message to dict of messages
        self.message_dict[message_id_str] = message

        # increment curr_message_id
        self.curr_message_id = self.curr_message_id + 1 

        # add to datetime_message_dict and sort (for displaying visible messages to user in get_visible_messages())
        self.datetime_message_dict[message.datetime] = message
        
        # but retained for functional sorting guarantee.
        self.datetime_message_dict = dict(sorted(self.datetime_message_dict.items())) # sort self.datetime_m_d by keys (dates)
                                                                                      # i think its in ascending order earliest to latest
        return message_id_str # Return the new ID for posting confirmation

    def retrieve_message(self, message_id: str):
        """
        like when a user requests a message id to view its content
        """
        # FIX: Use .get() for safe retrieval, returning None if not found
        return self.message_dict.get(message_id)

    def validate_message_id(self, message_id: str):
        """
        check if message id exists in the dict
        """
        return message_id in self.message_dict
    
    def get_visible_messages(self, join_time: datetime.datetime) -> list[Message.Message]:
        datetime_message_keys: list[datetime.datetime] = list(self.datetime_message_dict.keys()) # list of datetimes
        datetime_message_values: list[Message.Message] = list(self.datetime_message_dict.values()) # parallel list of Message's

        index = len(datetime_message_keys) # set index to max length. FIX: Removed -1 as it causes issues.

        # if 0 messages, return empty list
        if not datetime_message_keys:
            return []
        
        # if <= 2 messages, return them no matter what
        if len(datetime_message_keys) <= 2:
            return datetime_message_values
        
        # if > 3 messages, return all that are after join_time and the two before join_time
        # Find the index of the first message posted *after* the join_time
        for i in range(len(datetime_message_keys)):
            if join_time < datetime_message_keys[i]: # the first time that join_time < keys, store the index, and break the loop
                                                     # keys should already be sorted in ascending order of datetime
                index = i
                break
        
        # at this point, index is now the index that is first after the join_time (or len if no message is newer)
        # so everything after index including index is sent to the user
        # and the two before the index are sent to the user
        
        # Start index is 2 before the 'newer than join_time' messages, or 0 if less than 2 exist before that point
        start_index = max(0, index - 2)
        return datetime_message_values[start_index:] # this should be a list of messages incl. 2 before join date
    
    def add_notification(self, username: str, notification: str): # CRITICAL SECTION
        # FIX: Corrected logic to ensure list is initialized and appended to
        # add notification for user to self.notifications
        if username not in self.notifications:
            self.notifications[username] = []
        self.notifications[username].append(notification)

    # FIX: Corrected signature - 'notification: str' was removed as it's not needed for getting.
    def get_notifications(self, username: str) -> list[str]: # CRITICAL SECTION
        if username in self.notifications: # first check if user is in notifications
            return self.notifications.pop(username) # returns list of notifications for that user and removes the entry
        else: # return empty list of no entry for that user
            return []