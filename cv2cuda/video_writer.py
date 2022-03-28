import time
import traceback
import os.path
import math
import logging

import psutil
import cv2
from cv2cuda.ffmpeg_process import FFMPEG
from cv2cuda.decorator import timeit

logger = logging.getLogger(__name__)
check_log = logging.getLogger(__name__ + ".check")
# check_log.setLevel(logging.DEBUG)


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
        if " " in filename:
            logger.warning("Please dont pass spaces in the filename, as the video writer may not work")
        self._filename = filename
        self._fps = fps
        self._frameSize = frameSize
        width, height = frameSize # wxh
        self._terminate_time = None
        self._count = 0
        self._maxframes = maxframes
        self._already_warned = False

        self._check_deps()


        if os.path.exists(filename):
            if not yes:
                answer = input(f"{filename} already exists, overwrite? Y/n")
                if answer.lower() == "y":
                    pass
                else:
                    raise Exception(f"{filename} exists")
            else:
                logger.warning(f"{filename} exists already. Overwriting.")


        if isColor:
            raise Exception(f"User supplied isColor={isColor}."\
                f" cv2cuda.VideoWriter does not support color."\
                " Terminating ..."
            )
                
        if maxframes is not math.inf:
            logger.warning(f"User supplied maxframes={maxframes}."\
                f" Program calling cv2cuda.VideoWriter may malfunction after {maxframes} are captured")

        if device != "gpu":
            logger.warning(
                f"User supplied device={device}."\
                " The GPU and CUDA drivers will NOT be used."
            )

        self._ffmpeg = FFMPEG(width, height=height, fps=fps, output=filename, device=device, codec=fourcc, encode=True)


    @timeit
    def write(self, image):
        if len(image.shape) == 3:
            if not self._already_warned:
                logger.warning(
                    "Color frames are not supported, please provide gray images to remove this warning"\
                    " I will force the frames gray now"
                )
                self._already_warned = True

            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        self._ffmpeg.write(image)
        self._count += 1
        if self._count == self._maxframes:
            self.release()


    def _check_cuda(self):
        logger.warning("CUDA checks not implemented yet")
        return
    

    def _check_ffmpeg(self):
        logger.warning("FFMPEG checks not implemented yet")
        return


    def _check_deps(self):
        pass
        # self._check_ffmpeg()
        # self._check_cuda()

    
    def _check_terminated(self):

        check_log.debug(self._ffmpeg._command)
        check_log.debug(self._count)

        for process in psutil.process_iter():
            process_line = " ".join(process.cmdline())            
            if self._ffmpeg._command == process_line:
                msg = f"{self._ffmpeg._command} is stuck"
                # assert False, msg
                check_log.warning(msg)
                return False
        
        return True

    def release(self):
        code = self._ffmpeg.terminate()
        print(f"Termination code for {self._ffmpeg._command}: {code}")
        self._terminate_time = time.time()
        try:
            status = self._ffmpeg.wait(self._TIMEOUT)
        except Exception as error:
            logger.error(error)
            logger.error(traceback.print_exc())
            self._ffmpeg.kill()
            status = 1

        check_log.debug(f"STATUS: {status}")        
        if not self._check_terminated():
            check_log.debug(f"Killing {self._ffmpeg._command}")
            self._ffmpeg.kill()
        
                
        return status


VideoWriter = FFMPEGVideoWriter


class CV2VideoWriter(cv2.VideoWriter):

    @timeit
    def write(self, *args, **kwargs):
        return super().write(*args, **kwargs)

    @timeit
    def read(self, *args, **kwargs):
        return super().read(*args, **kwargs)