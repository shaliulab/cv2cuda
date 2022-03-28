import argparse
import logging
import signal
import time
import os
import os.path

from cv2cuda.utils.components import Process, Thread, get_queue


def get_parser():

    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=3860, help="width attribute of the camera and width of the recorded frames")
    ap.add_argument("--height", type=int, default=2178, help="height attribute of the camera and height of the recorded frames")
    ap.add_argument("--fps", type=int, default=30, help="Framerate of recording")
    ap.add_argument("--input", type=str, default="output", help="Input mp4")
    ap.add_argument("--output", type=str, default="output", help="Folder where output should be produced")
    # ap.add_argument(
    #     "--camera", type=str, default="virtual",
    #     choices=["virtual", "Basler", "opencv"]
    # )
    ap.add_argument("--device", default=0, help="Device to be used for encoding of video. Use cpu or gpu. An integer is understood as a GPU id")
    ap.add_argument(
        "--backend", type=str, default="FFMPEG", choices=["FFMPEG", "cv2"],
        help="Backend to be used to encode the video."\
        "Options are cv2 (uses cv2.VideoWriter)"\
        " or FFMPEG (calls an ffmpeg subprocess"\
        " that reads output from the main cv2cuda process and encodes it)"
    )
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--profile", type=str, default=None)
    ap.add_argument("--duration", type=int, default=999999)
    ap.add_argument("--yes", default=False, action="store_true")
    return ap


signal_count = 0

def main():

    ap = get_parser()
    args = ap.parse_args()
    kwargs = vars(args)
    njobs = kwargs.pop("jobs")

    processes = [None, ] * njobs
    stop_queues = [None, ] * njobs

    if njobs == 1:
        ProcessClass = Thread
    else:
        ProcessClass = Process

    for i in range(njobs):
        stop_queues[i] = get_queue(1)
        process_kwargs = kwargs.copy()
        process_kwargs["stop_queue"] = stop_queues[i]
        print(process_kwargs)
        processes[i] = ProcessClass(idx=i, **process_kwargs, daemon=True)

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
