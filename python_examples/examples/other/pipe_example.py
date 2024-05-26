import subprocess

if __name__ == "__main__":
    # Create the first subprocess (echo)
    echo_process = subprocess.Popen(
        ["echo", "line\n" * 10**4],
        stdout=subprocess.PIPE,
    )

    # Count the number of lines
    wc_process = subprocess.Popen(
        ["wc", "-l"],
        stdin=echo_process.stdout,
        stdout=subprocess.PIPE,
    )
    output, error = wc_process.communicate()
    output = output.decode()
    print(output)
