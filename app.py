import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import mysql.connector
from flask_httpauth import HTTPBasicAuth
import pandas as pd
import http.client


app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
socketio = SocketIO(app)

mydb = mysql.connector.connect(
  host="eu-cdbr-west-03.cleardb.net",
  user="bd5b45754d9419",
  password="cfd3aeb8",
  database="heroku_f7fc2d46da75047"
)

cursor = mydb.cursor()

class Reminder:
    def __init__(self):
        self.tasks = []

    def add_task(self, task, time, priority=1):
        self.tasks.append({'task': task, 'time': time, 'priority': priority, 'days_not_done': 0,'reminder': False})

    def mark_task_done(self, task_index):
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]['days_not_done'] = 0
        else:
            print("Invalid task index!")

    def increase_priority_if_not_done(self):
        for task in self.tasks:
            if task['days_not_done'] >= 3:
                task['priority'] += 1

    def run_reminder(self):
        now = datetime.datetime.now().strftime("%H:%M")
        for task in self.tasks:
            if now == task['time']:
                task['reminder'] = True
            else:
                task['reminder'] = False
        self.increase_priority_if_not_done()
        
    def mark_task_done(self, task_index):
        # Mark the task at the specified index as done
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]['reminder'] = True
    
    def add_task_to_db(self, user_id, task_desc, task_time, task_priority=1):
        # SQL statement to insert a new task
        sql = "INSERT INTO tbl_tasks (task_usr_id, task_desc, task_reminder_time, task_priority) VALUES (%s, %s, %s, %s)"
        values = (user_id, task_desc, task_time, task_priority)
        # Execute the SQL statement
        cursor.execute(sql, values)
        mydb.commit()
    
    def mark_task_done_in_db(self, task_id):
        # SQL statement to mark a task as done
        sql = "UPDATE tbl_tasks SET task_done = 1 WHERE task_id = %s"
        values = (task_id,)
        cursor.execute(sql, values)
        mydb.commit()

reminder_app = Reminder()

@app.route('/')
def index():
    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        reminder_app.add_task(task, time, priority)

    reminder_app.run_reminder()
    return render_template('index.html', tasks=reminder_app.tasks)

@app.route("/login",methods = ['GET',"POST"])
def login():
     return render_template('/login.html')
 
  
@app.route("/logout",methods = ['GET',"POST"])
def logout():    
    session.clear()
    session['is_logged_in']=False
    return redirect(url_for('home'))

def check_sql_injection(text):
    keywords = ['select', 'insert', 'update', 'delete', 'drop', 'alter', 'create', 'rename', 'truncate']
    for keyword in keywords:
        if keyword in text.lower():
            return True
    return False

def check_user_existence(username):
    mydb.reconnect()
    cursor = mydb.cursor()
    query = "SELECT * FROM tbl_users WHERE userName = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    if user is not None:
        return True
    return False

# insert user data into the database
def insert_user_data(data):
    mydb.reconnect()
    cursor = mydb.cursor()
    query = "INSERT INTO tbl_users (userPass, userFirstName, userLastName, userName, userDefaultAddr, userPhone, userAccess,userEIRcode) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"
    cursor.execute(query, (data['userPass'], data['userFirstName'], data['userLastName'], data['userName'], data['userDefaultAddr'], data['userPhone'], 2,data['userEirCode']))
    mydb.commit()

# Flask route to handle the signup form
@app.route('/signup', methods=['GET', 'POST'])
def signup():    
   return render_template('signup.html')

@app.route("/addUser", methods=['GET','POST'])
def addUser():
    if request.method == 'POST':
        # get form data
        input = request.get_json()
        userPass = input['userPass']
        userFirstName = input['userFirstName']
        userLastName = input['userLastName']
        userName = input['userName']
        userDefaultAddr = input['userDefaultAddr']
        userPhone = input['userPhone']
        userEirCode=input['eircode']
        
        userPass=str(hashlib.md5(userPass.encode("utf-8")).hexdigest())
        # check for SQL injection
        if check_sql_injection(userPass) or check_sql_injection(userFirstName) or check_sql_injection(userLastName) or check_sql_injection(userName) or check_sql_injection(userDefaultAddr) or check_sql_injection(userPhone):
            return jsonify({'Result':'Error: SQL injection detected!'})
        
        # check for user existence
        if check_user_existence(userName):

            return jsonify({'Result': 'User already exists!'})
        
        # insert user data into the database
        data = {
            'userPass': userPass,
            'userFirstName': userFirstName,
            'userLastName': userLastName,
            'userName': userName,
            'userDefaultAddr': userDefaultAddr,
            'userPhone': userPhone,
            'userEirCode':userEirCode
        }
        insert_user_data(data)
        mydb.reconnect()
        cursor = mydb.cursor()
        query = "SELECT * FROM tbl_users WHERE userName = %s"
        cursor.execute(query, (userName,))
        data2 = cursor.fetchall()
        session['is_logged_in'] = True
        session['userPass'] = userPass
        session['userFirstName'] = userFirstName
        session['userLastName'] = userLastName
        session['userName'] = userName
        session['userID'] = data2[0][0]
        session['userDefaultAddr'] = userDefaultAddr
        session['userPhone'] = userPhone
        session['userEirCode'] = userEirCode
        return jsonify({'Result': 'User added successfully!'})
 
@app.route("/verifyUser", methods = ['GET',"POST"])
def verifyUser():
    if request.method == 'POST':
        data = request.get_json()
        user = data['Username']
        password = data['Password']
        hashpassword = hashlib.md5(password.encode("utf-8")).hexdigest()
        mydb.reconnect()
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM tbl_users WHERE userName = %s AND userPass = %s', (user, str(hashpassword)))
        data2 = cursor.fetchall()
        cursor.close()                        
        if len(data2) > 0:   
            session['userID']=data2[0][0]
            session['userFirstName'] = data2[0][2]
            session['userLastName'] = data2[0][3]
            session['userName'] = data2[0][4]
            session['userDefaultAddr'] = data2[0][5]
            session['userPhone'] = data2[0][6]
            session['userEirCode'] = data2[0][8]
            session['user'] = str(data2[0][3])
            session['is_logged_in'] = True
            session['useraccess'] = data2[0][7]
            return jsonify({'Result': '1'})
        return jsonify({'error' : 'Missing data!'})


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        reminder_app.add_task(task, time, priority)
        return redirect(url_for('index'))

    return render_template('add_task.html')
 
@app.route('/mark_done/<int:task_index>', methods=['POST'])
def mark_done(task_index):
    reminder_app.mark_task_done(task_index)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)