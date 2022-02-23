# Benchmark performance of ffmpeg video encoding using GPU or CPU
# Author: Antonio Ortega
# Email: antonio.ortega@kuleuven.be
# Date: 2022-02-22
##########################

import argparse
import subprocess
import time

from tqdm import tqdm
import numpy as np
from cameras import AsyncCamera, SimCamera
from pipeline import run_v1, run_v2, run_v3
from ffmpeg_communication import init_ffmpeg, make_command
import multiprocessing

VERSION=3

def get_parser(ap=None):
    if ap is None:
        ap = argparse.ArgumentParser()

    ap.add_argument("--height", type=int, default=2178)
    ap.add_argument("--width", type=int, default=3860)
    ap.add_argument("--fps", type=int, default=30)  
    ap.add_argument("--device", type=str, default=None, required=True)  
    ap.add_argument("--output", type=str, default=None)  
    ap.add_argument("--camera", type=str, default=None)
    ap.add_argument("--color", default=False, action="store_true")
    ap.add_argument("--preview", default=False, action="store_true")
    ap.add_argument("--debug-bytes-conversion", dest="debug_bytes_conversion", default=False, action="store_true")
    return ap

 
def main(ap=None, args=None):
    if args is None:
        ap = get_parser(ap=ap)
        args = ap.parse_args()
        
        
    command = make_command(args.device, width=args.width, height=args.height, fps=args.fps, output=args.output)
    default_data = np.random.randint(0, 256, (args.height, args.width, 1), dtype=np.uint8)


    if args.camera == "Basler":
        CameraClass = AsyncCamera
    else:
        CameraClass = SimCamera


    if VERSION == 1:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    elif VERSION == 2 or VERSION == 3:
        proc = init_ffmpeg(cmd=command)

    queue=multiprocessing.Queue(1)
    stop_queue = multiprocessing.Queue(1)
    camera = CameraClass(queue=queue, stop_queue=stop_queue, width=args.width, height=args.height, fps=args.fps)
    
    pb = tqdm()
    pb = None

    if args.debug_bytes_conversion:
        data = default_data
    else:
        data = None
    
    try:
        while True:
            if VERSION == 1:
                status = run_v1(camera, proc, args, pb, data=data)
            elif VERSION == 2:
                status = run_v2(camera, proc, args, pb, data=data)
            elif VERSION == 3:
                status = run_v3(camera, proc, args, pb, data=data)
            if status:
                break
    
    except KeyboardInterrupt:
        pass

    proc.stdin.close()
    if proc.stderr:
        proc.stderr.close()
    proc.wait()


if __name__ == "__main__":
    main()
