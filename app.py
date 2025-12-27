import os
import sqlite3
import random  # សម្រាប់ generate user_id_number
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rathana_secret_123")
app.permanent_session_lifetime = timedelta(days=30)

# កំណត់ Folder សម្រាប់រក្សារូបភាព និងឯកសារ media
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            msg_type TEXT DEFAULT 'text',
            file_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        )''')
    print("Database Initialized Successfully.")

init_db()

# --- មុខងារចុះឈ្មោះ (Register) - បច្ចុប្បន្នភាពថ្មីតាមសំណូមពរ ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('friend_list'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username').strip() # បន្ថែម .strip() ដើម្បីលុប Space
        email = request.form.get('email').strip()       # បន្ថែម .strip() ដើម្បីលុប Space
        password = request.form.get('password')
        gender = request.form.get('gender')
        
        # បង្កើត ID 6 ខ្ទង់ដោយចៃដន្យ
        user_id_number = random.randint(100000, 999999)
        
        db = get_db()
        try:
            db.execute('''
                INSERT INTO users (username, name, gender, email, password, user_id_number) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, name, gender, email, password, user_id_number))
            db.commit()
            
            # ចុះឈ្មោះរួច ឱ្យ Login ចូលតែម្តង
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            
            return redirect(url_for('friend_list'))
            
        except sqlite3.IntegrityError:
            # បង្ហាញសារជាភាសាខ្មែរឱ្យចំបញ្ហា និង Alert ប្រាប់អ្នកប្រើ
            return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ អ៊ីមែលនេះមានគេប្រើរួចហើយ! សូមប្តូរថ្មី។'); window.location='/register';</script>"
        except Exception as e:
            return f"មានបញ្ហាក្នុងការចុះឈ្មោះ៖ {str(e)}"
            
    return render_template('register.html')

# --- មុខងារ Login ---
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                     (username, password)).fetchone()
    
    if user:
        session.permanent = True
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return redirect(url_for('friend_list'))
    else:
        return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ លេខសម្ងាត់មិនត្រឹមត្រូវ!'); window.location='/';</script>"

# --- Routes ដើមសម្រាប់ Chat និង Friends ---
@app.route('/')
def welcome():
    if 'user_id' in session: return redirect(url_for('friend_list'))
    return render_template('welcome.html')

@app.route('/friends')
def friend_list():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    db = get_db()
    friends = db.execute('SELECT id, name, user_id_number, profile_pic FROM users WHERE id != ?', 
                         (session['user_id'],)).fetchall()
    return render_template('friend_list.html', friends=friends, user_name=session['user_name'])

@app.route('/chat')
def chat():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    receiver_id = request.args.get('uid')
    if not receiver_id: return redirect(url_for('friend_list'))
    
    db = get_db()
    db.execute('UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?', 
               (receiver_id, session['user_id']))
    db.commit()
    
    user = db.execute('SELECT name FROM users WHERE id = ?', (receiver_id,)).fetchone()
    chat_with_name = user['name'] if user else "Unknown"
    
    return render_template('chat.html', user_name=session['user_name'], 
                           chat_with_name=chat_with_name, receiver_id=receiver_id)

@app.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    if 'user_id' not in session: return jsonify([])
    db = get_db()
    messages = db.execute('''
        SELECT * FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) 
        OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    return jsonify([dict(msg) for msg in messages])

# --- មុខងារផ្ញើសារ និង Media ---
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.get_json()
    db = get_db()
    db.execute('''
        INSERT INTO messages (sender_id, receiver_id, message, msg_type, is_read) 
        VALUES (?, ?, ?, ?, 0)
    ''', (session['user_id'], data.get('receiver_id'), data.get('message'), data.get('msg_type', 'text')))
    db.commit()
    return jsonify({"status": "sent"})

@app.route('/send_media', methods=['POST'])
def send_media():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    receiver_id = request.form.get('receiver_id')
    msg_type = request.form.get('type')
    file = request.files.get('file')
    if file:
        filename = secure_filename(f"{msg_type}_{random.randint(1000,9999)}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db = get_db()
        db.execute('''
            INSERT INTO messages (sender_id, receiver_id, msg_type, file_path, is_read) 
            VALUES (?, ?, ?, ?, 0)
        ''', (session['user_id'], receiver_id, msg_type, filename))
        db.commit()
        return jsonify({"status": "sent", "file": filename})
    return jsonify({"status": "error"}), 400

@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
