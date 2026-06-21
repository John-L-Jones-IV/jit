#!/usr/bin/env -S uv run
import filecmp
import os
import shutil
import subprocess
import unittest

from pathlib import Path
from jit import PROJECT_DIR


PROJECT_DIR = Path("/home/best/Projects/jit")
BASE_TEST_DIR = PROJECT_DIR / Path('t')
TESTING_DIR = BASE_TEST_DIR / Path('.testspace')
TEMPLATES_DIR = BASE_TEST_DIR / Path('testfiletemplates')


class TestRelativeDirectories(unittest.TestCase):
    def setUp(self):
        os.environ['PATH'] = '/home/best/Projects/jit/bin:' + os.environ['PATH']
        if TESTING_DIR.exists():
            shutil.rmtree(TESTING_DIR)
        shutil.copytree(TEMPLATES_DIR, TESTING_DIR)
        os.chdir(TESTING_DIR)

    def test0(self):
        subprocess.run(["jit", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["git", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        os.chdir('d1')
        subprocess.run(["jit", "add", "../README.md", "d2/testfile-two-deep.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["git", "add", "../README.md", "d2/testfile-two-deep.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        os.chdir('../')
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").left_only)
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").right_only)
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").diff_files)

    def test1(self):
        os.chdir('d1')
        subprocess.run(["jit", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["git", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["jit", "add", "d2/testfile-two-deep.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["git", "add", "d2/testfile-two-deep.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["git", "add", "../README.md"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["jit", "add", "../README.md"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").left_only)
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").right_only)
        self.assertListEqual([], filecmp.dircmp(".git/objects", ".jit/objects").diff_files)



    def tearDown(self):
        os.chdir('../')
        shutil.rmtree(TESTING_DIR)


if __name__ == '__main__':
    unittest.main(failfast=True)

