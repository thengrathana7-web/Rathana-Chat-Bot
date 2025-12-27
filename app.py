import os
import sqlite3
import random
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)

# កំណត់ Secret Key ពី Environment Variable ដើម្បីសុវត្ថិភាពលើ Render
app.secret_key = os.environ.get("SESSION_SECRET", "rathana_secret_123")

# កំណត់ឱ្យ Session នៅជាប់បាន ៣០ ថ្ងៃ (Persistent Session)
app.permanent_session_lifetime = timedelta(days=30)

def get_db():
    # កំណត់ Path ឱ្យច្បាស់លាស់ដើម្បីកុំឱ្យបាត់ File Database ពេលនៅលើ Server
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # បង្កើតតារាង users ប្រសិនបើមិនទាន់មាន (ថែម column gender)
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
        # បង្កើតតារាង messages
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database Initialized Successfully.")

# បង្កើត Database ភ្លាមពេល Start Server
init_db()

# --- ROUTES ---

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        gender = request.form.get('gender')
        email = request.form.get('email')
        password = request.form.get('password')
        user_id_number = random.randint(100000, 999999)
        
        try:
            db = get_db()
            cursor = db.execute('''INSERT INTO users (username, name, gender, email, password, user_id_number) 
                                   VALUES (?, ?, ?, ?, ?, ?)''',
                                (username, name, gender, email, password, user_id_number))
            db.commit()
            
            # ចូលប្រព័ន្ធភ្លាមៗក្រោយ Register ជោគជ័យ
            session.permanent = True
            session['user_id'] = cursor.lastrowid
            session['user_name'] = name
            session['username'] = username
            session['id_num'] = user_id_number
            
            return redirect(url_for('chat'))
        except Exception as e:
            return f"កំហុសក្នុងការចុះឈ្មោះ៖ Username ឬ Email នេះមានគេប្រើរួចហើយ! (Error: {str(e)})"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    
    if user:
        session.permanent = True # កំណត់ឱ្យជាប់បានយូរ ៣០ ថ្ងៃ
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['username'] = user['username']
        session['id_num'] = user['user_id_number']
        return redirect(url_for('chat'))
    
    return "Email ឬ Password មិនត្រឹមត្រូវ!"

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    receiver_id = request.args.get('uid')
    db = get_db()
    messages = []
    chat_with_name = "Global Chat"
    
    if receiver_id:
        user = db.execute('SELECT name FROM users WHERE id = ?', (receiver_id,)).fetchone()
        if user:
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
                           chat_with_name=chat_with_name)

@app.route('/search_friend', methods=['POST'])
def search_friend():
    if 'user_id' not in session: 
        return jsonify({"status": "error"}), 401
    
    search_query = request.form.get('username', '').strip() 
    db = get_db()
    user = db.execute('SELECT id, name, user_id_number FROM users WHERE user_id_number = ? AND id != ?', 
                      (search_query, session['user_id'])).fetchone()
    
    if user:
        return jsonify({
            "status": "found", 
            "id": user['id'], 
            "name": user['name'], 
            "id_num": user['user_id_number']
        })
    return jsonify({"status": "not_found"})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"status": "error"}), 403
    
    data = request.get_json()
    message_text = data.get('message')
    receiver_id = data.get('receiver_id')
    
    if message_text:
        db = get_db()
        db.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
                   (session['user_id'], receiver_id, message_text))
        db.commit()
        return jsonify({"status": "sent"}), 200
    return jsonify({"status": "empty"}), 400

@app.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    if 'user_id' not in session:
        return jsonify([]), 401
    
    db = get_db()
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    
    return jsonify([dict(row) for row in messages])

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    return render_template('settings.html', 
                           user_name=session['user_name'], 
                           username=session['username'],
                           id_num=session.get('id_num'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    # កំណត់ Port ឱ្យត្រូវជាមួយ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
