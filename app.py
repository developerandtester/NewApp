import datetime
from flask import Flask, render_template, request, redirect, url_for,session,jsonify,make_response, send_from_directory
import mysql.connector
import hashlib
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import openai
from apscheduler.schedulers.background import BackgroundScheduler



openai.api_key = "INSERT KEY HERE"
app = Flask(__name__,template_folder='templates')
app.config["SECRET_KEY"] = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'  # You can choose other session storage options
scheduler = BackgroundScheduler()

# login_manager = LoginManager()
# login_manager.login_view = 'login'  # Specify the login view
# login_manager.init_app(app)

mydb = mysql.connector.connect(
  host="ulsq0qqx999wqz84.chr7pe7iynqr.eu-west-1.rds.amazonaws.com",
  user="USER",
  password="PASS",
  database="nyuufuvltab3cl9m",
  port=3306
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
        sql = "INSERT INTO tbl_tasks (task_usr_id, task_desc, task_reminder_time, task_priority,last_done_date) VALUES (%s, %s, %s, %s,%s)"
        print(sql)
        values = (user_id, task_desc, task_time, task_priority,None)
    # Execute the SQL statement
        cursor.execute(sql, values)
        mydb.commit()
    
    def mark_task_done_in_db(self, task_id):
        # SQL statement to mark a task as done
        sql = "UPDATE tbl_tasks SET task_done = 1,last_done_date = CURDATE() WHERE task_id = %s"
        values = (task_id,)
        cursor.execute(sql, values)
        mydb.commit()
    
    def check_tasks_status(self):
        # Define the criteria for task completion (e.g., 3 days since last_done_date)
        completion_criteria = datetime.datetime.now() - datetime.timedelta(days=3)

        for task in self.tasks:
            if task['last_done_date'] is not None and task['last_done_date'] <= completion_criteria:
                # Task hasn't been done within the criteria, update task priority
                task['priority'] += 1

reminder_app = Reminder()
scheduler.add_job(reminder_app.check_tasks_status, 'cron', hour=0, minute=0)
scheduler.start()


@app.route('/')
@app.route('/index')
def index():
    print(session)    
    if session.get('is_logged_in') == None:
        return redirect(url_for('login'))  # Redirect unauthenticated users to login
    elif session['is_logged_in'] == "False":
        session['is_logged_in'] = "False"
        return redirect(url_for('login'))
    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        reminder_app.add_task(task, time, priority)
    
    # user_id = get_user_id(session['username'])
    # print(user_id)
    # if user_id is not None:
    tasks = get_user_tasks(0)
    
    # else:
    #     tasks = []
   

    reminder_app.run_reminder()

    return render_template('index.html', tasks=tasks)    

def get_user_tasks(user_id):
    # SQL statement to retrieve tasks for the given user ID
    sql = "SELECT task_id, task_desc, task_reminder_time, task_priority FROM tbl_tasks WHERE task_usr_id = 0"
    cursor.execute(sql)
    #cursor.execute(sql, (user_id,))
    tasks = []

    # Fetch all the tasks for the user
    rows = cursor.fetchall()
    print(rows)
    for row in rows:
        task_id, task_desc, task_reminder_time, task_priority = row
        print(task_id, task_desc, task_reminder_time, task_priority)
        tasks.append({
            'task_id': task_id,
            'task': task_desc,
            'time': task_reminder_time,
            'priority': task_priority
        })

    return tasks

@app.route("/OneSignalSDKWorker.js")
def sw():
  response = make_response(send_from_directory(app.static_folder, "OneSignalSDKWorker.js"))
  return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(password)
        # Retrieve the user's hashed password from the database
        hashed_password = get_user_password(username)  # Implement this function
        print(hashed_password)
        # Compare the provided password with the hashed password
        if hashed_password and verify_password(password, hashed_password):
            # Successful login
            session['is_logged_in'] = "True"
            session['username'] = username
            sql = "SELECT usr_id FROM tbl_users WHERE usr_login = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result:
                session['user_id'] = result[0]
            
            return redirect(url_for('index'))
        else:
            return "Invalid username or password. Please try again."
    
    return render_template('login.html')
     
def get_user_password(username):
    # SQL statement to retrieve the hashed password for the given username
    sql = "SELECT usr_pass FROM tbl_users WHERE usr_login = %s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Return the hashed password
    return None

def verify_password(provided_password, hashed_password):
    # Hash the provided password and compare it with the stored hashed password
    provided_hashed = hashlib.sha256(provided_password.encode()).hexdigest()    
    return provided_hashed == hashed_password


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['userName']
        password = request.form['userPass']
        email= request.form['userEmail']
        # Add code to validate and hash the password (e.g., using hashlib)
        
        # Check if the username is already taken
        if check_user_existence(email):
            return "Username already exists. Please choose a different one."
        
        # Insert the new user into the database
        insert_user_into_db(username,email, password)  # Implement this function
        
        # Redirect the user to the login page
        return redirect(url_for('login'))
    
    return render_template('signup.html')

def insert_user_into_db(username,email, password):
    # Hash the password (e.g., using hashlib)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # SQL statement to insert a new user
    sql = "INSERT INTO tbl_users (usr_nm, usr_pass,usr_login) VALUES (%s, %s,%s)"
    values = (username, hashed_password,email)
    
    # Execute the SQL statement
    cursor.execute(sql, values)
    mydb.commit()

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if not session.get('is_logged_in'):
        return redirect(url_for('login'))  # Redirect unauthenticated users to login

    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        user_id = session['user_id']  # Implement this function
        reminder_app.add_task_to_db(user_id, task, time, priority)
        return redirect(url_for('index'))

    return render_template('add_task.html')

def get_user_id(username):
    # SQL statement to retrieve the user ID for the given username
    sql = "SELECT usr_id FROM tbl_users WHERE usr_nm = %s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Return the user ID
    return None


@app.route("/logout",methods = ['GET',"POST"])
def logout():    
    session.clear()
    session['is_logged_in']="False"
    return redirect(url_for('index'))

def check_sql_injection(text):
    keywords = ['select', 'insert', 'update', 'delete', 'drop', 'alter', 'create', 'rename', 'truncate']
    for keyword in keywords:
        if keyword in text.lower():
            return True
    return False

def check_user_existence(email):
    mydb.reconnect()
    cursor = mydb.cursor()
    query = "SELECT * FROM tbl_users WHERE usr_login = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    if user is not None:
        return True
    return False

@app.route('/mark_done/<int:task_index>', methods=['POST'])
def mark_done(task_index):
    reminder_app.mark_task_done(task_index)
    return redirect(url_for('index'))

#code for openAI API to get response as a chatbot
def getOpenAIresponse(prompt:str):
    conversation = [
        {'role': 'system', 'content': 'You are a helpful assistant. But only for mental health purposes. So the reply should only be in 400 to 500 words.'},
        {'role': 'user', 'content': prompt}
    ]
    print(conversation)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=conversation
    )
    return response['choices'][0]['message']['content']

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_message = data['message']
    # Call the getOpenAIresponse function to get an AI response
    ai_response = getOpenAIresponse(user_message)
    response_data = {'response': ai_response}
    return jsonify(response_data), 200, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    app.run(debug=True)
