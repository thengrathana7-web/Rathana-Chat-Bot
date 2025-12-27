import os
import sqlite3
import random
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rathana_secret_123")
app.permanent_session_lifetime = timedelta(days=30)

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            gender TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id_number INTEGER UNIQUE, 
            profile_pic TEXT DEFAULT 'default.png'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database Initialized Successfully.")

init_db()

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('friend_list')) # ប្តូរទៅកាន់បញ្ជីមិត្តភក្តិ
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        email = request.form.get('email')
        password = request.form.get('password')
        user_id_number = random.randint(100000, 999999)
        username = str(user_id_number) 
        
        try:
            db = get_db()
            cursor = db.execute('''INSERT INTO users (username, name, gender, email, password, user_id_number) 
                                   VALUES (?, ?, ?, ?, ?, ?)''',
                                (username, name, gender, email, password, user_id_number))
            db.commit()
            
            session.permanent = True 
            session['user_id'] = cursor.lastrowid
            session['user_name'] = name
            session['id_num'] = user_id_number
            
            return redirect(url_for('friend_list')) # ទៅកាន់បញ្ជីមិត្តភក្តិក្រោយ Register
        except Exception as e:
            return f"កំហុស៖ {str(e)}"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = request.form.get('remember')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    
    if user:
        session.permanent = True if remember else False
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['id_num'] = user['user_id_number']
        return redirect(url_for('friend_list')) # ទៅកាន់បញ្ជីមិត្តភក្តិក្រោយ Login
    
    return "Email ឬ Password មិនត្រឹមត្រូវ!"

# --- មុខងារថ្មី៖ បញ្ជីមិត្តភក្តិ ---
@app.route('/friends')
def friend_list():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    db = get_db()
    # បង្ហាញអ្នកប្រើប្រាស់ផ្សេងៗដែលបានចុះឈ្មោះក្នុងប្រព័ន្ធ
    friends = db.execute('SELECT id, name, user_id_number, profile_pic FROM users WHERE id != ?', 
                         (session['user_id'],)).fetchall()
    
    return render_template('friend_list.html', friends=friends, user_name=session['user_name'])

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    receiver_id = request.args.get('uid')
    if not receiver_id:
        return redirect(url_for('friend_list'))

    db = get_db()
    user = db.execute('SELECT name FROM users WHERE id = ?', (receiver_id,)).fetchone()
    if not user:
        return redirect(url_for('friend_list'))

    chat_with_name = user['name']
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (sender_id = ? AND receiver_id = ?) 
        OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    
    return render_template('chat.html', 
                           user_name=session['user_name'], 
                           id_num=session.get('id_num'),
                           old_messages=messages,
                           chat_with_name=chat_with_name,
                           receiver_id=receiver_id)

@app.route('/search_friend', methods=['POST'])
def search_friend():
    if 'user_id' not in session: return jsonify({"status": "error"}), 401
    search_query = request.form.get('username', '').strip() 
    db = get_db()
    user = db.execute('SELECT id, name, user_id_number FROM users WHERE user_id_number = ? AND id != ?', 
                      (search_query, session['user_id'])).fetchone()
    if user:
        return jsonify({"status": "found", "id": user['id'], "name": user['name'], "id_num": user['user_id_number']})
    return jsonify({"status": "not_found"})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.get_json()
    db = get_db()
    db.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
               (session['user_id'], data.get('receiver_id'), data.get('message')))
    db.commit()
    return jsonify({"status": "sent"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
