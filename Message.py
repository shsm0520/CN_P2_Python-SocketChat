"""
Message: class 
    id
    user
    datetime posted
    subject
    content
"""
import datetime

class Message:
    def __init__(self, username: str, datetime: datetime.datetime, subject: str, content: str):
        self.id: str = None # gets set in Group
        self.username = username
        self.datetime = datetime
        self.subject = subject
        self.content = content
        return

    def set_id(self, id):
        self.id = id
        return  