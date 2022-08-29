import subprocess
import shlex
import logging
import threading

PIX_FMT = "gray" # graycolor format

logger = logging.getLogger(__name__)
write_log = logging.getLogger(__name__ + ".write")
terminate_log = logging.getLogger(__name__ + ".terminate")
# write_log.setLevel(logging.DEBUG)
# terminate_log.setLevel(logging.DEBUG)


class FFMPEG:
    
    def __init__(self, width, height, fps, output, device="gpu", codec="h264_nvenc", encode=True):
        """
        Manage a subprocess which calls ffmpeg and encodes incoming images

        Arguments:
            * width, height (int): Width and height of the images
            * fps (int): Framerate of the output video
            * output (str): Path to the resulting video
            * device (str): If gpu, ffmpeg is called with gpu acceleration
            * codec (str): If device = gpu, this should be h264_nvenc, otherwise,
            it should be one of the codes available for the cv2.VideoWriter_fourcc call
            * encode (str): For now it should always be True
        """
        command, registers = self._setup(width, height, fps, output, device=device, codec=codec, encode=encode)
        cmd = shlex.split(command)
        self._cmd = cmd
        self._command = command
        logger.debug(cmd)

        self._process = subprocess.Popen(
            cmd,
            stdin=registers[0],
            stdout=registers[1],
            shell=False,
            bufsize=0,
        )
        self._terminate_event = False

        self._validate_popen()
        self._lock = threading.Lock()



    def _validate_popen(self):

        if self._process.poll() is None:
            logger.info(f"{self._command} is alive")


    def _setup(self, width, height, fps, output, device="gpu", codec="h264_nvenc", encode=True):

        if not encode:
            raise Exception("Decoder is not yet implemented")

        if device == "gpu":
            command = f"ffmpeg -y -loglevel warning -r {fps} -f rawvideo -pix_fmt {PIX_FMT}"\
                " -vsync 0 -extra_hw_frames 2"\
                f" -s {width}x{height}"       
            if output is None:
                command += f" -i - -an -c:v {codec} -f null - "
            else:
                command += f" -i - -an -c:v {codec} {output}"

        elif device == "cpu":
                command = f"ffmpeg -loglevel warning -y  -r {fps} -f rawvideo  -pix_fmt {PIX_FMT}"\
                    f" -s {width}x{height}"
                if output is None:
                    command += f" -i - -an -vcodec {codec} -f null -"
                else:
                    command += f" -i - -an -vcodec {codec} {output}"
        
        if encode:
            registers = (subprocess.PIPE, None)
        else:
            registers = (None, subprocess.PIPE)

        return command, registers


    def write(self, image):

        if not self._terminate_event:
            with self._lock:
                try:
                    self._process.stdin.write(image)
                    # write_log.debug(f"{image.shape} to {self._command}")
                except BrokenPipeError as error:
                    write_log.warning(
                        "The FFMPEG process\n"\
                        f"{self._command}"\
                        "\nis defunct"
                    )
                    self._terminate_event = 2


    def terminate(self):
        with self._lock:
            self._terminate_event = True
            logger.debug(f"Terminating {self._command}")
            self._process.stdin.close()
            self._process.terminate()
            self._process.communicate()
            self._process.poll()
            assert self._process.returncode is not None


    def kill(self):
        self._process.stdin.close()
        return self._process.kill()
        

    def poll(self):
        return self._process.poll()

    @property
    def returncode(self):
        return self._process.returncode


    def wait(self, *args, **kwargs):
        return self._process.wait(*args, **kwargs)
