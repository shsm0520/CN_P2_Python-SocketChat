"""
Group.py: Class Definition for a Single Group/Message Board

This class encapsulates all state and core logic for one independent bulletin board group.
It is designed to be reusable; the server instantiates multiple Group objects (e.g., 'main', 'general').
"""

import Message
import datetime
import threading

class Group:
    """Manages the users, messages, and notifications for one group."""
    
    def __init__(self):
        # List of usernames currently joined to this group
        self.group_users: list[str] = [] 
        
        # Primary message storage: Maps message ID (str) -> Message object
        self.message_dict: dict[str, Message.Message] = {} 
        
        # Chronological message storage: Maps datetime -> Message object. Used for efficient
        # retrieval based on time (required by message visibility logic)
        self.datetime_message_dict: dict[datetime.datetime, Message.Message] = {}                                                                                
        
        # Counter to generate the next sequential unique message ID for *this group only*
        self.curr_message_id = 0 
        
        # Notification queue: Maps username (key) -> list of pending notification strings (value)
        # This is where notifications wait until the user's thread polls for them
        self.notifications: dict[str, list[str]] = {} 

    def add_user(self, username: str): 
        """Adds a user to the group if they are not already a member."""
        if username not in self.group_users: 
            self.group_users.append(username)
            return True
        return False

    def remove_user(self, username: str):
        """Removes a user from the group and purges their notification queue."""
        if username in self.group_users: 
            self.group_users.remove(username) 
            self.notifications.pop(username, None) # Remove any pending notifications for the leaving user
            return True
        return False

    def validate_user(self, username: str):
        """Checks membership status."""
        return username in self.group_users
    
    def get_users(self):
        """Returns a string representation of all users for the %users command."""
        return "\n".join(self.group_users)

    def add_message(self, message: Message.Message): 
        """Assigns ID, stores message, and updates history structures."""
        
        message_id_str = str(self.curr_message_id) 
        message.set_id(message_id_str) 

        self.message_dict[message_id_str] = message
        self.curr_message_id = self.curr_message_id + 1 

        # Add to time-based dict and ensure it remains sorted by datetime
        self.datetime_message_dict[message.datetime] = message
        self.datetime_message_dict = dict(sorted(self.datetime_message_dict.items())) 
                                                                                      
        return message_id_str 

    def retrieve_message(self, message_id: str):
        """Retrieves a message object by ID."""
        return self.message_dict.get(message_id)

    def validate_message_id(self, message_id: str):
        """Checks message existence."""
        return message_id in self.message_dict
    
    def get_visible_messages(self, join_time: datetime.datetime) -> list[Message.Message]:
        """
        Implements the message visibility rule:
        Returns the 2 messages posted immediately BEFORE the join_time, plus ALL messages posted AFTER the join_time.
        """
        datetime_message_keys: list[datetime.datetime] = list(self.datetime_message_dict.keys()) 
        datetime_message_values: list[Message.Message] = list(self.datetime_message_dict.values()) 

        if not datetime_message_keys:
            return []
        
        # Simple case: if 2 or fewer messages exist, show all
        if len(datetime_message_keys) <= 2:
            return datetime_message_values
        
        # Find the index of the first message posted *strictly after* the join_time
        index = len(datetime_message_keys) 
        for i, dt in enumerate(datetime_message_keys):
            if join_time < dt: 
                index = i
                break
        
        # Calculate the starting index: 2 positions before the first 'new' message
        # max(0, ...) ensures the index does not go below 0
        start_index = max(0, index - 2)
        
        # Return the slice containing the 2 prior messages and all subsequent messages
        return datetime_message_values[start_index:] 
    
    # Notification logic
    def add_notification(self, username: str, notification: str): 
        """Queues a notification for a specific user."""
        # Initialize list if user has no notification list, then append
        if username not in self.notifications:
            self.notifications[username] = []
        self.notifications[username].append(notification)

    def get_notifications(self, username: str) -> list[str]: 
        """
        Retrieves all pending notifications for a user and CLEARS the queue.
        Uses pop(key, default) for atomic retrieval and removal (polling).
        """
        return self.notifications.pop(username, [])