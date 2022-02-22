import subprocess
import logging
import shlex

PIX_FMT = "rgb24"
# PIX_FMT = "yuv420p"


def init_ffmpeg(cmd, *args, action: str = "", **kwargs):
    ffmpeg_cmd = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=False
    )
    return ffmpeg_cmd


def write_to_ffmpeg(ffmpeg_cmd, input_bytes: bytes) -> bytes or None:
    b = b''
    # write bytes to processe's stdin and close the pipe to pass
    # data to piped process
    # check if stdin is open
    logging.debug(f"Writing {len(input_bytes)} bytes...")
    ffmpeg_cmd.stdin.write(input_bytes)
    logging.debug(f"Writing {len(input_bytes)} bytes done")
    return b

def make_command(device, width, height, fps, output):

    # -rc-lookahead N 

    if device == "cpu":

        command = f"ffmpeg -y  -f rawvideo  -pix_fmt {PIX_FMT}"\
            f" -s {width}x{height} -r {str(fps)}"\
            f" -i - -an -vcodec mpeg4 {output}"
            
        # -pix_fmt yuv420p -preset slow -rc vbr_hq -b:v 8M -maxrate:v 10M -c:a aac -b:a 224k"\
    elif device == "gpu":
        # -hwaccel_output_format cuda -hwaccel cuvid"\
        command = f"ffmpeg -y -f rawvideo -pix_fmt {PIX_FMT}"\
            " -vsync 0 -hwaccel cuda"\
            f" -s {width}x{height} -r {str(fps)}"\
            f" -i - -an -c:v h264_nvenc {output}"
            # f" -i - -an -c:v h264_nvenc -f null - "#{output}"

    print(command)
    command = shlex.split(command)
    
    return command

