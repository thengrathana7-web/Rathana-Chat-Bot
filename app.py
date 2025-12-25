import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# បង្កើត Database សម្រាប់សារ និង Profile
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, msg TEXT, time TEXT, type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (phone TEXT PRIMARY KEY, nickname TEXT, username TEXT, photo TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('message')
def handle_message(data):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # រក្សាសារ (type អាចជា 'text', 'voice', ឬ 'emoji')
    c.execute("INSERT INTO messages (name, msg, time, type) VALUES (?, ?, ?, ?)", 
              (data['name'], data['msg'], data['time'], data.get('type', 'text')))
    conn.commit()
    conn.close()
    emit('message', data, broadcast=True)

@socketio.on('load_history')
def load_history():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT name, msg, time, type FROM messages ORDER BY id ASC")
    history = [{'name': row[0], 'msg': row[1], 'time': row[2], 'type': row[3]} for row in c.fetchall()]
    conn.close()
    emit('history', history)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
