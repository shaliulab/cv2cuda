from setuptools import setup, find_packages

PACKAGE_NAME = "cv2cuda"

setup(
    name=PACKAGE_NAME,
    version="1.0.6",
    install_requires=["opencv-python>=3.4.8.29", "psutil"],
    packages=find_packages(),
    extras_require={"profile": ["pynvml", "numpy"], "test": ["progressbar"]},
    entry_points={
        "console_scripts": [
            "cv2cuda=cv2cuda.bin.main:main",
            "cv2cuda-test=cv2cuda.tests.test:main"

        ]
    },
    python_requires=">=3.7.0"
)
