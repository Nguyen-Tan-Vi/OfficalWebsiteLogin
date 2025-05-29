from flask import Flask, request, redirect, render_template, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Thư mục upload ảnh
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploaded_avatars')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Đảm bảo thư mục tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = 'db.sqlite3'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    email TEXT,
                    fullname TEXT,
                    phone TEXT,
                    avatar_url TEXT,
                    bio TEXT
                )
            ''')

init_db()

def get_user_by_credentials(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return cur.fetchone()

def get_user_by_id(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        return cur.fetchone()

@app.route('/avatar/<filename>', endpoint='avatar_file')
def avatar_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        fullname = request.form['fullname']
        phone = request.form['phone']
        bio = request.form['bio']

        avatar_filename = None
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and allowed_file(file.filename):
                avatar_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT INTO users (username, password, email, fullname, phone, avatar_url, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username, password, email, fullname, phone, avatar_filename, bio))
            return redirect(url_for('login'))
        except:
            return "Tài khoản đã tồn tại!"

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_by_credentials(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('profile'))
        return "Sai tên đăng nhập hoặc mật khẩu!"
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        bio = request.form['bio']

        avatar_filename = user[6]  # giữ ảnh cũ nếu không upload mới
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and allowed_file(file.filename):
                avatar_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                UPDATE users SET fullname=?, email=?, phone=?, avatar_url=?, bio=? WHERE id=?
            ''', (fullname, email, phone, avatar_filename, bio, session['user_id']))
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
