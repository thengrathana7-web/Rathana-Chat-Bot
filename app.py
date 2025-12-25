import os
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rathana_secure_123'
socketio = SocketIO(app, cors_allowed_origins="*")

def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, photo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (room TEXT, sender TEXT, msg TEXT, photo TEXT, time TEXT)')
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
    photo = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, password, username, photo))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except:
        return "ឈ្មោះនេះមានគេប្រើរួចហើយ!"

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
        session['username'], session['name'], session['photo'] = user[0], user[2], user[3]
        return redirect(url_for('index'))
    return "ខុសលេខសម្ងាត់!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT sender, msg, photo, time FROM messages WHERE room=? ORDER BY rowid ASC", (room,))
    for h in c.fetchall():
        emit('message', {'name': h[0], 'msg': h[1], 'photo': h[2], 'time': h[3]})
    conn.close()

@socketio.on('message')
def handle_message(data):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", 
              (data.get('room', 'main'), data['name'], data['msg'], data['photo'], data['time']))
    conn.commit()
    conn.close()
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
