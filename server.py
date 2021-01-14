from flask import Flask, request, jsonify
from classes import User, Message
import atexit, pickle
app = Flask(__name__)
app.config["DEBUG"] = True
memory, users, sessions = {}, {}, {}

try:
    with open('detcord.dat', 'rb') as fp:
        (memory, users, sessions) = pickle.load(fp)
        print(" * Loaded detcord data")
except IOError:
    pass

def save():
    data = (memory, users, sessions)
    with open('detcord.dat', 'wb') as fp:
        pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)
        print(" * Saved detcord data")
atexit.register(save)

@app.route('/api/login', methods=['POST'])
def login():
    print(users)
    if request.data:
        username = request.json['username']
        password = request.json['password']
        if username in users:
            if users[username].password == password:
                nonce = users[username].generate_nonce()
                sessions[nonce] = username
                return jsonify(nonce)
    return jsonify(0)

@app.route('/api/<token>/message/new', methods=['POST'])
def message_compose(token):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify(0)
    if request.data:
        message = Message(0, user, request.json['content'])
        memory[message.nonce] = message
        return jsonify(message.nonce)
    return jsonify(0)


@app.route('/api/<token>/message/<nonce>/update', methods=['POST'])
def message_update(token, nonce):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify(0)
    if request.data:
        if nonce in memory:
            if memory[nonce].author == user:
                memory[nonce].content = request.json['content'][:2000]
                return jsonify(1)
    return jsonify(0)

@app.route('/api/test')
def test():
    return jsonify([message.content for message in memory.values()])

@app.route('/')
def index():
    return "<h1>Detcord</h1>"

app.run()
