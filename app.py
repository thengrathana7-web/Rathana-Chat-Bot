import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# បង្កើត Database សម្រាប់រក្សាទុក Profile
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profiles 
                 (id INTEGER PRIMARY KEY, name TEXT, username TEXT, photo TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/save_profile', methods=['POST'])
def save_profile():
    data = request.json
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO profiles (id, name, username, photo) VALUES (1, ?, ?, ?)",
              (data['name'], data['username'], data['photo']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
