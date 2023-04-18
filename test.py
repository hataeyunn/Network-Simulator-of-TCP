from model import scheduler, packet, node

time = 0

schedule = scheduler.Scheduler()
node_1 = node.Node(0, 1, [], "client")
node_2 = node.Node(1, 0, [], "server")

schedule.insert_event(scheduler.Event(1, node_1), 50)
schedule.insert_event(scheduler.Event(1, node_1), 10)

print(schedule.get_next_event())
print(schedule.get_next_event())
