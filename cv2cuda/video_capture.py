import logging
import time

try:
    import numpy as np # type: ignore
except ModuleNotFoundError:
    raise Exception("The capture module requires numpy installed (pip install numpy)")

import cv2

from cv2cuda.decorator import timeit

class VideoCapture:
    """
    A simulated cv2.VideoCapture class with ability to set FPS
    Useful for testing
    """

    def __init__(self, idx):
        self._idx = idx
        self._last_frame = None
        self._last_time = 0
        self._fps = 30
        self._width = None
        self._height = None


    def set(self, prop, value):

        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            self._width = value
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            self._height = value

        elif prop == cv2.CAP_PROP_FPS:
            self._fps = value

        else:
            logging.warning("This is a simulated camera")

    def get(self, prop):
        logging.warning("This is a simulated camera")
        return None

    @timeit
    def read(self):

        assert self._height is not None
        assert self._width is not None
        assert self._fps is not None
        
        ret = True
        now = time.time()
        
        while not (now - self._last_time) > (1 / self._fps):
            time.sleep(0.001)
            now = time.time()

        try:

            self._last_frame = np.random.randint(0, 256, (self._height, self._width), np.uint8)
            self._last_time = now
            ret = True
        except:
            frame = None
            ret = False
            
        return ret, self._last_frame

    def release(self):
        return


