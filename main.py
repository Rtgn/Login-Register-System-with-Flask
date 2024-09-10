from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, hashlib
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'yoursecretkey'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username'
app.config['MYSQL_PASSWORD'] = 'yourmysqlpassword'
app.config['MYSQL_DB'] = 'yourdatabasename'

# Intialize MySQL
mysql = MySQL(app)

def create_tables():
    create_accounts_table = """
    CREATE TABLE IF NOT EXISTS accounts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        profile_image VARCHAR(255),
        about TEXT,
        email VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        follower_count INT DEFAULT 0
    );
    """
    
    create_all_contents_table = """
    CREATE TABLE IF NOT EXISTS All_Contents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        icerik_id INT NOT NULL,
        icerik_name VARCHAR(255) NOT NULL,
        main_image VARCHAR(255),
        username VARCHAR(50),
        likes_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        etiketler TEXT,
        FOREIGN KEY (user_id) REFERENCES accounts(id)
    );
    """
    
    cursor = mysql.connection.cursor()
    cursor.execute(create_accounts_table)
    cursor.execute(create_all_contents_table)
    mysql.connection.commit()
    cursor.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('profile'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Bu hesap zaten mevcut!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Geçersiz e-mail adresi!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Kullanıcı adı sadece harf ve rakam içerebilir!'
        elif not username or not password or not email:
            msg = 'Lütfen formu doldurun!'
        else:
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            default_about = "Merhaba! Ben de buradayım."
            default_profile_image = 'picture.jpg'
            
            cursor.execute('INSERT INTO accounts (username, password, email, profile_image, about) VALUES (%s, %s, %s, %s, %s)', 
                           (username, password, email, default_profile_image, default_about))
            mysql.connection.commit()
            msg = 'Başarılı bir şekilde kayıt oldunuz!'
    elif request.method == 'POST':
        msg = 'Lütfen formu doldurun!'
    return render_template('register.html', msg=msg)

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        
        cursor.execute('SELECT follower_count FROM accounts WHERE username = %s', (session['username'],))
        follower_count = cursor.fetchone()['follower_count']
        
        cursor.execute('SELECT SUM(likes_count) AS total_likes FROM All_Contents WHERE user_id = %s', (session['id'],))
        total_likes = cursor.fetchone()['total_likes']
        
        cursor.execute('SELECT COUNT(*) AS total_content FROM All_Contents WHERE user_id = %s', (session['id'],))
        total_content = cursor.fetchone()['total_content']
        
        return render_template('profile.html',follower_count=follower_count, account=account, total_likes=total_likes,total_content=total_content)
    else:
        return redirect(url_for('login'))

@app.route('/profil_duzenle')
def profil_duzenle():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        
        return render_template('profil_duzenle.html', account=account)
    else:
        return redirect(url_for('login'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'loggedin' in session:
        user_id = session['id']
        username = request.form.get('username')
        hakkinda = request.form.get('hakkinda')
        profile_image = request.files.get('profile_image')
        
        if profile_image and profile_image.filename:
            filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join('static/profil_pictures', filename))
        else:
            filename = None
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if filename:
            cursor.execute('UPDATE accounts SET username = %s, about = %s, profile_image = %s WHERE id = %s',
                           (username, hakkinda, filename, user_id))
        else:
            cursor.execute('UPDATE accounts SET username = %s, about = %s WHERE id = %s',
                           (username, hakkinda, user_id))
        
        mysql.connection.commit()

        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    create_tables()  # Ensure tables are created
    app.run(debug=True)
