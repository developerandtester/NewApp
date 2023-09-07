import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import mysql.connector
from flask_httpauth import HTTPBasicAuth
import pandas as pd
import json
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