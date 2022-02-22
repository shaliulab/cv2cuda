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
import cv2

try:
    from baslerpi.io.cameras import BaslerCamera
    BaslerCameraImport = True
except ImportError:
    BaslerCameraImport = False



from ffmpeg_communication import init_ffmpeg, write_to_ffmpeg, make_command

VERSION=2

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




def read_frame(camera, color=False, height=2178, width=3860):
    
    if BaslerCameraImport and isinstance(camera, BaslerCamera):
        frame = camera._next_image()[0]
    else:
        frame = camera()

    if color:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    return frame


def init_camera(camera, width, height, fps):
    if camera:
        camera = BaslerCamera(
            width=width,
            height=height,
            framerate=fps,
            exposure=24000,
            iso=0,
            drop_each=1,
            use_wall_clock=False,
            timeout=30000,
            resolution_decrease=None,
            rois=None,
            start_time=time.time(),
            idx=0
        )
        camera.open(buffersize=100)

    else:
        frame  = np.random.randint(0, 256, (height, width, 1), dtype=np.uint8)

        def camera():
            return frame

    return camera


def stop_camera(camera):

    if BaslerCameraImport and isinstance(camera, BaslerCamera):
        return camera.close()
    else:
        return


class QuitException(Exception):
    pass


def run_v1(camera, proc, args, pb, data=None):
    try:
        if data is None:
            frame = read_frame(camera=camera, color=args.color, height=args.height, width=args.width)
            data = frame

        proc.stdin.write(data)
        if pb: pb.update(1)
        if  args.preview:
            cv2.imshow("frame", cv2.resize(frame, (300, 300)))  
            if cv2.waitKey(1) == ord("q"):
                raise QuitException
        return 0
    except (KeyboardInterrupt, QuitException):
        stop_camera(camera)
        return 1

def run_v2(camera, proc, args, pb, data=None):
    try:
        if data is None:
            frame = read_frame(camera=camera, color=args.color, height=args.height, width=args.width)
            data = frame
        
        write_to_ffmpeg(proc, data)
        if pb: pb.update(1)
        if  args.preview:
            cv2.imshow("frame", cv2.resize(frame, (300, 300)))  
            if cv2.waitKey(1) == ord("q"):
                raise QuitException
        return 0
    except (KeyboardInterrupt, QuitException):
        stop_camera(camera)
        return 1

  
def main(ap=None, args=None):
    if args is None:
        ap = get_parser(ap=ap)
        args = ap.parse_args()
        
        
    command = make_command(args.device, width=args.width, height=args.height, fps=args.fps, output=args.output)
    default_data = np.random.randint(0, 256, (args.height, args.width, 1), dtype=np.uint8).tobytes()


    if VERSION == 1:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    elif VERSION == 2:
        proc = init_ffmpeg(cmd=command)

    camera = init_camera(args.camera, width=args.width, height=args.height, fps=args.fps)
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
