import argparse

class SimProcess:
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.start_time = None
        self.completion_time = None

def read_processes(filename):
    processes = []

    with open(filename, "r") as file:
        next(file)

        for line in file:
            line = line.strip()

            if line == "":
                continue

            values = line.split(",")

            pid = values[0]
            arrival_time = int(values[1])
            burst_time = int(values[2])
            priority = int(values[3])

            processes.append(
                SimProcess(pid, arrival_time, burst_time, priority)
            )

    return processes

def reset_processes(processes):
    for p in processes:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

# Outputs
def output_metrics(processes, algo):
    if algo == "priority":
        print(f"{'PID':<8}{'Arrival':<10}{'Burst':<8}{'Priority':<10}{'Start':<8}{'Completion':<12}{'Waiting':<10}{'Turnaround':<12}")

    elif args.algo == "mlfq":
        results, events = schedule_mlfq(processes)
        output_mlfq_events(events)
        
    else:
        print(f"{'PID':<8}{'Arrival':<10}{'Burst':<8}{'Start':<8}{'Completion':<12}{'Waiting':<10}{'Turnaround':<12}")

    total_waiting_time = 0
    total_turnaround_time = 0

    for p in processes:
        turnaround_time = p.completion_time - p.arrival_time
        waiting_time = turnaround_time - p.burst_time

        total_waiting_time += waiting_time
        total_turnaround_time += turnaround_time

        if algo == "priority":
            print(f"{p.pid:<8}{p.arrival_time:<10}{p.burst_time:<8}{p.priority:<10}{p.start_time:<8}{p.completion_time:<12}{waiting_time:<10}{turnaround_time:<12}")
        else:
            print(f"{p.pid:<8}{p.arrival_time:<10}{p.burst_time:<8}{p.start_time:<8}{p.completion_time:<12}{waiting_time:<10}{turnaround_time:<12}")

    avg_waiting = total_waiting_time / len(processes)
    avg_time = total_turnaround_time / len(processes)

    print("\navg time =", round(avg_time, 2))
    print("avg waiting =", round(avg_waiting, 2))

# FCFS
def get_arrival_time(p):
    return p.arrival_time

def schedule_fcfs(processes, quantum=None):
    reset_processes(processes)

    results = []
    current_time = 0

    ordered = sorted(processes, key=get_arrival_time)

    for p in ordered:
        if current_time < p.arrival_time:
            current_time = p.arrival_time

        start = current_time
        end = start + p.burst_time

        p.start_time = start
        p.completion_time = end

        results.append((p.pid, start, end))
        current_time = end

    return results

# SJF
def schedule_sjf(processes, quantum=None):
    reset_processes(processes)

    results = []
    current_time = 0
    remaining = processes.copy()

    while len(remaining) > 0:
        available = []

        for p in remaining:
            if p.arrival_time <= current_time:
                available.append(p)

        if len(available) == 0:
            next_arrival = remaining[0].arrival_time

            for p in remaining:
                if p.arrival_time < next_arrival:
                    next_arrival = p.arrival_time

            current_time = next_arrival
            continue

        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                if available[j].burst_time < available[i].burst_time:
                    temp = available[i]
                    available[i] = available[j]
                    available[j] = temp

        p = available[0]

        start = current_time
        end = start + p.burst_time

        p.start_time = start
        p.completion_time = end

        results.append((p.pid, start, end))

        current_time = end
        remaining.remove(p)

    return results

