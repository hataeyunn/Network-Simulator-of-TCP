import simpy
import heapq
import random

class Task:
    def __init__(self, name, env, scheduler, task_time):
        self.name = name
        self.env = env
        self.scheduler = scheduler
        self.task_time = task_time

    def __lt__(self, other):
        return self.task_time < other.task_time

    def process(self):
        print(f'At time {self.env.now}, executed task: {self.name}')
        # Schedule a new task 1 or 2 seconds later
        new_task_time = self.env.now + random.choice([1, 2])
        new_task = Task(f'New task at time {new_task_time}', self.env, self.scheduler, new_task_time)
        self.scheduler.add_task(new_task_time, new_task)

class Scheduler:
    def __init__(self, env):
        self.env = env
        self.priority_queue = []

    def schedule(self):
        while self.priority_queue:
            task_time, task = heapq.heappop(self.priority_queue)
            yield self.env.timeout(task_time - self.env.now)
            task.process()

    def add_task(self, task_time, task):
        heapq.heappush(self.priority_queue, (task_time, task))

env = simpy.Environment()
scheduler = Scheduler(env)

for task_time in [9, 15]:
    task = Task(f'Task at time {task_time}', env, scheduler, task_time)
    scheduler.add_task(task_time, task)

env.process(scheduler.schedule())
env.run(until=30)
