import datetime
from flask import Flask, render_template, request, redirect, url_for,session,jsonify,make_response, send_from_directory
import mysql.connector
import hashlib
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import openai


openai.api_key = "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"
app = Flask(__name__,template_folder='templates')
app.config["SECRET_KEY"] = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'  # You can choose other session storage options
Session(app)
# login_manager = LoginManager()
# login_manager.login_view = 'login'  # Specify the login view
# login_manager.init_app(app)

mydb = mysql.connector.connect(
  host="ulsq0qqx999wqz84.chr7pe7iynqr.eu-west-1.rds.amazonaws.com",
  user="yh1rouqsuxxqdgbs",
  password="okn19h5k93o3dcqf",
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
@app.route('/index')
def index():
    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        reminder_app.add_task(task, time, priority)

    reminder_app.run_reminder()
    if('is_logged_in' not in session):
        session['is_logged_in']=False
    else:
        session['is_logged_in']=True
    return render_template('index.html', tasks=reminder_app.tasks)


@app.route("/OneSignalSDKWorker.js")
def sw():
  response = make_response(send_from_directory(app.static_folder, "OneSignalSDKWorker.js"))
  return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Retrieve the user's hashed password from the database
        hashed_password = get_user_password(username)  # Implement this function
        
        # Compare the provided password with the hashed password
        if hashed_password and verify_password(password, hashed_password):
            # Successful login
            session['is_logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password. Please try again."
    
    return render_template('login.html')
     
def get_user_password(username):
    # SQL statement to retrieve the hashed password for the given username
    sql = "SELECT usr_pass FROM tbl_users WHERE usr_nm = %s"
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
        username = request.form['username']
        password = request.form['password']
        # Add code to validate and hash the password (e.g., using hashlib)
        
        # Check if the username is already taken
        if check_user_existence(username):
            return "Username already exists. Please choose a different one."
        
        # Insert the new user into the database
        insert_user_into_db(username, password)  # Implement this function
        
        # Redirect the user to the login page
        return redirect(url_for('login'))
    
    return render_template('signup.html')

def insert_user_into_db(username, password):
    # Hash the password (e.g., using hashlib)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # SQL statement to insert a new user
    sql = "INSERT INTO tbl_users (usr_nm, usr_pass) VALUES (%s, %s)"
    values = (username, hashed_password)
    
    # Execute the SQL statement
    cursor.execute(sql, values)
    mydb.commit()

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if not session.get('is_logged_in'):
        return redirect(url_for('login'))  # Redirect unauthenticated users to login

    if request.method == 'POST':
        task = request.form['task']
        time = request.form['time']
        priority = int(request.form['priority'])
        user_id = get_user_id(session['username'])  # Implement this function
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

@app.route('/mark_done/<int:task_index>', methods=['POST'])
def mark_done(task_index):
    reminder_app.mark_task_done(task_index)
    return redirect(url_for('index'))

#code for openAI API to get response as a chatbot
def getOpenAIresponse(prompt:str):
    conversation = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
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