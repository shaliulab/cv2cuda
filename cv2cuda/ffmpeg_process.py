import subprocess
import shlex
import logging
import threading
import math

PIX_FMT = "gray" # graycolor format

logger = logging.getLogger(__name__)
write_log = logging.getLogger(__name__ + ".write")
terminate_log = logging.getLogger(__name__ + ".terminate")
# write_log.setLevel(logging.DEBUG)
# terminate_log.setLevel(logging.DEBUG)


class FFMPEG:

    def __init__(self, width, height, fps, output, device="gpu", codec="h264_nvenc", min_bitrate=None, max_bitrate=None, maxframes=math.inf, encode=True, gop_duration=None):
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
        command, registers = self._setup(width, height, fps, output, device=device, max_bitrate=max_bitrate, min_bitrate=min_bitrate, maxframes=maxframes, codec=codec, encode=encode, gop_duration=gop_duration)
        print(command)
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

    def _setup(self, width, height, fps, output, device="gpu", min_bitrate=None, max_bitrate=None, maxframes=math.inf, codec="h264_nvenc", encode=True, gop_duration=None):

        # drawtext = r'drawtext="box=1:text=\'%{n}\':x=(w-tw)*0.01: y=(2*lh):fontcolor=black: fontsize=16"'
        # pipeline = f'-vf {drawtext} {output}'
        pipeline = output

        # ffmpeg -hide_banner -h encoder=h264_nvenc | xclip -sel clip
        encoder_flags = " "#-preset lossless "

        if gop_duration is not None:
            encoder_flags += f"-g {int(fps * gop_duration)}"

        # if "highspeed" in output:
        #     encoder_flags = f"-g {int(fps*60)}"
        # else:
        #     encoder_flags = ""
        print(f"Encoder flags: {encoder_flags}")
        # import ipdb; ipdb.set_trace()

        if not encode:
            raise Exception("Decoder is not yet implemented")

        if device == "gpu":
            command = f"/usr/local/ffmpeg4/bin/ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -loglevel warning -r {fps} -f rawvideo -pix_fmt {PIX_FMT}"\
                " -vsync 0 -extra_hw_frames 2"\
                f" -s {width}x{height}"
            if output is None:
                command += f" -i - -an -c:v {codec} -f null - "
            else:
                command += f" -i - -an -c:v {codec} {encoder_flags} {pipeline}"

        elif device == "cpu":
                command = f"ffmpeg -loglevel warning -y  -r {fps} -f rawvideo  -pix_fmt {PIX_FMT}"\
                    f" -s {width}x{height}"
                if output is None:
                    command += f" -i - -an -vcodec {codec} -f null -"
                else:
                    command += f" -i - -an -vcodec {codec} {pipeline}"

        if encode:
            registers = (subprocess.PIPE, None)
        else:
            registers = (None, subprocess.PIPE)

        return command, registers



    def _setup_not_working(self, width, height, fps, output, device="gpu", min_bitrate=None, max_bitrate=None, maxframes=math.inf, codec="h264_nvenc", encode=True):


        # pipeline = f'-f lavfi -i color=a0a0a0:s={width}x{height} -f lavfi -i color=black:s={width}x{height} -f lavfi -i color=white:s={width}x{height} -i mask.png  -filter_complex "threshold[segmented],[segmented][4:v] overlay=0:0'

        # drawtext = r'drawtext="box=1:text=\'%{n}\':x=(w-tw)*0.01: y=(2*lh):fontcolor=black: fontsize=16"'
        # pipeline = f'-vf {drawtext} {output}'

        if output is not None and "lowres" in output:
            inputs = f'-f lavfi -i color=0c0c0a:s={width}x{height} -f lavfi -i color=black:s={width}x{height} -f lavfi -i color=white:s={width}x{height} '#-i /opt/scicam/mask.png'
            # inputs=""
            # gamma=1.8
            # gamma=2.7
            # pipeline = f'-filter_complex "[0:v][1:v][2:v][3:v]threshold[segmented],[segmented][4:v] overlay=0:0[out]" -map 0:v {output} -map "[out]" {output}_segmented.mp4'
            # pipeline = f'-filter_complex "format=pix_fmts=yuv420p,eq=contrast=1:brightness=-.1:saturation=1:gamma={gamma}:gamma_weight=1,dilation,erosion" {output}' # working!
            # pipeline = f'-filter_complex "eq=contrast=1:brightness=-.1:saturation=1:gamma={gamma}:gamma_r={gamma}:gamma_g={gamma}:gamma_b={gamma}:gamma_weight=1,dilation,erosion[out]" -f dshow -map "[out]" {output}'
            # encoder_flags="-preset p7 -cbr 1"
            encoder_flags = ""

            # pipeline = f'-filter_complex "format=pix_fmts=yuv420p,eq=c ontrast=1:brightness=-.1:saturation=1:gamma={gamma}:gamma_weight=1,dilation,erosion,split[er1][er2];[er1][1:v][2:v][3:v]threshold[thr];[thr]{drawtext}[out2];[er2]{drawtext}[out1]" -map "[out2]" {output}_thr.mp4 -map "[out1]" {output}'
            inputs=""
        else:
            encoder_flags = ""

            inputs = ""

        if not encode:
            raise Exception("Decoder is not yet implemented")

        bitrate = ""

        # if max_bitrate is None:
        #     bitrate = ""
        # else:
        #     bitrate = f" -b:v {max_bitrate/1000}k -minrate {min_bitrate/1000}k -maxrate {max_bitrate/1000}k -bufsize 1G"
        loglevel="warning"

        if maxframes is not None and maxframes < math.inf:

            position_total_seconds=maxframes / fps
            position_hours = math.floor(position_total_seconds // 3600)
            position_minutes = math.floor(position_total_seconds // 60)
            position_seconds = math.ceil(position_total_seconds % 60)
            position=f"-to {str(position_hours).zfill(2)}:{str(position_minutes).zfill(2)}:{str(position_seconds).zfill(2)}"
        else:
            position=" "

        if device == "gpu":
            # vsync passthrough
            # issues a deprecation warning that states vsync should be replaced with fps_mode
            # however doing that makes it stop working...
            # also, vsync=0 is the same as vsync passthrough

            command = f"ffmpeg -y -loglevel {loglevel} -r {int(fps)} -f rawvideo -pix_fmt {PIX_FMT}"\
                " -vsync 0 -extra_hw_frames 2" \
                f" -s {width}x{height}"
                # " -thread_queue_size 512"\
            if output is None:
                command += f" -i - {bitrate} -an -c:v {codec} {encoder_flags} -f null - "
            else:
                command += f' -i - -c:v {codec} {output}'


        # elif device == "cpu":
        #         command = f"ffmpeg -loglevel {loglevel} -y  -r {fps} -f rawvideo  -pix_fmt {PIX_FMT}"\
        #             f" -s {width}x{height}"
        #         if output is None:
        #             command += f" -i - {bitrate} -an -vcodec {codec} -f null -"
        #         else:

        #             command += f" -i - {bitrate} -an -vcodec {codec} {pipeline}"

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

                # poll = self._process.poll()
                # print(f"Poll {poll}")
                # if poll is not None:
                #     self.terminate()

    def terminate(self):
        with self._lock:
            print(f"Executing ffmpeg process terminate() for {self._command}")
            self._terminate_event = True
            logger.debug(f"Terminating {self._command}")
            self._process.stdin.close()
            out = self._process.terminate()
            self._process.wait()
            print(f"out: {out}")
            # self._process.communicate()
            self._process.poll()
            assert self._process.returncode is not None
            self._process.kill()

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
