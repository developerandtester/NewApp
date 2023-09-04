import datetime

class Reminder:
    def __init__(self):
        self.tasks = []

    def add_task(self, task, time, priority=1):
        self.tasks.append({'task': task, 'time': time, 'priority': priority, 'days_not_done': 0})

    def display_tasks(self):
        for i, task in enumerate(self.tasks):
            print(f"{i + 1}. Task: {task['task']}, Time: {task['time']}, Priority: {task['priority']}")

    def mark_task_done(self, task_index):
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]['days_not_done'] = 0
            print("Task marked as done!")
        else:
            print("Invalid task index!")

    def increase_priority_if_not_done(self):
        for task in self.tasks:
            if task['days_not_done'] >= 3:
                task['priority'] += 1

    def run_reminder(self):
        while True:
            now = datetime.datetime.now().strftime("%H:%M")
            for task in self.tasks:
                if now == task['time']:
                    print(f"Reminder: {task['task']}")
                    user_input = input("Did you do the task? (y/n): ").lower()
                    if user_input == 'y':
                        self.mark_task_done(self.tasks.index(task))
                    else:
                        task['days_not_done'] += 1
            self.increase_priority_if_not_done()

if __name__ == "__main__":
    reminder_app = Reminder()

    print("Welcome to Reminder App!")
    print("Example: Task: 'Workout', Time: '08:00', Priority: 1")
    print("Enter 'exit' in Task to stop adding tasks.")

    while True:
        task = input("Enter Task: ")
        if task.lower() == 'exit':
            break
        time = input("Enter Time (HH:MM): ")
        priority = int(input("Enter Priority (1-5): "))
        reminder_app.add_task(task, time, priority)

    print("\nYour tasks:")
    reminder_app.display_tasks()

    print("\nRunning the reminder:")
    reminder_app.run_reminder()
