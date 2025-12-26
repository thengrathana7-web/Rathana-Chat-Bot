import os
import sqlite3
import random
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rathana_secure_123'

# --- កំណត់ការផ្ញើ Email (ត្រូវប្តូរព័ត៌មានខាងក្រោមដើម្បីឱ្យដើរ) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com' # ដាក់ Email របស់អ្នក
app.config['MAIL_PASSWORD'] = 'your-app-password'   # ដាក់ App Password ១៦ ខ្ង់ពី Google
mail = Mail(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# បង្កើត Database និង Table
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # Table users ដែលមាន ៦ columns: username, password, name, photo, gender, dob
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

# --- មុខងារថ្មី៖ ផ្ញើ OTP ទៅកាន់ Email ---
@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    otp = str(random.randint(100000, 999999))
    session['otp'] = otp  # រក្សាទុកក្នុង session បណ្តោះអាសន្ន
    
    try:
        msg = Message('Verify Code - Rathana Chat', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"លេខកូដផ្ទៀងផ្ទាត់គណនីរបស់អ្នកគឺ: {otp}"
        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- មុខងារ Register ថ្មី៖ ផ្ទៀងផ្ទាត់ OTP និងរក្សាទុកទិន្នន័យ ---
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('identifier') # នេះជា Email (Step 1)
    user_otp = request.form.get('verify_code') # លេខកូដដែលអ្នកប្រើបញ្ចូល
    name = request.form.get('fullname')
    gender = request.form.get('gender')
    dob = request.form.get('dob')
    
    # ផ្ទៀងផ្ទាត់លេខកូដ OTP
    if not session.get('otp') or user_otp != session.get('otp'):
        return "លេខកូដ OTP មិនត្រឹមត្រូវ ឬហួសសុពលភាព!"

    password = "default_password" # អ្នកអាចបន្ថែម input password ក្នុង HTML បាន
    photo = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                  (username, password, name, photo, gender, dob))
        conn.commit()
        conn.close()
        
        # សម្អាត OTP ចោល រួច Login ចូលតែម្តង
        session.pop('otp', None)
        session['username'], session['name'], session['photo'] = username, name, photo
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return "ឈ្មោះនេះមានគេប្រើរួចហើយ ឬមានបញ្ហាបច្ចេកទេស!"

# --- មុខងារ Login ចាស់ ---
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
    return "ខុសលេខសម្ងាត់ ឬឈ្មោះអ្នកប្រើ!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- រក្សាមុខងារ SocketIO ដូចដើម ---
@socketio.on('join')
def on_join(data):
    room = data.get('room', 'main')
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
