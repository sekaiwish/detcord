from flask import Flask, request, jsonify
import time, uuid, json, pickle, asyncio, multiprocessing, atexit, websockets
app = Flask(__name__)
app.config["DEBUG"] = True
memory, users, sessions = {}, {}, {}

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.creation_date = time.time()
        self.sessions = set()
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

# i.e.  const ws=new WebSocket("ws://127.0.0.1:8765");ws.onmessage=function(event){console.log(event.data)};
async def socket_connection(socket, path):
    print(" * WebSocket connection made")
    while True:
        ws_data = await socket.recv()
        try:
            ws_data = json.loads(ws_data)
            print(ws_data['key'])
        except:
            print("Invalid JSON structure")

@app.route('/api/login', methods=['POST'])
def login():
    if request.data:
        username = request.json['username']
        password = request.json['password']
        if username in users:
            if users[username].password == password:
                nonce = users[username].generate_nonce()
                users[username].sessions.add(nonce)
                sessions[nonce] = username
                return jsonify({"token":nonce})
    return jsonify(0)

@app.route('/api/<token>/logout')
def logout(token):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify(0)
    for session in users[user].sessions:
        del sessions[session]
    users[user].sessions.clear()
    return jsonify(1)

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

def main():
    server = websockets.serve(socket_connection, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

p = multiprocessing.Process(target=main)
p.start()
app.run()
