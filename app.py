<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ចុះឈ្មោះគណនីថ្មី - Rathana Chat Bot</title>
    <style>
        :root {
            --bg-dark: #0e1621;
            --box-bg: #17212b;
            --input-bg: #242f3d;
            --primary-blue: #2481cc;
            --text-white: #ffffff;
            --text-gray: #b1b1b1;
        }

        body {
            font-family: 'Segoe UI', 'Khmer OS Battambang', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-white);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }

        .register-container {
            background: var(--box-bg);
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }

        h2 { color: var(--text-white); margin-bottom: 0.5rem; font-size: 24px; }
        p.subtitle { color: var(--text-gray); font-size: 14px; margin-bottom: 1.5rem; }

        .input-group { margin-bottom: 1.2rem; text-align: left; }

        label { display: block; margin-bottom: 8px; color: var(--text-gray); font-size: 14px; }

        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid transparent;
            border-radius: 10px;
            background: var(--input-bg);
            color: var(--text-white);
            box-sizing: border-box;
            font-size: 15px;
            outline: none;
            transition: 0.3s;
            font-family: inherit;
        }

        input:focus, select:focus {
            border-color: var(--primary-blue);
        }

        /* បន្ថែមរចនាបថសម្រាប់ Select Option */
        select option {
            background: var(--box-bg);
            color: var(--text-white);
        }

        button {
            width: 100%;
            padding: 14px;
            background-color: var(--primary-blue);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            transition: 0.3s;
        }

        button:hover {
            background-color: #1d6fa5;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(36, 129, 204, 0.3);
        }

        .footer-link { 
            margin-top: 20px; 
            font-size: 14px; 
            color: var(--text-gray); 
        }

        .footer-link a { 
            color: var(--primary-blue); 
            text-decoration: none; 
            font-weight: bold;
        }

        .footer-link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<div class="register-container">
    <h2>បង្កើតគណនីថ្មី</h2>
    <p class="subtitle">សូមបំពេញព័ត៌មានខាងក្រោមដើម្បីចាប់ផ្តើម</p>

    <form action="/register" method="POST">
        <div class="input-group">
            <label>ឈ្មោះពេញ</label>
            <input type="text" name="name" placeholder="ឧទាហរណ៍៖ រតនា" required>
        </div>

        <div class="input-group">
            <label>ឈ្មោះអ្នកប្រើ (Username)</label>
            <input type="text" name="username" placeholder="សម្រាប់ប្រើពេល Login" required>
        </div>

        <div class="input-group">
            <label>ភេទ</label>
            <select name="gender" required>
                <option value="" disabled selected>ជ្រើសរើសភេទ</option>
                <option value="Male">ប្រុស (Male)</option>
                <option value="Female">ស្រី (Female)</option>
                <option value="Other">ផ្សេងៗ</option>
            </select>
        </div>

        <div class="input-group">
            <label>អ៊ីមែល (Email)</label>
            <input type="email" name="email" placeholder="បញ្ចូល Email ថ្មីរបស់អ្នក" required>
        </div>

        <div class="input-group">
            <label>លេខសម្ងាត់</label>
            <input type="password" name="password" placeholder="យ៉ាងតិច ៦ ខ្ទង់" required>
        </div>

        <button type="submit">ចុះឈ្មោះឥឡូវនេះ</button>
    </form>

    <div class="footer-link">
        មានគណនីរួចហើយមែនទេ? <a href="/">ត្រឡប់ទៅ Login</a>
    </div>
</div>

</body>
</html>
