"""
Group: class
    list of group_users: dict user->socket
    message_dict: dict message_id->Message object
"""

import Message
import datetime

class Group:
    def __init__(self):
        self.group_users: list[str] = {} # list of usernames in group
        self.message_dict: dict[str, Message.Message] = {} # dict of messages of form "message_id: Message"
        self.datetime_message_dict = dict[datetime.datetime, Message.Message] = {} # i know it's not memory efficient but it works and it's easier to code...
                                                                                   # dict of messages of form "datetime_of_message: Message"
        self.curr_message_id = 0 # initialize message id, used to keep track of message id's
                                 # message_id's are strings as they're stored in the message_dict  
                                 # and in the message object, but kept as int in Group so it can be incremented easier
        self.notifications: dict[str, list[str]] = {} # dict to organize how to distribute notifications
                                                      # usernames are keys, and list of notifications for that user are values
                               # username:str -> list[notifaction: str]

    def add_user(self, username: str): # CRITICAL SECTION (I think?)
        if username not in self.group_users: # check if user in group before appending
            self.group_users.append(username)
            return True
        return False

    def remove_user(self, username: str):
        if username in self.group_users: # check first if user is in group
            self.group_users.remove(username) # remove username
            return True
        return False

    def validate_user(self, username: str):
        """
        check if user in group
        """
        if username in self.group_users:
            return True
        return False
    
    def get_users(self):
        """return string of all users to be printed if user wants to view list of users in group"""

        str_of_users = ""
        for user in self.group_users:
            str_of_users = str_of_users + user + "\n"
        return str_of_users

    def add_message(self, message: Message.Message): # CRITICAL SECTION (i think?)
        # set message id
        message.set_id(str(self.curr_message_id)) 

        # add message to dict of messages
        self.message_dict[str(self.curr_message_id)] = message

        # increment curr_message_id
        self.curr_message_id = self.curr_message_id + 1 

        # add to datetime_message_dict and sort (for displaying visible messages to user in get_visible_messages())
        self.datetime_message_dict[message.datetime] = message
        self.datetime_message_dict = dict(sorted(self.datetime_message_dict.items())) # sort self.datetime_m_d by keys (dates)
                                                                                      # i think its in ascending order earliest to latest
    def retrieve_message(self, message_id: str):
        """
        like when a user requests a message id to view its content
        is already validated that message_id exists before this function is called
        """

        return self.message_dict[message_id]

    def validate_message_id(self, message_id: str):
        """
        check if message id exists in the dict
        """
        if message_id in self.message_dict:
            return True
        return False
    
    def get_visible_messages(self, join_time: datetime.datetime) -> list[Message.Message]:
        datetime_message_keys: list[datetime.datetime] = list(self.datetime_message_dict.keys()) # list of datetimes
        datetime_message_values: list[Message.Message] = list(self.datetime_message_dict.values()) # parallel list of Message's

        index = len(datetime_message_keys)-1 # set index to max length (-1 because indexing starts at 0)

        # if 0 messages, return empty list
        if len(datetime_message_keys) == 0:
            return []
        # if <= 2 messages, return them no matter what
        elif len(datetime_message_keys) <= 2:
            return datetime_message_values
        else:
            # if > 3 messages, return all that are after join_time and the two before join_time
            for i in range(len(datetime_message_keys)):
                if join_time < datetime_message_keys[i]: # the first time that join_time < keys, store the index, and break the loop
                                                         # keys should already be sorted in ascending order of datetime
                    index = i
                    break
            # at this point, index is now the index that is first after the join_time
            # so everything after index including index is sent to the user
            # and the two before the index are sent to the user
            if index <= 2: # if there are 2 messages or less before index, just return all values
                return datetime_message_values
            else: # else, splice the list of Messages and send that
                return datetime_message_values[index-2:] # this should be a list of messages incl. 2 before join date
    
    def add_notification(self, username: str, notification: str): # CRITICAL SECTION
        # add notification for user to self.notifications
        if username in self.notifications:
            self.notifications[username] = [notification]
        else:
            self.notifications[username].append(notification)

    def get_notifications(self, username: str, notification: str): # CRITICAL SECTION
        if username in self.notifications: # first check if user is in notifications
            return self.notifications.pop(username) # returns list of notifications for that user
        else: # return empty list of no entry for that user
            return [] 
        
    
                



        
    
    

