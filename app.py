import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

def get_db():
    # ប្រើប្រាស់ផ្លូវ (Path) ត្រឹមត្រូវសម្រាប់ Database
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# បង្កើត Table សម្រាប់ User និង Message
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
    # ប្រសិនបើមាន Login រួចហើយ ឱ្យទៅទំព័រ Chat តែម្តង
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
    return render_template('chat.html', user_name=session['user_name'])

# មុខងារថ្មី៖ ស្វែងរកអ្នកប្រើប្រាស់តាម Username
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
    # កំណត់ឱ្យដំណើរការលើគ្រប់ IP (សម្រាប់ Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
