import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
# កំណត់ Secret Key ឱ្យមានសុវត្ថិភាព
app.secret_key = os.environ.get('SECRET_KEY', 'rathana_chat_bot_2025_secure')

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # បង្កើតតារាងអ្នកប្រើប្រាស់ (Users)
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id_number INTEGER UNIQUE, 
            gender TEXT DEFAULT 'Male'
        )''')
        
        # បង្កើតតារាងសារ (Messages) - កែសម្រួលតាមតម្រូវការ chat.html
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            msg_type TEXT DEFAULT 'text',
            file_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database រៀបចំរួចរាល់!")

# ហៅមុខងារបង្កើត Database
init_db()

# --- ROUTES សម្រាប់ទំព័រទូទៅ ---

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        gender = request.form.get('gender', 'Male')
        user_id_num = random.randint(100000, 999999)
        
        if not username or not email or not password:
            return "<script>alert('សូមបំពេញព័ត៌មានឱ្យបានគ្រប់គ្រាន់!'); window.location='/register';</script>"
        
        db = get_db()
        try:
            db.execute('''INSERT INTO users (username, name, email, password, gender, user_id_number) 
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (username, name, email, password, gender, user_id_num))
            db.commit()
            return redirect(url_for('welcome'))
        except sqlite3.IntegrityError:
            return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ អ៊ីមែលនេះមានគេប្រើរួចហើយ!'); window.location='/register';</script>"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    if user:
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['id_num'] = user['user_id_number']
        return redirect(url_for('chat'))
    return "<script>alert('អ៊ីមែល ឬលេខសម្ងាត់មិនត្រឹមត្រូវ!'); window.location='/';</script>"

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    return render_template('chat.html', user_name=session['user_name'], id_num=session.get('id_num'))

# --- API សម្រាប់មុខងារ CHAT (សំខាន់សម្រាប់ឱ្យ chat.html ដើរ) ---

@app.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    if 'user_id' not in session: return jsonify([])
    db = get_db()
    messages = db.execute('''
        SELECT * FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC''', 
        (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    return jsonify([dict(msg) for msg in messages])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session: return jsonify({'status': 'unauthorized'})
    data = request.json
    db = get_db()
    db.execute('''INSERT INTO messages (sender_id, receiver_id, message, msg_type) 
                  VALUES (?, ?, ?, ?)''', 
               (session['user_id'], data['receiver_id'], data['message'], data.get('msg_type', 'text')))
    db.commit()
    return jsonify({'status': 'sent'})

@app.route('/search_user/<int:user_id_num>')
def search_user(user_id_num):
    db = get_db()
    user = db.execute('SELECT id, name FROM users WHERE user_id_number = ?', (user_id_num,)).fetchone()
    if user:
        return jsonify({'id': user['id'], 'name': user['name']})
    return jsonify({'error': 'រកមិនឃើញ'})

# --- មុខងារ SETTINGS ---

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', user=user)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    new_name = request.form.get('name', '').strip()
    new_gender = request.form.get('gender', 'Male')
    if new_name:
        db = get_db()
        db.execute('UPDATE users SET name = ?, gender = ? WHERE id = ?', (new_name, new_gender, session['user_id']))
        db.commit()
        session['user_name'] = new_name
        return redirect(url_for('settings'))
    return "<script>alert('ឈ្មោះមិនអាចទទេបានទេ!'); window.location='/settings';</script>"

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
    db.execute('DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?', (session['user_id'], session['user_id']))
    db.commit()
    session.clear()
    return redirect(url_for('welcome'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
