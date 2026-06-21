#!/usr/bin/env -S uv run
import os
import shutil
import subprocess
import sys
import unittest
import zlib
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
TESTING_DIR = PROJECT_DIR / Path('t/.testspace')
TEMPLATES_DIR = PROJECT_DIR / Path('t/testfiletemplates')


class TestHarness(unittest.TestCase):
    def setUp(self):
        os.environ['PATH'] = '/home/best/Projects/jit/bin:' + os.environ['PATH']
        # TODO: does path get cleared or does it grow every time?
        if TESTING_DIR.exists():
            shutil.rmtree(TESTING_DIR)
        shutil.copytree(TEMPLATES_DIR, TESTING_DIR)
        os.chdir(TESTING_DIR)

    def test01GitHarness(self):
        _run_on_terminal("git init")
        _run_on_terminal("git add README.md")
        self.assertTrue(Path(".git/objects/c6/20724c9d894a8c6639bbb4bda372a8d0959763").is_file())

    def test02JitHarness(self):
        _run_on_terminal("jit init")
        _run_on_terminal("jit add README.md")
        self.assertTrue(Path(".jit/objects/c6/20724c9d894a8c6639bbb4bda372a8d0959763").is_file())

    def tearDown(self):
        os.chdir('../')
        shutil.rmtree('.testspace')


class TestObjectCompatability(unittest.TestCase):
    def setUp(self):
        os.environ['PATH'] = '/home/best/Projects/jit/bin:' + os.environ['PATH']
        if TESTING_DIR.exists():
            shutil.rmtree(TESTING_DIR)
        shutil.copytree(TEMPLATES_DIR, TESTING_DIR)
        os.chdir(TESTING_DIR)

    def _assert_object_matches(self, expected_hash):
        """Helper method to verify jit and git objects match"""
        test_file_hash_path = Path(expected_hash)
        jit_blob_path = Path(".jit/") / test_file_hash_path
        git_blob_path = Path(".git/") / test_file_hash_path
        
        self.assertTrue(jit_blob_path.is_file())
        self.assertTrue(git_blob_path.is_file())
        
        with open(jit_blob_path, 'rb') as f:
            jit_obj = f.read()
        with open(git_blob_path, 'rb') as f:
            git_obj = f.read()
        
        self.assertEqual(jit_obj, git_obj)

    def _add_and_assert_blobs_match(self, filepath, expected_hash):
        """Helper method to jit add and git add then verify both blobs match."""
        subprocess.run(["jit", "add", filepath], stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", filepath], stdout=subprocess.DEVNULL)
        self._assert_object_matches(expected_hash)

    def test0Init(self):
        _run_on_terminal("git init")
        p = Path(".git/HEAD")
        self.assertTrue(p.exists() and p.is_file())
        p = Path(".git/refs/heads")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".git/refs/tags")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".git/branches")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".git/objects")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".git/objects/pack")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".git/objects/info")
        self.assertTrue(p.exists() and p.is_dir())

        _run_on_terminal("jit init")
        p = Path(".jit/HEAD")
        self.assertTrue(p.exists() and p.is_file())
        p = Path(".jit/refs/heads")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".jit/refs/tags")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".jit/branches")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".jit/objects")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".jit/objects/pack")
        self.assertTrue(p.exists() and p.is_dir())
        p = Path(".jit/objects/info")
        self.assertTrue(p.exists() and p.is_dir())
    
    def test1Blobs(self):
        _run_on_terminal("git init")
        _run_on_terminal("jit init")
        self._add_and_assert_blobs_match(
            "d1/d2/testfile-two-deep.py",
            "objects/ea/6e4e80d8bedd6b3debe844b96f09651421f360"
        )
        # Test again to ensure idempotency
        self._add_and_assert_blobs_match(
            "d1/d2/testfile-two-deep.py",
            "objects/ea/6e4e80d8bedd6b3debe844b96f09651421f360"
        )
        self._add_and_assert_blobs_match(
            "README.md",
            "objects/c6/20724c9d894a8c6639bbb4bda372a8d0959763"
        )
        self._add_and_assert_blobs_match(
            "testfile1.txt",
            "objects/92/8048420fadad905124eb575da12f40f42cf6ef"
        )

    def test2Trees(self):
        self.test1Blobs()  # lazy add files
        _write_jit_config()
        _run_on_terminal("jit commit -m test")
        _run_on_terminal("git commit -m test")
        self._assert_object_matches('objects/4b/494caac435467b8054709119cb638c0b3f34ed')
        self._assert_object_matches('objects/e7/00756d8acfb8fe1fa4b4bdcbe862b35b1ff672')
        self._assert_object_matches('objects/02/ad9538b3e20b55b791281af0a2c7340179e455')

    def test3Commits(self):
        _run_on_terminal("git init")
        _run_on_terminal("jit init")
        _write_jit_config()

        _run_on_terminal("git add README.md")
        _run_on_terminal("jit add README.md")

        _run_on_terminal("git commit -m batman")
        _run_on_terminal("jit commit -m batman")

        _run_on_terminal("git add testfile1.txt")
        _run_on_terminal("jit add testfile1.txt")

        _run_on_terminal("git commit -m test")
        _run_on_terminal("jit commit -m test")

        git_commit_hash = _get_commit_hash_from_head(Path('.git/HEAD'))
        jit_commit_hash = _get_commit_hash_from_head(Path('.jit/HEAD'))

        git_commit_contents = _commit_contents_from_hash('.git/objects', git_commit_hash)
        jit_commit_contents = _commit_contents_from_hash('.jit/objects', jit_commit_hash)

        # test trees
        self.assertIsNotNone(git_commit_contents.get('tree'))
        self.assertIsNotNone(jit_commit_contents.get('tree'))
        self.assertEqual(git_commit_contents.get('tree'),
                         jit_commit_contents.get('tree'))

        # test current commit has a parent
        self.assertIsNotNone(git_commit_contents.get('parents'))
        self.assertIsNotNone(jit_commit_contents.get('parents'))
        self.assertEqual(len(git_commit_contents.get('parents')), 1)
        self.assertEqual(len(jit_commit_contents.get('parents')), 1)

        # go to parent (first commit)
        git_commit_hash = git_commit_contents.get('parents')[0]
        jit_commit_hash = jit_commit_contents.get('parents')[0]
        git_commit_contents = _commit_contents_from_hash('.git/objects', git_commit_hash)
        jit_commit_contents = _commit_contents_from_hash('.jit/objects', jit_commit_hash)

        # test first commit has a tree ref
        self.assertIsNotNone(git_commit_contents.get('tree'))
        self.assertIsNotNone(jit_commit_contents.get('tree'))
        self.assertEqual(git_commit_contents.get('tree'),
                         jit_commit_contents.get('tree'))

        # assert first commit has no parent
        self.assertIsNone(git_commit_contents.get('parents'))
        self.assertIsNone(jit_commit_contents.get('parents'))

    def tearDown(self):
        os.chdir('../')
        shutil.rmtree('.testspace')


