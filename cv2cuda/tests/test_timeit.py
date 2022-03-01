import unittest
import time
from cv2cuda.decorator import timeit

class TestTimeIt(unittest.TestCase):

    def setUp(self):

        @timeit
        def foo():
            time.sleep(.2)
        self._f = foo

    
    def test_timeit(self):

        self.assertTrue(self._f() is None)
        self.assertTrue(self._f.unwrapped() is None)

if __name__ == "__main__":
    unittest.main()
