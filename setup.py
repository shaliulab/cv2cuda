from setuptools import setup, find_packages

PACKAGE_NAME = "cv2cuda"

setup(
    name=PACKAGE_NAME,
    version="1.0.1",
    install_requires=["opencv-python", "numpy"],
    packages=find_packages(),
    extras_requires={"profile": ["pynvml"], "test": ["progressbar"]},
    entry_points={
        "console_scripts": [
            "cv2cuda=cv2cuda.bin.main:main" 
        ]
    },
)
