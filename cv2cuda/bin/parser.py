import argparse

from cv2cuda.utils.components import SUPPORTED_CAMERAS

def get_parser():

    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=3860, help="width attribute of the camera and width of the recorded frames")
    ap.add_argument("--height", type=int, default=2178, help="height attribute of the camera and height of the recorded frames")
    ap.add_argument("--fps", type=int, default=30, help="Framerate of recording")
    ap.add_argument("--input", type=str, default="output", help="Input mp4")
    ap.add_argument("--output", type=str, default="output", help="Folder where output should be produced")
    ap.add_argument(
        "--camera", type=str, default="virtual",
        choices=SUPPORTED_CAMERAS
    )
    ap.add_argument("--device", default=0, help="Device to be used for encoding of video. Use cpu or gpu. An integer is understood as a GPU id")
    ap.add_argument(
        "--backend", type=str, default="FFMPEG", choices=["FFMPEG", "cv2"],
        help="""
        Backend to be used to encode the video.
        Options are cv2 (uses cv2.VideoWriter)
        or FFMPEG (calls an ffmpeg subprocess
        that reads output from the main cv2cuda process and encodes it)
        """
    )
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--profile", type=str, default=None)
    ap.add_argument("--duration", type=int, default=999999)
    ap.add_argument("--yes", default=False, action="store_true")
    return ap

