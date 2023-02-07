import time
import xonsh

def count_jobs() -> int:
    xonsh.jobs._clear_dead_jobs()
    return len(xonsh.jobs.get_tasks())
    # return len(xonsh.jobs.get_jobs())

print("Starting jobs ...")
MAX_JOBS = 5
for i in range(10):
    # Create command
    command1 = ["sleep", f"{i}"]
    command2 = ["echo", f"{i}"]
    # Don't have more than X jobs at once
    while MAX_JOBS <= count_jobs():
        time.sleep(1)
    print(f"Starting job: {command1}")
    # Run command
    # @(command1)
    # Run command in background
    # @(command1) &
    # Run multiple commands sequentially in the background
    $i = i
    (sleep $i && echo $i) &
    # Run multiple commands in background suppressing output
    # (sleep $i && echo $i) all>/dev/null &

print("Waiting for jobs to finish")
while count_jobs() > 0:
    print(f"{count_jobs()} jobs still active...")
    time.sleep(1)

print("Parallel running jobs completed!")
