import os
import sqlite3
import random
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rathana_secret_123")
app.permanent_session_lifetime = timedelta(days=30)

# កំណត់ Folder សម្រាប់រក្សារូបភាព
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
        
        # កែសម្រួល Table messages បន្ថែម msg_type និង file_path
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            msg_type TEXT DEFAULT 'text', -- 'text', 'image', 'video', 'audio'
            file_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        )''')
    print("Database Initialized Successfully.")

init_db()

# --- Route ពិសេសសម្រាប់ Update Database ចាស់ (កុំឱ្យបាត់ទិន្នន័យ) ---
@app.route('/upgrade_database')
def upgrade_database():
    db = get_db()
    try:
        # បន្ថែម Column ថ្មីទៅក្នុង Table messages ដែលមានស្រាប់
        db.execute("ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT 'text'")
        db.execute("ALTER TABLE messages ADD COLUMN file_path TEXT")
        db.commit()
        return "Database បាន Upgrade ជោគជ័យ!"
    except Exception as e:
        return f"Database ប្រហែលជាមាន Column ទាំងនេះរួចហើយ៖ {e}"

# --- មុខងារ Notifications ---
@app.route('/check_notifications')
def check_notifications():
    if 'user_id' not in session: return jsonify({"unread_total": 0, "unread_by_user": {}})
    db = get_db()
    total = db.execute('SELECT COUNT(*) as count FROM messages WHERE receiver_id = ? AND is_read = 0', 
                       (session['user_id'],)).fetchone()
    by_user = db.execute('''
        SELECT sender_id, COUNT(*) as count 
        FROM messages 
        WHERE receiver_id = ? AND is_read = 0 
        GROUP BY sender_id
    ''', (session['user_id'],)).fetchall()
    unread_dict = {str(row['sender_id']): row['count'] for row in by_user}
    return jsonify({"unread_total": total['count'], "unread_by_user": unread_dict})

# --- Routes ដើម ---
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
    
    # ទាញយកសារទាំងអស់ (រួមទាំង msg_type និង file_path)
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (sender_id = ? AND receiver_id = ?) 
        OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    
    return render_template('chat.html', user_name=session['user_name'], old_messages=messages,
                           chat_with_name=chat_with_name, receiver_id=receiver_id)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.get_json()
    
    msg_type = data.get('msg_type', 'text') # default ជា text
    file_path = data.get('file_path', None)
    
    db = get_db()
    db.execute('''
        INSERT INTO messages (sender_id, receiver_id, message, msg_type, file_path, is_read) 
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (session['user_id'], data.get('receiver_id'), data.get('message'), msg_type, file_path))
    db.commit()
    return jsonify({"status": "sent"})

# --- Settings & Profile Update ---
@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', user=user)

@app.route('/update_info', methods=['POST'])
def update_info():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    name = request.form.get('name')
    gender = request.form.get('gender')
    db = get_db()
    db.execute('UPDATE users SET name = ?, gender = ? WHERE id = ?', (name, gender, session['user_id']))
    db.commit()
    session['user_name'] = name
    return redirect(url_for('settings'))

@app.route('/update_profile_pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    file = request.files.get('file') or request.files.get('profile_pic')
    if file and file.filename != '':
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
        filename = secure_filename(f"user_{session['user_id']}.{ext}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db = get_db()
        db.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, session['user_id']))
        db.commit()
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
