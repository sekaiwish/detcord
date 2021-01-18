from flask import Flask, request, jsonify, render_template
import time, uuid, json, pickle, asyncio, threading, atexit, websockets
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
                return jsonify({'token':nonce})
    return jsonify({'error':'invalid username/password'})

@app.route('/api/<token>/logout')
def logout(token):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify({'error':'invalid token'})
    for session in users[user].sessions:
        del sessions[session]
    users[user].sessions.clear()
    return jsonify({'success':1})

@app.route('/api/<token>/message/new', methods=['POST'])
def message_compose(token):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify({'error':'invalid token'})
    if request.data:
        message = Message(0, user, request.json['content'])
        memory[message.nonce] = message
        return jsonify({'nonce':message.nonce})
    return jsonify({'error':'invalid request'})

@app.route('/api/<token>/message/<nonce>/update', methods=['POST'])
def message_update(token, nonce):
    if token in sessions:
        user = sessions[token]
    else:
        return jsonify({'error':'invalid token'})
    if request.data:
        if nonce in memory:
            if memory[nonce].author == user:
                memory[nonce].content = request.json['content'][:2000]
                return jsonify({'success':1})
    return jsonify({'error':'invalid request'})

@app.route('/api/test')
def test():
    return jsonify([message.content for message in memory.values()])

@app.route('/')
def index():
    return render_template('index.html')

# i.e.  const ws=new WebSocket("ws://127.0.0.1:8765");ws.onmessage=function(event){console.log(event.data)};
async def socket_connection(socket, path):
    print(" * WebSocket connection made")
    while True:
        ws_data = await socket.recv()
        try:
            ws_data = json.loads(ws_data)
            if ws_data['token'] in sessions:
                user = sessions[ws_data['token']]
            else:
                await socket.send("{'error':'invalid token'}")
                continue
            if ws_data['intent'] == 'compose':
                message = Message(0, user, ws_data['content'])
                memory[message.nonce] = message
                await socket.send(jsonify({'nonce':message.nonce}))
            elif ws_data['intent'] == 'update':
                if ws_data['nonce'] in memory:
                    if memory[ws_data['nonce']] == user:
                        memory[ws_data['nonce']].content = ws_data['content'][:2000]
                        await socket.send("{'success':1}")
        except:
            raise
            print("Invalid JSON structure")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(socket_connection, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

p = threading.Thread(target=main, daemon=True)
p.start()
app.run()
