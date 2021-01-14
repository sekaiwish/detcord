from flask import Flask, request, jsonify
import time, uuid
app = Flask(__name__)
app.config["DEBUG"] = True
memory = {}

class Message:
    def __init__(self, type: int, author, content):
        self.type = type
        self.author = author
        self.content = content
        self.timestamp = time.time()
        self.nonce = self.assign_nonce()
    def assign_nonce(self):
        return uuid.uuid4().hex

def get_username(token):
    # TODO: authorisation tokens
    return token

@app.route('/api/<token>/message/new', methods=['POST'])
def message_compose(token):
    user = get_username(token)
    if request.data:
        message = Message(0, user, request.data)
        memory[message.nonce] = message
        return jsonify(message.nonce)
    return jsonify(0)

@app.route('/api/<token>/message/<nonce>/update', methods=['POST'])
def message_update(token, nonce):
    user = get_username(token)
    if request.data:
        if nonce in memory:
            if memory[nonce].author == user:
                memory[nonce].content = request.data
                return jsonify(1)
    return jsonify(0)

@app.route('/api/test')
def test():
    return jsonify([message.content.decode("utf-8") for message in memory.values()])

@app.route('/')
def index():
    return "<h1>Detcord</h1>"

app.run()
