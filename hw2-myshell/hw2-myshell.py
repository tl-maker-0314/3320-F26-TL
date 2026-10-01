import os, signal
class Job:
    def __init__(self, pid, command, background):
        self.pid = pid
        self.command = command
        self.background = background
        self.status = "Running"


jobs = {}          
next_job_id = 1

while True:
    
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)

            if pid == 0:
                break

            for job_id, job in jobs.items():
                if job.pid == pid:
                    job.status = "Done"
                    break

        except ChildProcessError:
            break

    line = input("myshell> ").strip()

    args = line.split()
    
    if not args:
        print("Hey, you didn't input anything.")
        continue

    background = False

    if args[-1] == "&":
        background = True
        args.pop()

    if args[0] == "cd":
        pass

    elif args[0] == "exit":
        break

    elif args[0] == "jobs":
        for job_id, job in jobs.items():
            print(f"[{job_id}] {job.status}")
            print(job.command)

    elif args[0] == "fg":
        job_id = int(args[1])
        job = jobs[job_id]

        os.waitpid(job.pid, 0)

        del jobs[job_id]

    elif args[0] == "kill":
        job_id = int(args[1])
        job = jobs[job_id]

        os.kill(job.pid, signal.SIGTERM)
        
        print(f"[{job_id}] Terminated {job.command}")
    
    else:
        pid = os.fork()

        if pid == 0:
            os.execvp(args[0], args)
    
        else:
            if background:
                
                command = " ".join(args)
    
                job = Job(pid, command, background)
                jobs[next_job_id] = job
    
                print(f"[{next_job_id}] {pid} {command}")
    
                next_job_id += 1
    
            else:
                os.waitpid(pid, 0)
    