import time, uuid

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.creation_date = time.time()
        users[username] = self
    def generate_nonce(self):
        return uuid.uuid4().hex

class Message:
    def __init__(self, type: int, author, content):
        self.type = type
        self.author = author
        self.content = content
        self.timestamp = time.time()
        self.nonce = self.generate_nonce()
    def generate_nonce(self):
        return uuid.uuid4().hex
