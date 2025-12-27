import os
import sqlite3
import random
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

# កំណត់ឱ្យ Session នៅជាប់បាន ៣០ ថ្ងៃ
app.permanent_session_lifetime = timedelta(days=30)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # បន្ថែម column 'gender' ក្នុងតារាង users
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
    print("Database initialized.")

init_db()

@app.route('/')
def welcome():
    # ប្រសិនបើមាន Session ស្រាប់ ឱ្យចូលទៅ Chat តែម្ដង
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        gender = request.form.get('gender') # ទទួលទិន្នន័យភេទ
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_id_number = random.randint(100000, 999999)
        
        try:
            db = get_db()
            cursor = db.execute('''INSERT INTO users (username, name, gender, email, password, user_id_number) 
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (username, name, gender, email, password, user_id_number))
            db.commit()
            
            # ចុះឈ្មោះហើយ ឱ្យចូលប្រព័ន្ធ (Login) ស្វ័យប្រវត្តិ
            session.permanent = True # ធ្វើឱ្យ Session នេះទៅជា Permanent (ជាប់បានយូរ)
            session['user_id'] = cursor.lastrowid
            session['user_name'] = name
            session['username'] = username
            session['id_num'] = user_id_number
            
            return redirect(url_for('chat'))
        except Exception as e:
            print(f"Error: {e}")
            return "Username ឬ Email នេះមានគេប្រើរួចហើយ!"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    # ពិនិត្យមើលថាតើអ្នកប្រើចុច "ចងចាំខ្ញុំ" ឬអត់ (បើចង់បន្ថែមប៊ូតុងនេះ)
    remember = request.form.get('remember') 

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    
    if user:
        session.permanent = True # កំណត់ឱ្យជាប់បានយូរ ៣០ ថ្ងៃតាម setting ខាងលើ
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['username'] = user['username']
        session['id_num'] = user['user_id_number']
        return redirect(url_for('chat'))
    
    return "Email ឬ Password មិនត្រឹមត្រូវ!"

# --- ផ្នែកផ្សេងៗទៀត (Chat, Search, Send Message) រក្សាទុកដដែល ---
# ... (កូដចាស់របស់អ្នក) ...

@app.route('/logout')
def logout():
    session.clear() # លុប Session ចោលទាំងអស់ ទើបត្រូវ Login ម្ដងទៀត
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # បិទ debug ពេលដាក់លើ Render
