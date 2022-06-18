A replacement for cv2.videoWriter with CUDA support in Linux, [which is currently not supported](https://github.com/opencv/opencv_contrib/issues/3044)
Instead, we use [ffmpeg](https://www.ffmpeg.org/) built with CUDA support to encode and save frames.

# Tested requirements

* NVIDIA GPU
* CUDA 11.3.r11.3
* Ubuntu 20.04.4 LTS
* Python 3.8.10


# Quick encoding test from a random image with 2000x2000 image at 45 FPS

```
cv2cuda --device gpu --width 2000 --height 2000 --fps 45 --output output.mp4
```

# Implementation details


## FFMPEG

Following the guides from NVIDIA, ffmpeg and StackOverflow:

  * https://docs.nvidia.com/video-technologies/video-codec-sdk/ffmpeg-with-nvidia-gpu/#commonly-faced-issues-and-tips-to-resolve-them
  * https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu
  * https://stackoverflow.com/a/55747785/3541756

an ffmpeg subprocess is used to receive Python's standard output and encode it into a video using GPU hardware acceleration.
The ffmpeg command has the following structure

```
ffmpeg -y -r FRAMERATE -f rawvideo -pix_fmt gray -vsync 0 -extra_hw_frames 2 -s WIDTHxHEIGHT -i - -an -c:v h264_nvenc OUTPUT.mp4
```

* `-y -r FRAMERATE` tells ffmpeg to ignore and overwrite any existing data in the output and sets the framerate 
*  `-f rawvideo -pix_fmt gray` tells ffmpeg that the input will be raw video (which matches what Python outputs), and the pixel format is gray (only gray is supported for now by cv2cuda)

* `-vsync 0 -extra_hw_frames 2` are flags that I have read can improve the performance. But I am not sure why and maybe they dont. They could potentially be removed
*  `-s WIDTHxHEIGHT` tells ffmpeg what width and height to expect in the incoming frames
* `-i -` tells ffmpeg to read input from the standard input (i.e. to listen to Python)
* `-an` tells ffmpeg there is no audio input
* `c:v h264_nvenc` tells ffmpeg to use hardware acceleration by using the NVIDIA h264_nvenc codec for encoding
* `OUTPUT.mp4` (or whatever path) is the output file

This command is built and run for you when you use cv2cuda

## VideoWriter

The cv2cuda package provides a drop-in replacement for the popular `cv2.VideoWriter` class called `cv2cuda.VideoWriter`.
It has functionality very similar to the original `cv2.VideoWriter` but uses ffmpeg behind the scenes to make use of the GPU. Thus it is a solution to the issue posed here https://github.com/opencv/opencv_contrib/issues/3044

You can initialize like so:

```
video_writer = cv2cuda.VideoWriter(
                filename = output_mp4,
                apiPreference="FFMPEG",
                fourcc="h264_nvenc",
                fps=fps,
                frameSize=frameSize,
                isColor=False,
)
```

i.e. just like the `cv2.VideoWriter`


You can add frames to the video, and stop it, in a way identical to the `cv2.VideoWriter`

```
video_writer.write(frame)
video_writer.release()
```

# Versions

```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2021 NVIDIA Corporation
Built on Sun_Mar_21_19:15:46_PDT_2021
Cuda compilation tools, release 11.3, V11.3.58
Build cuda_11.3.r11.3/compiler.29745058_0
```


```
ffmpeg version n4.2.2 Copyright (c) 2000-2019 the FFmpeg developers
built with gcc 9 (Ubuntu 9.3.0-17ubuntu1~20.04)
configuration: --prefix=/usr/local/ffmpeg --pkg-config-flags=--static --enable-nonfree --enable-gpl --enable-version3 --enable-libmp3lame --enable-libvpx --enable-libopus --enable-opencl --enable-libxcb --enable-opengl --enable-nvenc --enable-vaapi --enable-vdpau --enable-ffplay --enable-ffprobe --enable-libxvid --enable-libx264 --enable-libx265 --enable-openal --enable-openssl --enable-cuda-nvcc --enable-cuvid --extra-cflags=-I/usr/local/cuda/include --extra-ldflags=-L/usr/local/cuda/lib64 --nvccflags='-gencode arch=compute_52,code=sm_52 -O2' --enable-pic
libavutil      56. 31.100 / 56. 31.100
libavcodec     58. 54.100 / 58. 54.100
libavformat    58. 29.100 / 58. 29.100
libavdevice    58.  8.100 / 58.  8.100
libavfilter     7. 57.100 /  7. 57.100
libswscale      5.  5.100 /  5.  5.100
libswresample   3.  5.100 /  3.  5.100
libpostproc    55.  5.100 / 55.  5.100
```
