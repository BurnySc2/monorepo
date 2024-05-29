import subprocess
import time

if __name__ == "__main__":
    # Create the first subprocess (echo)
    start = time.time()
    echo_process = subprocess.Popen(
        ["sh", "-c", r'echo "line\n" && sleep 1 && echo "line\n" && sleep 1 && echo "line"'],
        # ["echo", "line\n" * 10**4],
        stdout=subprocess.PIPE,
    )

    # Count the number of lines
    wc_process = subprocess.Popen(
        ["sh", "-c", r"sleep 2 && wc -l"],
        # ["wc", "-l"],
        stdin=echo_process.stdout,
        stdout=subprocess.PIPE,
    )
    output, error = wc_process.communicate()
    end = time.time()
    output = output.decode()
    print(end - start)  # 2 seconds which means it runs in parallel
    print(output)
