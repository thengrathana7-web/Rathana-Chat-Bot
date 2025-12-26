import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

def get_db():
    # ប្រើផ្លូវទៅកាន់ database.db
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# បង្កើត Table (រក្សាទុក Table ចាស់ និងបន្ថែមការកំណត់ខ្លះៗ)
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

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    # ទាញយកសារចាស់ៗមកបង្ហាញ (Load Messages)
    db = get_db()
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        ORDER BY timestamp ASC
    ''').fetchall()
    
    return render_template('chat.html', user_name=session['user_name'], old_messages=messages)

# --- មុខងារថ្មី៖ ផ្ញើសារ និងរក្សាទុកក្នុង Database ---
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"status": "error"}), 403
    
    data = request.get_json()
    message_text = data.get('message')
    
    if message_text:
        db = get_db()
        db.execute('INSERT INTO messages (sender_id, message) VALUES (?, ?)',
                   (session['user_id'], message_text))
        db.commit()
        return jsonify({"status": "sent"}), 200
    return jsonify({"status": "empty"}), 400

# មុខងារស្វែងរកតាម Username (រក្សាទុកដដែល)
@app.route('/search', methods=['POST'])
def search_user():
    username = request.form.get('username')
    db = get_db()
    user = db.execute('SELECT username, name FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return jsonify({"status": "found", "name": user['name'], "username": user['username']})
    return jsonify({"status": "not_found"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
