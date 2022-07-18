import time
import subprocess
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


class FFMPEGVideoWriter:
    """
    A cv2.VideoWriter-like interface that supports FFMPEG+CUDA
    for faster and efficient encoding of videos
    """

    _TIMEOUT=3
    _CODEC_BURNIN_PERIOD=5 # seconds

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
        self._is_released = False

        self._check_deps()

        ODD_WRONG=1

        if width % 2 == ODD_WRONG:
            width-=1

        if height % 2 == ODD_WRONG:
            height-=1

        self._width = width
        self._height = height


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
            raise Exception(
                f"""User supplied isColor={isColor}.
                cv2cuda.VideoWriter does not support color.
                Terminating ...
                """
            )
                
        if maxframes is not math.inf:
            logger.warning(
                f"""
                User supplied maxframes={maxframes}.
                Program calling cv2cuda.VideoWriter may malfunction after {maxframes} are captured
                """
            )

        if device != "gpu":
            logger.warning(
                f"""User supplied device={device}.
                The GPU and CUDA drivers will NOT be used.
                """
            )

        self._ffmpeg = FFMPEG(width=width, height=height, fps=fps, output=filename, device=device, codec=fourcc, encode=True)

        _filename, extension = os.path.splitext(filename)
        if extension == ".mp4" and fourcc == "h264_nvenc":
            self._hq_video_writer = cv2.VideoWriter(
                f"{_filename}.avi",
                cv2.VideoWriter_fourcc(*"DIVX"),
                frameSize=(width, height),
                fps=fps,
                isColor=False,
            )
            self._hq_video_writer_open = True

        else:
            self._hq_video_writer = None
            self._hq_video_writer_open = False

    def ensure_size(self, img):
        return img[:self._height, :self._width]


    def __str__(self):
        return self._filename


    @timeit
    def write(self, image):
        if len(image.shape) == 3:
            if not self._already_warned:
                logger.warning(
                    """
                    Color frames are not supported, please provide gray images to remove this warning
                    I will force the frames gray now, which may add computational time which could be spared
                    """
                )
                self._already_warned = True

            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image = self.ensure_size(image)
        self._ffmpeg.write(image)
        if self._hq_video_writer and self._count < (self._CODEC_BURNIN_PERIOD * self._fps):
            self._hq_video_writer.write(image)
        elif self._hq_video_writer_open:
            self._hq_video_writer.release()
            self._hq_video_writer_open = False

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
        # TODO
        # Write some code that
        # 1. Checks ffmpeg is installed and can be called with the syntax
        # ffmpeg -y -loglevel warning -r 40.0 -f rawvideo -pix_fmt gray -vsync 0 -extra_hw_frames 2 -s NxM \ 
        #   -i - -an -c:v h264_nvenc video.mp4
        # 2. Checks that the right CUDA drivers are installed (so ffmpeg can use them)

        # For now, the user really checks if this is fine just by running the program
        # and checking if an error immediately pops up
        
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
        self._ffmpeg.terminate()
        del self._ffmpeg._process
        del self._ffmpeg
        self._is_released = True

    def is_released(self):
        return self._is_released



VideoWriter = FFMPEGVideoWriter


class CV2VideoWriter(cv2.VideoWriter):
    """
    A clone of the standard cv2.VideoWriter, with a timer for the write method
    """

    @timeit
    def write(self, *args, **kwargs):
        return super().write(*args, **kwargs)

