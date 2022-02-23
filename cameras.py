import cv2
import numpy as np
import time
import multiprocessing


class BaseCamera:

    def read_frame(self, color=False):
        frame = self._queue.get()
        return frame


try:
    from baslerpi.io.cameras import BaslerCamera
    BaslerCameraImport = True


    class AsyncCamera(multiprocessing.Process, BaseCamera):

        def __init__(self, width, height, fps, queue, stop_queue, *args, **kwargs):
            self._queue = queue
            self._stop_queue = stop_queue
            self._camera = BaslerCamera(
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
            self._camera.open(buffersize=100)
            super().__init__(*args, **kwargs)

        
        def run(self):

            for t, frames in self._camera:

                if self._stop_queue.qsize() > 1:
                    break
                else:
                    for frame in frames: # only 1
                        self._queue.put(frame)


        def stop(self):
            self._camera.close()


except ImportError:
    BaslerCameraImport = False
    AsyncCamera = None



class SimCamera(multiprocessing.Process, BaseCamera):

    def __init__(self, width, height, fps, queue, stop_queue, *args, **kwargs):
        self._queue = queue
        self._stop_queue = stop_queue
        self._width = width
        self._height = height
        self._fps = fps
        super().__init__(*args, **kwargs)


    def run(self):

        while True:
            if self._stop_queue.qsize() > 1:
                break
            else:
                frame = np.random.raindint(0, 255, (self._height, self._width, 1), np.uint8)
                self._queue.put(frame)


    def stop(self):
        return

