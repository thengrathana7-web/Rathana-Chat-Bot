# --- មុខងារចុះឈ្មោះ (Register) - កែសម្រួលថ្មីឱ្យចុះឈ្មោះបានច្រើនគណនី ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    # ប្រសិនបើមាន Session ចាស់ (កំពុង Login) ត្រូវឱ្យគាត់ Logout សិនទើបអាចចុះឈ្មោះថ្មីបាន
    # ឬអ្នកអាចដកលក្ខខណ្ឌនេះចេញ ប្រសិនបើចង់ឱ្យចុះឈ្មោះទាំងកំពុង Login
    if 'user_id' in session:
        session.clear() 

    if request.method == 'POST':
        try:
            # ចាប់យកទិន្នន័យពី Form
            name = request.form.get('name')
            username = request.form.get('username').strip()
            email = request.form.get('email').strip()
            password = request.form.get('password')
            gender = request.form.get('gender')
            
            # បង្កើតលេខ ID សម្គាល់ខ្លួន (៦ខ្ទង់)
            user_id_number = random.randint(100000, 999999)
            
            db = get_db()
            
            # ១. ពិនិត្យមើលថា Email ឬ Username នេះមានគេប្រើរួចហើយឬនៅ
            existing_user = db.execute(
                'SELECT id FROM users WHERE username = ? OR email = ?', 
                (username, email)
            ).fetchone()
            
            if existing_user:
                return "<script>alert('ឈ្មោះអ្នកប្រើ ឬ អ៊ីមែលនេះមានគេប្រើរួចហើយ! សូមប្រើព័ត៌មានផ្សេង។'); window.location='/register';</script>"

            # ២. បញ្ចូលទិន្នន័យទៅក្នុង Database (INSERT)
            db.execute('''
                INSERT INTO users (username, name, gender, email, password, user_id_number) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, name, gender, email, password, user_id_number))
            db.commit()
            
            # ៣. ចាប់យកទិន្នន័យដែលទើបបញ្ចូលដើម្បីបង្កើត Session (Login ឱ្យភ្លាមៗ)
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            
            return redirect(url_for('friend_list'))
            
        except sqlite3.IntegrityError:
            return "<script>alert('កំហុស៖ ទិន្នន័យស្ទួន! សូមសាកល្បងម្ដងទៀត។'); window.location='/register';</script>"
        except Exception as e:
            return f"មានបញ្ហាបច្ចេកទេស៖ {str(e)}"
            
    return render_template('register.html')
