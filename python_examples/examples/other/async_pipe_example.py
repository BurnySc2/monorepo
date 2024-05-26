import asyncio


async def run():
    # Create the first subprocess (echo)
    echo_process = await asyncio.create_subprocess_exec(
        "echo",
        "line\n" * 10**4,
        stdout=asyncio.subprocess.PIPE,
    )

    # Count the number of lines
    wc_process = await asyncio.create_subprocess_exec(
        "wc",
        "-l",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    # Write the output of echo_process to the stdin of wc_process
    wc_output, _ = await wc_process.communicate(input=await echo_process.stdout.read())

    # Decode the output from bytes to string
    output = wc_output.decode()

    print(output)


if __name__ == "__main__":
    # Run the async function
    asyncio.run(run())
