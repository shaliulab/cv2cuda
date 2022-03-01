import argparse
import logging
import threading
import multiprocessing
import signal
import time
import math
import os
import os.path

import cv2
import cv2cuda
import cv2cuda.utils.cpu as cpu_utils
try:
    import cv2cuda.utils.gpu as gpu_utils
    GPU_PROFILING_ENABLED=True
except ImportError:
    GPU_PROFILING_ENABLED=False


try:
    from baslerpi.io.cameras import BaslerCamera
    BASLER_CAMERA_ENABLED=True
except ImportError:
    BASLER_CAMERA_ENABLED=False


def get_camera(camera, width, height, fps):
    
    if camera == "virtual":
        cap = cv2cuda.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    elif camera == "Basler":
        if not BASLER_CAMERA_ENABLED:
            raise Exception("Basler camera not supported")
        else:
            exposure = int(14000)
            print(exposure)

            cap = BaslerCamera(
                width=width,
                height=height,
                framerate=fps,
                exposure=exposure,
                iso=0,
                drop_each=1,
                use_wall_clock=False,
                timeout=30000,
                resolution_decrease=None,
                rois=None,
                start_time=time.time(),
                idx=0
            )
            cap.open(buffersize=100)

    else:
        raise Exception("Passed supported camera [virtual,Basler]")

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


class BaseProcess:


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

        os.makedirs(os.path.dirname(self._profile), exist_ok=True)

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

class Process(BaseProcess, multiprocessing.Process):
    pass

class Thread(BaseProcess, threading.Thread):
    pass

def get_parser():

    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=3860)
    ap.add_argument("--height", type=int, default=2178)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--output", type=str, default="output")
    ap.add_argument("--camera", type=str, default="virtual")
    ap.add_argument("--device", type=str, default=0)
    ap.add_argument("--backend", type=str, default="FFMPEG")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--profile", type=str, default=None)
    ap.add_argument("--duration", type=int, default=999999)
    ap.add_argument("--yes", default=False, action="store_true")
    return ap


signal_count = 0

def main():

    ap = get_parser()
    args = ap.parse_args()
    kwargs = vars(args)
    njobs = kwargs.pop("jobs")

    # process(**kwargs)
    processes = [None, ] * njobs
    stop_queues = [None, ] * njobs

    if njobs == 1:
        ProcessClass = Thread
    else:
        ProcessClass = Process

    for i in range(njobs):
        stop_queues[i] = multiprocessing.Queue(1)
        process_kwargs = kwargs.copy()
        process_kwargs["stop_queue"] = stop_queues[i]
        print(process_kwargs)
        processes[i] = ProcessClass(idx=i, **process_kwargs, daemon=True)

    def quitHandler(signalNumber, frame):

        global signal_count

        print(f"Received: signal.SIGINT")
        for i, process in enumerate(processes):
            process.terminate()

        signal_count += 1
        os._exit(0)

    signal.signal(signal.SIGINT, quitHandler)
    start_time = time.time()

    for i in range(njobs):
        print(i)
        processes[i].start()

    for i in range(njobs):
        print(i)
        try:
            processes[i].join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
