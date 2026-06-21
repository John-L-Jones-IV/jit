# jit
Jit - ~~Janky git.~~ A version control system writen in python that has byte-for-byte compatability with git's hash-index object data base.

This is an educational project for understanding the internals of git.

"If you know the internals of git you have intuition for what git commands must exist and how to use them" -Something that might have been said at a Tech Talk once.

## How to setup

git clone

source addJitToPath.sh
Note: this will need to be ran on every new terminal. Jit does not intend to crowd your working path.

jit
Usage: jit <command> [<args>]

Available commands:
  init       Initialize a new jit repository
  add        Add file contents to the staging area
  commit     Record changes to the repository
  status     Show the working tree status


Happy hacking!


## Code Testing
Just like real git, a test suite is in the 't/' directory. If your system has a bash interpretor you can also use status.sh

mypy:
Success: no issues found in 10 source files

ruff check:
All checks passed!

unit tests:
test01GitHarness (test_object_compatability.TestHarness.test01GitHarness) ... ok
test02JitHarness (test_object_compatability.TestHarness.test02JitHarness) ... ok
test0Init (test_object_compatability.TestObjectCompatability.test0Init) ... ok
test1Blobs (test_object_compatability.TestObjectCompatability.test1Blobs) ... ok
test2Trees (test_object_compatability.TestObjectCompatability.test2Trees) ... ok
test3Commit (test_object_compatability.TestObjectCompatability.test3Commit) ... ok
test0 (test_relative_paths.TestRelativeDirectories.test0) ... ok
test1 (test_relative_paths.TestRelativeDirectories.test1) ... ok

----------------------------------------------------------------------
Ran 8 tests in 1.416s

OK

