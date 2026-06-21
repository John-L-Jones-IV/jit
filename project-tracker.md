# Roadmap
1. core ui commands:
    - [x] init
    - [x] add
    - [x] status
    - [x] commit
    - [ ] branch
1. plumbing commands:
    - [ ] cat-file
    - [ ] init-db
    - [ ] update-cache
    - [ ] show diff
    - [ ] write-tree
    - [ ] read-tree
    - [ ] commit-tree
    - [ ] read-cache

## Extended Roadmap
1. shattered hash collision attack case-study
1. TDD for expanded core ui commands (scope below)
    - [ ] test suite for expanded core ui commands
    - [ ] develop expanded core ui
1. expanded core ui commands:
    - [ ] config
    - [ ] log
    - [ ] stash
    - [ ] restore

## Beyond the Roadmap
1. commands:
    - [ ] rebase
    - [ ] merge
    - [ ] pull
    - [ ] push

## Dreams and Spinoffs?
1. Undo tree
1. jj
1. Case study of historical scm's (svn, hg, etc.)
1. git-like for non-text files? such as mechanical CAD?

# thoughts
* why bother build index testing for the .json version?
    json is a prototype.
    convert to git comptabile index and build test suite

## Issues Backlog
1.  can commits be made while in detached HEAD state? aka no branch label?

## overall
1.  remove regex.
1.  jitAdd compares system st.mode vs git normalized in index
1.  jit's objects files are not write protected like git's

## tools
1.   readGitIndex.py doesn't display to files in the same directory...?

## jit status
1.  Report untracked files by directory i.e. be concise as possible by default
1.  jit status report not in lexiconical order

## jit add
1.  Should save index to /tmp file, verify, then update/move to .jit folder
    use os.rename() to copy index from /tmp/ file
1.  Possible to get full path saved into index example /home/best/Projects/jit/init_sandbox/README.md
1.  Use relative paths to jit_repo_dir when adding file to index

# ideas

# questions