def _run_on_terminal(cmd: str):
    args = cmd.split(" ")
    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def _write_jit_config():
    with open('.jit/config', 'w') as f:
        f.write(
"""
[user]
    name="George P. Burdell"
    email="george.p.burdell@gatech.edu"

"""
)


def _get_commit_hash_from_head(head_path: Path) -> str:
    with open(head_path, 'r') as f:
        buf = f.read()
    head_branch = buf.split(' ')[1].strip()
    head_path = head_path.parent / Path (head_branch)
    with open(head_path) as f:
        buf = f.read()
    return str(buf)


def _commit_contents_from_hash(folder: str, hashkey: str) -> dict[str, str]:
    commit_contents = {}
    obj_path = Path(folder)/Path(hashkey[:2])/Path(hashkey[2:].strip())
    with open(obj_path, 'rb') as f:
        buf = f.read()
    commit_buf = zlib.decompress(buf)
    commit_buf = commit_buf.split(b'\0')[1]
    commit_lines = commit_buf.decode('utf-8').split('\n')
    for i, line in enumerate(commit_lines):
        if 'tree ' in line[:5]:
            hashkey = str(line).split(' ')[1]
            if commit_contents.get('tree') is None:
                commit_contents['tree'] = str(line).split(' ')[1]
            else:
                raise Exception(f'two trees in {folder} {hashkey}')
        if 'parent ' in line[:7]:
            hashkey = str(line).split(' ')[1]
            if commit_contents.get('parents') is None:
                commit_contents['parents'] = [hashkey]
            else:
                commit_contents['parents'].append(hashkey)
    return commit_contents


if __name__ == '__main__':
    unittest.main()

