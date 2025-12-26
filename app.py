from flask import Flask, request, jsonify
# ... កូដផ្សេងៗទៀត ...

@app.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'សូមបញ្ចូល Email'}), 400
            
        # កូដសម្រាប់បង្កើត និងផ្ញើ OTP ទៅ Email របស់អ្នកនៅទីនេះ
        # ...
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