# Round Robin
def schedule_rr(processes, quantum=None):
    if quantum is None or quantum <= 0:
        raise ValueError("Time quantum must be positive.")

    reset_processes(processes)

    results = []
    current_time = 0

    remaining = sorted(processes, key=get_arrival_time)
    ready_queue = []
    i = 0

    while i < len(remaining) or len(ready_queue) > 0:

        while i < len(remaining):
            if remaining[i].arrival_time <= current_time:
                ready_queue.append(remaining[i])
                i += 1
            else:
                break

        if len(ready_queue) == 0:
            current_time = remaining[i].arrival_time
        else:

            p = ready_queue[0]
            ready_queue = ready_queue[1:]

            start = current_time

            if p.remaining_time < quantum:
                run_time = p.remaining_time
            else:
                run_time = quantum

            end = start + run_time

            if p.start_time is None:
                p.start_time = start

            results.append((p.pid, start, end))

            current_time = end
            p.remaining_time = p.remaining_time - run_time

            if p.remaining_time == 0:
                p.completion_time = end

            while i < len(remaining):
                if remaining[i].arrival_time <= current_time:
                    ready_queue.append(remaining[i])
                    i += 1
                else:
                    break

            if p.remaining_time > 0:
                ready_queue.append(p)

    return results

# Priority (Lower priority = higher priority)

