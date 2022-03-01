import subprocess
import shlex
import logging

PIX_FMT = "gray" # graycolor format

class FFMPEG:
    
    def __init__(self, *args, **kwargs):
        command, registers = self._setup(*args, **kwargs)
        cmd = shlex.split(command)
        self._cmd = cmd
        self._command = command

        self._process = subprocess.Popen(
            cmd,
            stdin=registers[0],
            stdout=registers[1],
            shell=False
        )
        self._terminate_event = False


    def _setup(self, width, height, fps, output, device="gpu", codec="h264_nvenc", encode=True):

        if not encode:
            raise Exception("Decoder is not yet implemented")

        if device == "gpu":
            command = f"ffmpeg -y -r {fps} -f rawvideo -pix_fmt {PIX_FMT}"\
                " -vsync 0 -extra_hw_frames 2"\
                f" -s {width}x{height}"       
            if output is None:
                command += f" -i - -an -c:v {codec} -f null - "
            else:
                command += f" -i - -an -c:v {codec} {output}"

            registers = (subprocess.PIPE, None)


        elif device == "cpu":
                command = f"ffmpeg -y -r {fps} -f rawvideo  -pix_fmt {PIX_FMT}"\
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
            try:
                self._process.stdin.write(image)
            except BrokenPipeError as error:
                logging.warning(
                    "The FFMPEG process\n"\
                    f"{self._command}"\
                    "\nis defunct"
                )
                self._terminate_event = 2


    def stop(self):
        self._process.stdin.close()
        if self._process.stderr:
            self._process.stderr.close()
        self._process.wait()


    def terminate(self):
        self._terminate_event = True
        self._process.terminate()


    def poll(self):
        self._process.poll()


    def wait(self, *args, **kwargs):
        self._process.wait(*args, **kwargs)
