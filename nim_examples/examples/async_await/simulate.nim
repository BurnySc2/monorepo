import asyncdispatch
import random
import strformat

randomize()

proc run_some_code(i: int): Future[int] {.async.} =
    echo fmt"Starting process {i}"
    # Sleep for 1-2 seconds
    await sleep_async(rand(1.0..2.0))
    echo fmt"Done with process {i}"
    # Return some value
    return i * 2

proc main() {.async.} =
    var futures = newSeqOfCap[Future[int]](8)
    echo "Starting async calls"
    for i in 1..8:
        # Function calls start running as sool as possible
        futures.add run_some_code(i)
    echo "Waiting for async calls to finish"
    let data = await futures.all
    echo data

waitFor main()
