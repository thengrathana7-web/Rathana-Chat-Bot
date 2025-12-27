import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, session

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
        # បង្កើត Table users (បន្ថែម Column user_id_number និង gender)
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id_number INTEGER UNIQUE, 
            gender TEXT DEFAULT 'Male'
        )''')
        
        # បន្ថែម Table messages (សំខាន់ខ្លាំង៖ បើគ្មាន table នេះ កម្មវិធីនឹង Error ពេលផ្ញើសារ)
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database Initialized Successfully.")

# ហៅមុខងារបង្កើត Database
init_db()

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
        except Exception as e:
            print(f"Registration Error: {e}")
            return "<script>alert('មានបញ្ហាបច្ចេកទេស កំឡុងពេលចុះឈ្មោះ!'); window.location='/register';</script>"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    
    if user:
        session.clear() # សម្អាត session ចាស់មុនពេល login ថ្មី
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['id_num'] = user['user_id_number'] # បន្ថែម id_num ក្នុង session
        return redirect(url_for('chat'))
    
    return "<script>alert('អ៊ីមែល ឬលេខសម្ងាត់មិនត្រឹមត្រូវ!'); window.location='/';</script>"

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    return render_template('chat.html', user_name=session['user_name'], id_num=session.get('id_num'))

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
        session['user_name'] = new_name # Update ឈ្មោះក្នុង session ភ្លាមៗ
        return redirect(url_for('settings'))
    
    return "<script>alert('ឈ្មោះមិនអាចទទេបានទេ!'); window.location='/settings';</script>"

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('welcome'))
    
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
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
