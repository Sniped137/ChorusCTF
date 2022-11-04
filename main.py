from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_table import Table, Col
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = 'test'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'MFswB4WK6^&U!Rza&5bfNtQ!nc&'
app.config['MYSQL_DB'] = 'ctfdb'

mysql = MySQL(app)

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('login'))
        else:
            msg = 'Incorrect username/password'
            
    if "loggedin" in session: 
        return redirect(url_for('challenges'))
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
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        score = 0
        challengescomplete = 0
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username can only contain characters and numbers'
        elif not username or not password or not email:
            msg = 'Please fill out the form'
        else:
            cursor.execute(f"INSERT INTO accounts VALUES (NULL, '{username}', '{password}', '{email}', {score}, {challengescomplete})")
            cursor.execute("INSERT INTO completed VALUES (DEFAULT, 0, 0, 0, 0, 0)")
            mysql.connection.commit()
            msg = 'You have successfully registered'
    elif request.method == 'POST':
        msg = 'Please fill out the form'

    if "loggedin" in session: 
        return redirect(url_for('challenges'))
    return render_template('register.html', msg=msg)

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route('/hackerboard', methods=['GET', 'POST'])
def hackerboard():
    headings = ['ID', 'Username', 'Score', 'Challenges Complete']
    data = []
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM accounts ORDER BY score desc")
    results = cursor.fetchall()
    for row in results:
        data.append((row['id'], row['username'], row['score'], row['challenges_complete']))
    return render_template('hackerboard.html', headings=headings, data=data)

@app.route('/challenges', methods=['GET', 'POST'])
def challenges():
    if "loggedin" not in session: 
        return redirect(url_for('index'))
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        formcontents = []
        for i in range(1,6):
            flag = request.form.get(f'{i}')
            formcontents.append(flag)

        for value in formcontents:
            if value != None:
                challengeid = formcontents.index(value) + 1

        filteredcontents = list(filter(None, formcontents))

        cursor.execute(f"SELECT * FROM completed WHERE userid = '{session['id']}'")
        userchallengelist = cursor.fetchall()
        readonly = []

        for key,value in userchallengelist[0].items():
            if key != "userid" and value == 1:
                cid = int(key[-1])
                readonly.append(cid)

        solvenums = []
        cursor.execute(f"SELECT * FROM challenges")
        solvers = cursor.fetchall()
        slength = len(solvers)

        for i in range(0, slength):
            for key, value in solvers[i].items():
                if key == 'solves':
                    solvenums.append(value)

        if request.method == 'POST':    
            cursor.execute(f"SELECT * FROM challenges WHERE id='{challengeid}' ")
            results = cursor.fetchall()
            answer = results[0]['flag']
            points = results[0]['points']
            
            flagstr = "" ; guessstr = "" 
            guess = (guessstr.join(filteredcontents)) ; realflag = (flagstr.join(answer)) ; 

            if guess == realflag:
                cursor.execute(f" SELECT score FROM accounts WHERE id='{session['id']}' ")
                sqlresult = cursor.fetchall() 
                cursor.execute(f"UPDATE accounts SET score = score + {points}, challenges_complete = challenges_complete + 1 WHERE id={session['id']}")
                cursor.execute(f"UPDATE completed SET challengeid{challengeid}=1 WHERE userid={session['id']}")
                cursor.execute(f"UPDATE challenges SET solves = solves + 1 WHERE id={challengeid}")
                mysql.connection.commit()

                return redirect(url_for('challenges'))

        return render_template('challenges.html', msg=readonly, msg2=solvenums)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
