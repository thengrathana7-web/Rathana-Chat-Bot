import os
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rathana_secure_123'
socketio = SocketIO(app, cors_allowed_origins="*")

# កែសម្រួលការបង្កើត Database ដើម្បីថែម Column ថ្មី
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # បន្ថែម gender និង dob ក្នុង table users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, name TEXT, photo TEXT, gender TEXT, dob TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS messages (room TEXT, sender TEXT, msg TEXT, photo TEXT, time TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('chat.html', username=session['username'], name=session['name'], photo=session['photo'])
    return render_template('login.html')

# មុខងារ Register ថ្មីដែលទទួលទិន្នន័យពី Step 2
@app.route('/register', methods=['POST'])
def register():
    # ទទួលទិន្នន័យពី Form ថ្មីរបស់អ្នក
    username = request.form.get('identifier') # នេះជា Email ឬ លេខទូរស័ព្ទ (Step 1)
    name = request.form.get('fullname')      # ឈ្មោះពេញ (Step 2)
    gender = request.form.get('gender')      # ភេទ (Step 2)
    dob = request.form.get('dob')            # ថ្ងៃកំណើត (Step 2)
    
    # ចំណាំ៖ ដោយសារអ្នកមិនទាន់មានកន្លែងបញ្ចូល Password ថ្មី 
    # ខ្ញុំកំណត់ Password បណ្តោះអាសន្ន ឬអ្នកអាចថែម input password ក្នុង Form step 2 បាន
    password = "default_password" 
    photo = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        # បញ្ចូលទិន្នន័យទៅក្នុង Table users ដែលមាន ៦ columns
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                  (username, password, name, photo, gender, dob))
        conn.commit()
        conn.close()
        
        # បន្ទាប់ពី Register រួច ឱ្យវា Login ចូលតែម្តង
        session['username'], session['name'], session['photo'] = username, name, photo
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return "មានបញ្ហាក្នុងការចុះឈ្មោះ ឬឈ្មោះនេះមានគេប្រើរួចហើយ!"

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
        # user[0]=username, user[2]=name, user[3]=photo
        session['username'], session['name'], session['photo'] = user[0], user[2], user[3]
        return redirect(url_for('index'))
    return "ខុសលេខសម្ងាត់!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- រក្សាមុខងារ SocketIO ដូចដើម ---

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
