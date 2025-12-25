import os
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rathana_secure_key_123' # សម្រាប់ការពារ Session
socketio = SocketIO(app, cors_allowed_origins="*")

# បង្កើត Database សម្រាប់ Profile និង សារឆាត (Messages)
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # តារាងរក្សាគណនីអ្នកប្រើ
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, name TEXT, photo TEXT)''')
    # តារាងរក្សាសារឆាតទាំងអស់ (ដើម្បីកុំឱ្យបាត់សារពេល Refresh)
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (room TEXT, sender TEXT, msg TEXT, photo TEXT, time TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('chat.html', username=session['username'], name=session['name'], photo=session['photo'])
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    name = username 
    photo = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, name, photo) VALUES (?, ?, ?, ?)",
                  (username, password, name, photo))
        conn.commit()
        conn.close()
        return "ចុះឈ្មោះជោគជ័យ! <a href='/'>ត្រឡប់ទៅ Login</a>"
    except:
        return "ឈ្មោះនេះមានគេប្រើរួចហើយ! <a href='/'>ព្យាយាមម្តងទៀត</a>"

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['username'] = user[0]
        session['name'] = user[2]
        session['photo'] = user[3]
        return redirect(url_for('index'))
    return "ឈ្មោះអ្នកប្រើ ឬលេខសម្ងាត់មិនត្រឹមត្រូវ! <a href='/'>ព្យាយាមម្តងទៀត</a>"

@app.route('/logout')
def logout():
    session.clear() # លុបទិន្នន័យ Login ចេញ
    return redirect(url_for('index'))

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    # ទាញយកប្រវត្តិឆាតចាស់ៗពី Database មកបង្ហាញឡើងវិញ
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT sender, msg, photo, time FROM messages WHERE room=? ORDER BY rowid ASC", (room,))
    history = c.fetchall()
    conn.close()
    for h in history:
        emit('message', {'name': h[0], 'msg': h[1], 'photo': h[2], 'time': h[3]})

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'private_room_1')
    # រក្សាទុកសារចូលក្នុង Database រាល់ពេលមានការផ្ញើ
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (room, sender, msg, photo, time) VALUES (?, ?, ?, ?, ?)",
              (room, data['name'], data['msg'], data['photo'], data['time']))
    conn.commit()
    conn.close()
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
