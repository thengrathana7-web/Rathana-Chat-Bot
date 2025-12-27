import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'rathana_secret_key'

# មុខងារភ្ជាប់ទៅកាន់ Database
def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# បង្កើត Table ប្រសិនបើមិនទាន់មាន
def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id_number INTEGER UNIQUE, 
            gender TEXT DEFAULT 'Male'
        )''')
    print("Database ready.")

init_db()

@app.route('/')
def welcome():
    if 'user_id' in session: return redirect(url_for('chat'))
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        gender = request.form.get('gender', 'Male')
        user_id_num = random.randint(100000, 999999)
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, name, email, password, gender, user_id_number) VALUES (?, ?, ?, ?, ?, ?)',
                       (username, name, email, password, gender, user_id_num))
            db.commit()
            return redirect(url_for('welcome'))
        except:
            return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ អ៊ីមែលមានរួចហើយ!'); window.location='/register';</script>"
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
        return redirect(url_for('chat'))
    return "<script>alert('ព័ត៌មានមិនត្រឹមត្រូវ!'); window.location='/';</script>"

@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', user=user)

# មុខងាររក្សាទុកការផ្លាស់ប្តូរ (Update Settings)
@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session: return redirect(url_for('welcome'))
    new_name = request.form.get('name')
    new_gender = request.form.get('gender')
    
    db = get_db()
    db.execute('UPDATE users SET name = ?, gender = ? WHERE id = ?', (new_name, new_gender, session['user_id']))
    db.commit()
    session['user_name'] = new_name 
    return redirect(url_for('settings'))

# មុខងារលុបគណនី (Delete Account)
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session: return redirect(url_for('welcome'))
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
