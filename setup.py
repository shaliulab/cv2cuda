from setuptools import setup, find_packages

PACKAGE_NAME = "cv2cuda"

setup(
    name=PACKAGE_NAME,
    version="1.0.2",
    install_requires=["opencv-python", "numpy", "psutil"],
    packages=find_packages(),
    extras_require={"profile": ["pynvml"], "test": ["progressbar"]},
    entry_points={
        "console_scripts": [
            "cv2cuda=cv2cuda.bin.main:main"
        ]
    },
    python_requires=">=3.8.12"
)
