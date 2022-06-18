python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine

# Release cv2cuda 
python3 -m build
python3 -m twine upload dist/* # this requires PyPI user and password
