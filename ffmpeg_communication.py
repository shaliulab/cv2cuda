import subprocess
import logging
import shlex

PIX_FMT = "rgb24"


def init_ffmpeg(cmd):
    ffmpeg_cmd = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=False
    )
    return ffmpeg_cmd


def write_to_ffmpeg(ffmpeg_cmd, data: bytes) -> bytes or None:
    logging.debug(f"Writing {len(data)} bytes...")
    ffmpeg_cmd.stdin.write(data)
    logging.debug(f"Writing {len(data)} bytes done")


def make_command(device, width, height, fps, output=None):

    if device == "cpu":

        command = f"ffmpeg -y  -f rawvideo  -pix_fmt {PIX_FMT}"\
            f" -s {width}x{height} -r {str(fps)}"

        
        if output is None:
            command += f" -i - -an -vcodec mpeg4 -f null -"
        else:
            command += f" -i - -an -vcodec mpeg4 {output}"
            
    elif device == "gpu":
        command = f"ffmpeg -y -f rawvideo -pix_fmt {PIX_FMT}"\
            " -vsync 0 -hwaccel cuda"\
            f" -s {width}x{height} -r {str(fps)}"
        
        if output is None:
            command += f" -i - -an -c:v h264_nvenc -f null - "
        else:
            command += f" -i - -an -c:v h264_nvenc {output}"

    print(command)
    command = shlex.split(command)
    return command

