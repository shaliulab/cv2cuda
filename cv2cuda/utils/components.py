import logging
import os.path
import time
import threading
import multiprocessing
import math
from abc import ABC

import cv2
import cv2cuda
import cv2cuda.utils.cpu as cpu_utils
SUPPORTED_CAMERAS=["virtual", "opencv"]
# try:
#     from scicam.io.cameras import BaslerCamera #pyright: reportMissingImports=false
#     BASLER_CAMERA_ENABLED=True
# except ImportError:
#     BASLER_CAMERA_ENABLED=False

try:
    import cv2cuda.utils.gpu as gpu_utils
    GPU_PROFILING_ENABLED=True
except ImportError:
    GPU_PROFILING_ENABLED=False


def get_queue(size):
    return multiprocessing.Queue(size)


def get_camera(camera, width, height, fps, idx=0):

    if camera not in SUPPORTED_CAMERAS:
        raise Exception(f"Passed camera {camera} is not one of the supported cameras: {SUPPORTED_CAMERAS}")
    
    elif camera == "virtual":
        cap = cv2cuda.VideoCapture(idx)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # elif camera == "Basler":
    #     if not BASLER_CAMERA_ENABLED:
    #         raise Exception("Basler camera not supported")
    #     else:
    #         exposure = int(14000)
    #         print(exposure)

    #         cap = BaslerCamera(
    #             width=width,
    #             height=height,
    #             framerate=fps,
    #             exposure=exposure,
    #             iso=0,
    #             drop_each=1,
    #             use_wall_clock=False,
    #             timeout=30000,
    #             resolution_decrease=None,
    #             rois=None,
    #             start_time=time.time(),
    #             idx=idx
    #         )
    #         cap.open(buffersize=100)

    elif camera == "opencv":
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    return cap


def get_video_writer(output, fps, frameSize, backend="FFMPEG", device="gpu", **kwargs):

    if device == "gpu":
        if backend == "cv2":
            raise Exception(
                "cv2.VideoWriter class using GPU is not supported in Linux."\
                "https://github.com/opencv/opencv_contrib/issues/3044"
            )
            
        elif backend == "FFMPEG":
        
            video_writer = cv2cuda.VideoWriter(
                filename = output + '.mp4',
                apiPreference="FFMPEG",
                fourcc="h264_nvenc",
                fps=fps,
                frameSize=frameSize,
                isColor=False,
                **kwargs,
            )
    elif device == "cpu":
        if backend == "cv2":
            logging.warning(
                ".avi container will be used"\
                "(instead of .mp4)"\
                "because the developer's setup does not support"\
                "encoding of videos in the cpu to .mp4"          
            )
            video_writer = cv2cuda.CV2VideoWriter(
                filename = output + '.avi',
                apiPreference=cv2.CAP_FFMPEG,
                fourcc=cv2.VideoWriter_fourcc(*"MJPG"),
                fps=fps,
                frameSize=frameSize,
                isColor=False
            )
        elif backend == "FFMPEG":
            video_writer = cv2cuda.VideoWriter(
                filename = output + '.mp4',
                apiPreference="FFMPEG",
                fourcc="mpeg4",
                fps=fps,
                frameSize=frameSize,
                isColor=False,
                **kwargs,
            )            
    
    else:
        raise Exception("device must be one of [cpu, gpu]")
    
    return video_writer



class BaseProgram(ABC):


    def __init__(self, idx, stop_queue, width, height, fps, profile, output, *args, camera="virtual", backend="FFMPEG", device="0", yes=False, duration=math.inf, **kwargs):
        self._idx = idx,
        self._stop_queue = stop_queue
        self._width = width
        self._height = height
        self._fps = fps
        self._output = output
        self._backend = backend
        self._duration = duration
        self._camera = camera
        self._yes = yes

        self._output_prefix = os.path.join(output, f"{profile}_{idx}")
       
        if profile:
            self._profile = self._output_prefix + ".profile"
        else:
            self._profile = None

        if profile:
            self._init_profile_log()
        
        self._handle = None
        self._N = None


        if device != "cpu":
            if device == "gpu": device = 0
            try:
                self._device_int = int(device)
            except ValueError:
                raise Exception("Please pass to --device either [cpu] [gpu] or a [gpu index](0, 1,..)")
            
            device = "gpu"
        else:
            self._device_int = None

        self._device = device
        super().__init__()


    @property
    def video_name(self):
        return self._output_prefix + ".mp4"

    def _init_profile_log(self):

        os.makedirs(self._profile, exist_ok=True)

        with open(self._profile, "w") as filehandle:
            filehandle.write("t,read,write,cpu_usage,encode_usage,gpu_usage\n")


    def run(self):

        cap = get_camera(self._camera, self._width, self._height, self._fps)

        video_writer = None

        start_time = time.time()


        if self._profile and GPU_PROFILING_ENABLED:
            pynvml_handles = gpu_utils.init_pynvml_handlers(self._device_int)
        else:
            pynvml_handles = None


        while (time.time() - start_time) < self._duration:
             
            if not self._stop_queue.empty() :
                self._stop_queue.get()
                logging.debug("Got STOP")
                break

            try:
                logging.debug("Reading frame")

                if "unwrapped" in dir(cap.read):
                    now = time.time()
                    if self._profile:
                        (ret, frame), read_msec = cap.read()
                    else:
                        ret, frame = cap.read.unwrapped(cap)
                else:
                    ret, frame = cap.read()


                if ret:

                    if video_writer is None:
                        video_writer = get_video_writer(
                            self.video_name, self._fps, frame.shape[:2][::-1],
                            backend=self._backend, device=self._device,
                            yes=self._yes
                        )
                    
                    logging.debug("Writing frame")
                    if self._profile:
                        _, write_msec = video_writer.write(frame)
                    else:
                        video_writer.write.unwrapped(video_writer, frame)


                    if self._profile:
                        cpu_usage = cpu_utils.query_cpu_usage()
                        if GPU_PROFILING_ENABLED:
                            enc_usage = gpu_utils.query_encoder_usage(pynvml_handles)
                            gpu_usage = gpu_utils.query_gpu_usage(pynvml_handles)
                        else:
                            enc_usage = None
                            gpu_usage = None
                        
                        with open(self._profile, "a") as filehandle:
                            data = f"{now-start_time},{read_msec},{write_msec},"\
                            f"{cpu_usage},{enc_usage},{gpu_usage}"\
                            "\n"
                            filehandle.write(data)

                else:
                    break
            
            except KeyboardInterrupt:
                pass

        logging.debug(f"Queue is empty: {self._stop_queue.qsize() == 0}")
        logging.debug("Releasing VideoCapture instance")
        cap.release()
        if video_writer:
            logging.debug("Releasing VideoWriter instance")
            video_writer.release()
        logging.debug("Process terminated")
        return

    def terminate(self):
        self._stop_queue.put("STOP")
        time.sleep(.5)
        try:
            while not self._stop_queue.empty():
                self._stop_queue.get()
            super().terminate()
        except:
            logging.debug("Terminate failed")
            pass


class Process(BaseProgram, multiprocessing.Process):
    pass

class Thread(BaseProgram, threading.Thread):
    pass
