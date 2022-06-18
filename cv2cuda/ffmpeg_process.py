import subprocess
import shlex
import logging
import threading
import time

PIX_FMT = "gray" # graycolor format

logger = logging.getLogger(__name__)
write_log = logging.getLogger(__name__ + ".write")
terminate_log = logging.getLogger(__name__ + ".terminate")
# write_log.setLevel(logging.DEBUG)
# terminate_log.setLevel(logging.DEBUG)


class FFMPEG:
    
    def __init__(self, *args, **kwargs):
        command, registers = self._setup(*args, **kwargs)
        cmd = shlex.split(command)
        self._cmd = cmd
        self._command = command
        logger.debug(cmd)

        self._process = subprocess.Popen(
            cmd,
            stdin=registers[0],
            stdout=registers[1],
            shell=False
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

            registers = (subprocess.PIPE, None)


        elif device == "cpu":
                command = f"ffmpeg -y -loglevel warning -r {fps} -f rawvideo  -pix_fmt {PIX_FMT}"\
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
                    write_log.debug(f"{image.shape} to {self._command}")
                except BrokenPipeError as error:
                    write_log.warning(
                        "The FFMPEG process\n"\
                        f"{self._command}"\
                        "\nis defunct"
                    )
                    self._terminate_event = 2


    def terminate(self):
        with self._lock:
            terminate_log.debug(f"Closing standard input of {self._command}")
            self._process.stdin.close()
            self._terminate_event = True
            terminate_log.debug(f"Terminating {self._command}")
            # terminate_log.debug(f"Sleeping 10 seconds")
            # time.sleep(10)
            code = self._process.terminate()
            terminate_log.debug(f"CODE: {code}")
            return code

    
    def kill(self):
        return self._process.kill()
        

    def poll(self):
        return self._process.poll()


    def wait(self, *args, **kwargs):
        return self._process.wait(*args, **kwargs)
