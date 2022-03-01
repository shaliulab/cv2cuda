import time
import logging
import os.path
import math

import cv2
from cv2cuda.ffmpeg_process import FFMPEG
from cv2cuda.decorator import timeit

class FFMPEGVideoWriter:
    """
    A cv2.VideoWriter-like interface that supports FFMPEG+CUDA
    for faster and efficient encoding of videos
    """
    _TIMEOUT=3

    def __init__(self, filename, apiPreference, fourcc, fps, frameSize, isColor=False, maxframes=math.inf, yes=True, device="gpu"):

        self._isColor = isColor # color not supported for now
        self._fourcc = fourcc
        self._apiPreference = apiPreference
        self._filename = filename
        self._fps = fps
        self._frameSize = frameSize
        width, height = frameSize # wxh
        self._terminate_time = None
        self._count = 0
        self._maxframes = maxframes

        self._check_deps()


        if os.path.exists(filename):
            if not yes:
                answer = input(f"{filename} already exists, overwrite? Y/n")
                if answer.lower() == "y":
                    pass
                else:
                    raise Exception(f"{filename} exists")
            else:
                logging.warning("{filename} exists already. Overwriting.")


        if isColor:
            raise Exception(f"User supplied isColor={isColor}."\
                f" cv2cuda.VideoWriter does not support color."\
                " Terminating ..."
            )
                
        if maxframes is not math.inf:
            logging.warning(f"User supplied maxframes={maxframes}."\
                f" Program calling cv2cuda.VideoWriter may malfunction after {maxframes} are captured")

        if device != "gpu":
            logging.warning(
                f"User supplied device={device}."\
                " The GPU and CUDA drivers will NOT be used."
            )

        self._ffmpeg = FFMPEG(width, height=height, fps=fps, output=filename, device=device, codec=fourcc, encode=True)


    @timeit
    def write(self, image):
        if len(image.shape) == 3:
            logging.warning(
                "Color frames are not supported, please provide gray images to remove this warning"\
                " I will force the frames gray now"
            )
            image = cv2.cvtColor(image, cv2.COLOR_BAYER_BG2GRAY)

        self._ffmpeg.write(image)
        self._count += 1
        if self._count == self._maxframes:
            self.release()


    def _check_cuda(self):
        logging.warning("CUDA checks not implemented yet")
        return
    

    def _check_ffmpeg(self):
        logging.warning("FFMPEG checks not implemented yet")
        return


    def _check_deps(self):
        self._check_ffmpeg()
        self._check_cuda()


    def release(self):
        self._ffmpeg.terminate()
        self._terminate_time = time.time()
        status = self._ffmpeg.wait(self._TIMEOUT)
        return status


class VideoWriter(FFMPEGVideoWriter):
    pass

class CV2VideoWriter(cv2.VideoWriter):

    @timeit
    def write(self, *args, **kwargs):
        return super().write(*args, **kwargs)

    @timeit
    def read(self, *args, **kwargs):
        return super().read(*args, **kwargs)