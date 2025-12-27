import os
import sqlite3
import random
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rathana_secret_123")
app.permanent_session_lifetime = timedelta(days=30)

# ការកំណត់ទីតាំងសម្រាប់រក្សារូបភាព Profile
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# បង្កើត Folder បើមិនទាន់មាន
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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database Initialized Successfully.")

init_db()

# --- Routes ដើម ---

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('friend_list'))
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
            
            return redirect(url_for('friend_list'))
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
        return redirect(url_for('friend_list'))
    
    return "Email ឬ Password មិនត្រឹមត្រូវ!"

@app.route('/friends')
def friend_list():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    db = get_db()
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

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', user=user, user_name=user['name'], id_num=user['user_id_number'], user_email=user['email'], user_gender=user['gender'], user_profile_pic=user['profile_pic'])

# --- មុខងារថ្មីដែលអ្នកចង់បន្ថែម ---

@app.route('/update_info', methods=['POST'])
def update_info():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    
    new_name = request.form.get('name')
    new_gender = request.form.get('gender')
    
    db = get_db()
    db.execute('UPDATE users SET name = ?, gender = ? WHERE id = ?', 
               (new_name, new_gender, session['user_id']))
    db.commit()
    
    session['user_name'] = new_name # Update session ភ្លាមៗ
    return redirect(url_for('settings'))

@app.route('/update_profile_pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    if 'profile_pic' not in request.files: return redirect(url_for('settings'))
    
    file = request.files['profile_pic']
    if file.filename == '': return redirect(url_for('settings'))
    
    if file:
        # បង្កើតឈ្មោះ file ថ្មីដោយប្រើ user_id ដើម្បីកុំឱ្យជាន់គ្នា (ឧទាហរណ៍៖ profile_1.png)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"profile_{session['user_id']}.{ext}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        db = get_db()
        db.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, session['user_id']))
        db.commit()
        
    return redirect(url_for('settings'))

@app.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    if 'user_id' not in session: return jsonify([])
    db = get_db()
    messages = db.execute('''
        SELECT sender_id, message, timestamp 
        FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) 
        OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    return jsonify([dict(msg) for msg in messages])

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
