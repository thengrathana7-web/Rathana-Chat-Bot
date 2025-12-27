import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

def get_db():
    # កែសម្រួលឱ្យទាញយក Path ឱ្យបានត្រឹមត្រូវសម្រាប់ Deploy
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # បង្កើត Table Users
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id_number INTEGER UNIQUE, 
            profile_pic TEXT DEFAULT 'default.png'
        )''')
        # បង្កើត Table Messages
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

# --- កែសម្រួលមុខងារចុះឈ្មោះ (Register) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    # គន្លឹះសំខាន់៖ ជម្រះ Session ចាស់ចោលភ្លាមៗ នៅពេលចូលមកទំព័រចុះឈ្មោះ
    # ដើម្បីឱ្យទូរសព្ទដដែលអាចបង្កើតគណនីថ្មីបានដោយគ្មានបញ្ហា
    if 'user_id' in session:
        session.clear()

    if request.method == 'POST':
        username = request.form['username'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        # បង្កើតលេខ ID ៦ខ្ទង់ដោយចៃដន្យ
        user_id_number = random.randint(100000, 999999)
        
        db = get_db()
        
        # ឆែកមើលជាមុនថា Email ឬ Username នេះមានគេប្រើរួចហើយឬនៅ
        existing_user = db.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username)).fetchone()
        
        if existing_user:
            return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ អ៊ីមែលនេះមានគេប្រើរួចហើយ! សូមប្រើព័ត៌មានថ្មី។'); window.location='/register';</script>"
            
        try:
            db.execute('INSERT INTO users (username, name, email, password, user_id_number) VALUES (?, ?, ?, ?, ?)',
                       (username, name, email, password, user_id_number))
            db.commit()
            
            # ចុះឈ្មោះហើយ ឱ្យគាត់ Login ចូលដោយស្វ័យប្រវត្តិជាមួយគណនីថ្មីនោះតែម្តង
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['username'] = user['username']
            session['id_num'] = user['user_id_number']
            
            return redirect(url_for('chat'))
        except Exception as e:
            return f"មានបញ្ហាក្នុងការចុះឈ្មោះ៖ {str(e)}"
            
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email'].strip()
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['username'] = user['username']
        session['id_num'] = user['user_id_number']
        return redirect(url_for('chat'))
    return "<script>alert('Email ឬ Password មិនត្រឹមត្រូវ!'); window.location='/';</script>"

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
    
    user_id = session['user_id']
    db = get_db()
    
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (user_id, receiver_id, receiver_id, user_id)).fetchall()
    
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
