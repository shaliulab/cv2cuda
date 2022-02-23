import cv2
from cameras_f import read_frame, stop_camera
from exceptions import QuitException
from ffmpeg_communication import write_to_ffmpeg


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

def run_v3(camera, proc, args, pb, data=None):
    try:
        if data is None:
            frame = camera.read_frame(color=args.color)
            data = frame
        
        write_to_ffmpeg(proc, data)
        if pb: pb.update(1)
        if  args.preview:
            cv2.imshow("frame", cv2.resize(frame, (300, 300)))  
            if cv2.waitKey(1) == ord("q"):
                raise QuitException
        return 0
    except (KeyboardInterrupt, QuitException):
        camera.stop()
        return 1