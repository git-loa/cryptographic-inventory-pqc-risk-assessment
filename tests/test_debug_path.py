"""
Test to debug the current working directory and list files in it.
This is useful for diagnosing issues with file paths in tests.
"""

import os


def test_debug_path():
    """
    Test to debug the current working directory and list files in it.
    This can help identify issues with file paths in tests.
    """
    print("WORKING DIR:", os.getcwd())
    print("FILES:", os.listdir(os.getcwd()))
