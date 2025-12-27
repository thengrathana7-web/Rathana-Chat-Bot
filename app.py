<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ចុះឈ្មោះគណនីថ្មី</title>
    <style>
        :root {
            --primary-color: #0084ff;
            --bg-color: #f0f2f5;
        }
        body {
            font-family: 'Khmer OS Battambang', sans-serif;
            background-color: var(--bg-color);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .register-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        h2 { color: var(--primary-color); margin-bottom: 1.5rem; }
        .input-group { margin-bottom: 1rem; text-align: left; }
        label { display: block; margin-bottom: 5px; color: #555; }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { opacity: 0.9; }
        .footer-link { margin-top: 15px; font-size: 14px; }
        .footer-link a { color: var(--primary-color); text-decoration: none; }
    </style>
</head>
<body>

<div class="register-container">
    <h2>បង្កើតគណនីថ្មី</h2>
    <form action="/register" method="POST">
        <div class="input-group">
            <label>ឈ្មោះពេញ</label>
            <input type="text" name="name" placeholder="ឧទាហរណ៍៖ រតនា" required>
        </div>
        <div class="input-group">
            <label>ឈ្មោះអ្នកប្រើ (Username)</label>
            <input type="text" name="username" placeholder="សម្រាប់ Login" required>
        </div>
        <div class="input-group">
            <label>អ៊ីមែល (Email)</label>
            <input type="email" name="email" placeholder="ត្រូវតែជា Email ថ្មី" required>
        </div>
        <div class="input-group">
            <label>លេខសម្ងាត់</label>
            <input type="password" name="password" placeholder="បញ្ចូលលេខសម្ងាត់" required>
        </div>
        <button type="submit">ចុះឈ្មោះឥឡូវនេះ</button>
    </form>
    <div class="footer-link">
        មានគណនីរួចហើយមែនទេ? <a href="/">ត្រឡប់ទៅ Login</a>
    </div>
</div>

</body>
</html>
