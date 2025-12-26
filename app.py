from flask import Flask, request, jsonify, render_template
import random

app = Flask(__name__)

# ទុកលេខកូដ OTP បណ្តោះអាសន្ន (ក្នុងជីវិតជាក់ស្តែងត្រូវប្រើ Database)
otp_storage = {}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'សូមបញ្ចូល Email'}), 400
            
        # បង្កើតលេខកូដ OTP ៦ ខ្ទង់
        otp = str(random.randint(100000, 999999))
        otp_storage[email] = otp
        
        # បង្ហាញក្នុង Logs លើ Render ដើម្បីឱ្យអ្នកមើលឃើញ (ព្រោះមិនទាន់បានភ្ជាប់ SMTP Email)
        print(f"--- OTP សម្រាប់ {email} គឺ: {otp} ---")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    # កូដសម្រាប់ទទួលទិន្នន័យចុះឈ្មោះក្រោយពេលផ្ទៀងផ្ទាត់ OTP
    return "ចុះឈ្មោះជោគជ័យ!"

if __name__ == '__main__':
    app.run(debug=True)

