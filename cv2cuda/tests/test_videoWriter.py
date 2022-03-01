import argparse
import unittest
import tempfile
import os
import urllib.request
import cv2
from cv2cuda import VideoWriter
import progressbar

BIGBUCKBUNNY_WEB = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

pbar = None

def show_progress(block_num, block_size, total_size):
    global pbar
    if pbar is None:
        pbar = progressbar.ProgressBar(maxval=total_size)
        pbar.start()

    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()
        pbar = None


def download_file(resource, destination):
    print(f"Downloading {resource} -> {destination}")
    urllib.request.urlretrieve(resource, destination, show_progress)

def get_video_writer(output):
    return VideoWriter(
                filename = output,
                apiPreference="FFMPEG",
                fourcc="h264_nvenc",
                fps=24,
                frameSize=(1280, 720),
                isColor=False,
            )
            

class TestVideoWriter(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self._mp4_file = tempfile.NamedTemporaryFile(suffix=".mp4")
        download_file(BIGBUCKBUNNY_WEB, self._mp4_file.name)
        
    def setUp(self):
        self._output = tempfile.NamedTemporaryFile(suffix=".mp4")
        self._cap = cv2.VideoCapture(self._mp4_file.name)

    def test_VideoWriter_initializes(self):

        video_writer = get_video_writer(self._output.name)        

        self.assertTrue(isinstance(video_writer, VideoWriter))
        self.assertTrue("write" in dir(video_writer))
        video_writer.release()

    def test_VideoWriter_writes(self):

        video_writer = get_video_writer(self._output.name)        

        for i in range(1200):
            ret, frame = self._cap.read()
            # color data not supported
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            video_writer.write(frame)
        video_writer.release()
        
        self.assertTrue(os.path.exists(self._output.name))
        file_size = os.path.getsize(self._output.name)
        self.assertTrue(file_size == 13267725)
        
    def tearDown(self):
        self._cap.release()
        # os.remove(self._output.name)
    
    @classmethod
    def tearDownClass(self):
        pass
        # os.remove(self._mp4_file.name)


if __name__ == "__main__":
    unittest.main()