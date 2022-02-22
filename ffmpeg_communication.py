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
    # write bytes to processe's stdin and close the pipe to pass
    # data to piped process
    # check if stdin is open
    logging.debug(f"Writing {len(data)} bytes...")
    ffmpeg_cmd.stdin.write(data)
    logging.debug(f"Writing {len(data)} bytes done")

def make_command(device, width, height, fps, output):

    if device == "cpu":

        command = f"ffmpeg -y  -f rawvideo  -pix_fmt {PIX_FMT}"\
            f" -s {width}x{height} -r {str(fps)}"\
            f" -i - -an -vcodec mpeg4 {output}"
            
    elif device == "gpu":
        command = f"ffmpeg -y -f rawvideo -pix_fmt {PIX_FMT}"\
            " -vsync 0 -hwaccel cuda"\
            f" -s {width}x{height} -r {str(fps)}"\
            f" -i - -an -c:v h264_nvenc {output}"
            # f" -i - -an -c:v h264_nvenc -f null - "#{output}"

    print(command)
    command = shlex.split(command)
    return command