def schedule_priority(processes, quantum=None, aging_interval=4):

    reset_processes(processes)

    results = []
    current_time = 0
    remaining = processes.copy()

    while len(remaining) > 0:
        available = []

        for p in remaining:
            if p.arrival_time <= current_time:
                available.append(p)

        if len(available) == 0:
            next_arrival = remaining[0].arrival_time

            for p in remaining:
                if p.arrival_time < next_arrival:
                    next_arrival = p.arrival_time

            current_time = next_arrival
            continue

        p = available[0]

        for candidate in available:
            waiting_time = current_time - candidate.arrival_time
            effective_priority = candidate.priority - (waiting_time // aging_interval)

            p_waiting_time = current_time - p.arrival_time
            p_effective_priority = p.priority - (p_waiting_time // aging_interval)

            if effective_priority < p_effective_priority:
                p = candidate

            elif effective_priority == p_effective_priority:
                if candidate.arrival_time < p.arrival_time:
                    p = candidate

        start = current_time
        end = start + p.burst_time

        p.start_time = start
        p.completion_time = end

        results.append((p.pid, start, end))

        current_time = end
        remaining.remove(p)

    return results

# MLFQ
def schedule_mlfq(processes, quantum=None, priority_boost=20):
    reset_processes(processes)

    results = []
    events = []
    current_time = 0

    remaining = processes.copy()

    if quantum is None:
        quantum = 2

    if quantum <= 0:
        raise ValueError("Quantum must be positive.")

    if priority_boost <= 0:
        raise ValueError("Priority Boost must be positive.")

    quantums = [quantum, quantum * 2, quantum * 4]
    queues = [[], [], []]

    levels = {}
    time_used = {}

    for i in range(len(remaining)):
        for j in range(i + 1, len(remaining)):
            if remaining[j].arrival_time < remaining[i].arrival_time:
                temp = remaining[i]
                remaining[i] = remaining[j]
                remaining[j] = temp

    i = 0

    while i < len(remaining) or len(queues[0]) > 0 or len(queues[1]) > 0 or len(queues[2]) > 0:

        while i < len(remaining):
            if remaining[i].arrival_time <= current_time:
                p = remaining[i]
                queues[0].append(p)
                levels[p.pid] = 0
                time_used[p.pid] = 0
                i += 1
            else:
                break

        if len(queues[0]) == 0 and len(queues[1]) == 0 and len(queues[2]) == 0:
            if i < len(remaining):
                current_time = remaining[i].arrival_time
                continue
            else:
                break

        if current_time > 0 and current_time % priority_boost == 0:
            for level in range(1, len(queues)):
                for p in queues[level]:
                    queues[0].append(p)
                    levels[p.pid] = 0
                    time_used[p.pid] = 0
                    events.append((
                        current_time,
                        p.pid,
                        f"Q{level + 1}",
                        "Boosted to Q1"
                    ))

                queues[level] = []

        if len(queues[0]) > 0:
            level = 0
        elif len(queues[1]) > 0:
            level = 1
        else:
            level = 2

        p = queues[level][0]

        start = current_time
        end = current_time + 1

        if p.start_time is None:
            p.start_time = start

        if len(results) > 0 and results[-1][0] == p.pid and results[-1][2] == start:
            results[-1] = (p.pid, results[-1][1], end)
        else:
            results.append((p.pid, start, end))

        p.remaining_time -= 1
        time_used[p.pid] += 1
        current_time = end

        if p.remaining_time == 0:
            p.completion_time = end
            events.append((
                end,
                p.pid,
                f"Q{level + 1}",
                f"Finishes at t={end}"
            ))
            queues[level].pop(0)

        elif time_used[p.pid] >= quantums[level]:
            queues[level].pop(0)
            time_used[p.pid] = 0

            if level < 2:
                events.append((
                    end,
                    p.pid,
                    f"Q{level + 1}",
                    f"Runs full quantum ({quantums[level]}) -> demoted to Q{level + 2}"
                ))

                levels[p.pid] = level + 1
                queues[level + 1].append(p)
            else:
                events.append((
                    end,
                    p.pid,
                    "Q3",
                    f"Runs full quantum ({quantums[level]}) -> remains in Q3"
                ))
                queues[level].append(p)

    return results, events

#MLFQ Event Helper
def output_mlfq_events(events):
    print(f"{'Time':<8}{'PID':<8}{'Queue':<8}{'Action'}")

    for time, pid, queue, action in events:
        print(f"{time:<8}{pid:<8}{queue:<8}{action}")

# Compare
def compare_algorithms(processes):
    algorithms = [
        ("FCFS", schedule_fcfs),
        ("SJF", schedule_sjf),
        ("RR", schedule_rr),
        ("Priority", schedule_priority),
        ("MLFQ", schedule_mlfq)
    ]

    print(
        f"{'Algorithm':<12}"
        f"{'Avg Waiting':<15}"
        f"{'Avg Turnaround':<18}"
        f"{'Avg Response':<15}"
    )

    for name, algorithm in algorithms:
        # Create fresh processes for each algorithm
        test_processes = []

        for p in processes:
            test_processes.append(
                SimProcess(
                    p.pid,
                    p.arrival_time,
                    p.burst_time,
                    p.priority
                )
            )

        if name == "RR":
            algorithm(test_processes, quantum=4)
        elif name == "MLFQ":
            algorithm(test_processes)
        else:
            algorithm(test_processes)

        total_waiting = 0
        total_turnaround = 0
        total_response = 0

        for p in test_processes:
            total_waiting += (
                p.completion_time - p.arrival_time - p.burst_time
            )
            total_turnaround += p.completion_time - p.arrival_time
            total_response += p.start_time - p.arrival_time

        count = len(test_processes)

        print(
            f"{name:<12}"
            f"{total_waiting / count:<15.2f}"
            f"{total_turnaround / count:<18.2f}"
            f"{total_response / count:<15.2f}"
        )

# File Input

parser = argparse.ArgumentParser()
parser.add_argument("--workload", required=True)
parser.add_argument("--algo")
parser.add_argument("--compare", action="store_true")

args = parser.parse_args()
processes = read_processes(args.workload)

# Which Output
if args.compare:
    compare_algorithms(processes)

elif args.algo == "fcfs":
    schedule_fcfs(processes)
    output_metrics(processes, args.algo)

elif args.algo == "sjf":
    schedule_sjf(processes)
    output_metrics(processes, args.algo)

elif args.algo == "rr":
    schedule_rr(processes, quantum=4)
    output_metrics(processes, args.algo)

elif args.algo == "priority":
    schedule_priority(processes)
    output_metrics(processes, args.algo)

elif args.algo == "mlfq":
    results, events = schedule_mlfq(processes)
    output_mlfq_events(events)

    total_waiting_time = 0

    for p in processes:
        waiting_time = p.completion_time - p.arrival_time - p.burst_time
        total_waiting_time += waiting_time

    avg_waiting = total_waiting_time / len(processes)
    print("\nAverage waiting time =", round(avg_waiting, 2))