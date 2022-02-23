import cv2
import numpy as np
import time
import multiprocessing

try:
    from baslerpi.io.cameras import BaslerCamera
    BaslerCameraImport = True
except ImportError:
    BaslerCameraImport = False

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

