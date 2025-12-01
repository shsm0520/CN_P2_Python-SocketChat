"""
Message.py: Class Definition for a Single Bulletin Board Post

This class serves as a robust data container for all information associated with a
message. It is designed to be immutable once created, with the ID being set externally
by the Group class upon insertion.
"""
import datetime

class Message:
    """Represents a single message posted to any group."""
    
    def __init__(self, username: str, datetime: datetime.datetime, subject: str, content: str):
        # Unique identifier (string) for the message within its Group. Set by Group
        self.id: str = None 
        
        # The username of the message's sender
        self.username = username
        
        # The exact timestamp of when the message was posted. Critical for visibility sorting
        self.datetime = datetime
        
        # The subject line or title of the post
        self.subject = subject
        
        # The main body content of the post
        self.content = content
        return

    def set_id(self, id: str):
        """Sets the unique ID assigned by the Group instance upon insertion."""
        self.id = id
        return