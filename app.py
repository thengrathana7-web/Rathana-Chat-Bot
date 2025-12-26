import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic TEXT DEFAULT 'default.png'
        )''')
        # បន្ថែម receiver_id ក្នុង table messages បើមិនទាន់មាន
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER, 
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database initialized.")

init_db()

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        try:
            db = get_db()
            db.execute('INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)',
                       (username, name, email, password))
            db.commit()
            return redirect(url_for('welcome'))
        except:
            return "Username ឬ Email មានគេប្រើរួចហើយ!"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['username'] = user['username']
        return redirect(url_for('chat'))
    return "Email ឬ Password មិនត្រឹមត្រូវ!"

# --- កែប្រែ Route Chat ឱ្យអាចមើលសារជាមួយមិត្តភក្តិជាក់លាក់ ---
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    receiver_id = request.args.get('uid') # យក ID មិត្តភក្តិពី URL
    db = get_db()
    
    messages = []
    receiver_name = "Global Chat"
    
    if receiver_id:
        # ទាញយកឈ្មោះមិត្តភក្តិ
        user = db.execute('SELECT name FROM users WHERE id = ?', (receiver_id,)).fetchone()
        if user:
            receiver_name = user['name']
            # ទាញយកសាររវាងអ្នកទាំងពីរ (Private Message)
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
                           old_messages=messages, 
                           chat_with_name=receiver_name,
                           receiver_id=receiver_id)

# --- កែប្រែការផ្ញើសារឱ្យមាន Receiver ---
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"status": "error"}), 403
    
    data = request.get_json()
    message_text = data.get('message')
    receiver_id = data.get('receiver_id') # ទទួល ID អ្នកទទួល
    
    if message_text:
        db = get_db()
        db.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
                   (session['user_id'], receiver_id, message_text))
        db.commit()
        return jsonify({"status": "sent"}), 200
    return jsonify({"status": "empty"}), 400

@app.route('/search_friend', methods=['POST'])
def search_friend():
    if 'user_id' not in session:
        return jsonify({"status": "error"}), 401
    
    query = request.form.get('username', '').replace('@', '').strip()
    db = get_db()
    user = db.execute('SELECT id, username, name FROM users WHERE username = ? AND id != ?', 
                      (query, session['user_id'])).fetchone()
    
    if user:
        return jsonify({
            "status": "found", 
            "id": user['id'], 
            "name": user['name'], 
            "username": user['username']
        })
    return jsonify({"status": "not_found"})

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    return render_template('settings.html', user_name=session['user_name'], username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
