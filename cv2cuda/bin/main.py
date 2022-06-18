"""
Run video encoding programs in parallel (either using threads or processes) to test the package
and benchmark your hardware
"""

import signal
import time
import os
import os.path

from cv2cuda.utils.components import Process, Thread, get_queue

from .parser import get_parser

signal_count = 0

def main():

    ap = get_parser()
    args = ap.parse_args()
    kwargs = vars(args)
    njobs = kwargs.pop("jobs")

    processes = [None, ] * njobs
    stop_queues = [None, ] * njobs

    if njobs == 1:
        ProgramClass = Thread
    else:
        ProgramClass = Process

    for i in range(njobs):
        stop_queues[i] = get_queue(1)
        process_kwargs = kwargs.copy()
        process_kwargs["stop_queue"] = stop_queues[i]
        processes[i] = ProgramClass(idx=i, **process_kwargs, daemon=True)

    def quitHandler(signalNumber, frame):

        global signal_count

        print(f"Received: signal.SIGINT")
        for i, process in enumerate(processes):
            process.terminate()

        signal_count += 1
        os._exit(0)

    signal.signal(signal.SIGINT, quitHandler)
    start_time = time.time()

    for i in range(njobs):
        print(i)
        processes[i].start()

    for i in range(njobs):
        print(i)
        try:
            processes[i].join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
