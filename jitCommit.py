#!/usr/bin/env -S uv run
"""
jitCommit.py - Record changes to the repository
"""
import os
import sys
import subprocess
import time
import zlib
from pathlib import Path
from typing import Optional

import odb as odb
import dircache as dircache

from jitConfig import get_jit_config
from jitcoreutils import get_jit_repo_dir


def main(args) -> int:
    return commit(args)


def commit(args) -> int:
    # Check if in jit repo and there are changes to commit
    jit_repo_dir: Optional[Path] = get_jit_repo_dir()
    if jit_repo_dir is None:
        print(f'No jit repo identifed in {Path.cwd()} or parent directories')
        return 1
    index: dict[str, dict[str, str]] = dircache.load_index()
    if index == {}:
        print('Nothing staged in index to commit')
        return 2

    # Verify config
    config = get_jit_config(jit_repo_dir)
    user = config.get('user')
    if user is None:
        print('No user section found in .jitconfig. Exiting')
        return 3
    if user.get('name') is None:
        print('No user.name in jit config found')
        return 4
    if user.get('email') is None:
        print('No user.email in jit config found')
        return 5

    # Write index to database
    idx_thashkey = odb.write_index_to_odb(index)
    if idx_thashkey == (repo_thashkey:=get_head_thashkey(jit_repo_dir)):  # no changes to directory
        if repo_thashkey is not None:
            print('No changes since last commit')
            return 6

    # Get commit message
    if args[0] == '-m':
        if args[1]:
            commit_comment = args[1]
        else:
            print('You must enter a commit message')
            return 7
    else:
        commit_comment = open_editor(jit_repo_dir)
        commit_comment = remove_comments(commit_comment)
        if commit_comment == '':
            print('You must enter a commit message')
            return 7

    # commit parents
    with open(jit_repo_dir / Path('.jit/HEAD'), 'r') as f:
        HEAD = f.read()
    # refs = HEAD.replace('ref: ', '')
    # refs = refs.rstrip('\n')
    refs = HEAD.split(' ')[1].strip()
    branch = refs.split('/')[-1]
    ref_path = jit_repo_dir / Path('.jit') / Path(refs)
    if ref_path.is_file(): 
       with open(ref_path, 'r') as f:
           commit_parent = f.read().rstrip('\n')
       commit_parents = [commit_parent]
    else:
       commit_parents = None

    # Write commit object to database
    author_name = config['user']['name']
    author_email = config['user']['email']
    committer_name = config['user']['name']
    committer_email = config['user']['email']
    utc_time = int(time.time())
    tz_offset = time.localtime().tm_gmtoff/3600
    tz_offset_s = f"{tz_offset:03.0f}{(tz_offset%1)*60:02.0f}"
    commit_contents = f'tree {idx_thashkey}\n'

    if commit_parents:
        for parent in commit_parents:
            commit_contents += f'parent {parent}\n'

    commit_contents += (
            f'author {author_name} <{author_email}> {utc_time} {tz_offset_s}\n'
            f'committer {committer_name} <{committer_email}> {utc_time} {tz_offset_s}\n\n'
            f'{commit_comment}\n'
                  )
    commit_buf = f"commit {len(commit_contents)}\0".encode('utf-8') + commit_contents.encode('utf-8')
    commit_hash = odb.buf_to_odb(commit_buf)

    # update refs
    path = jit_repo_dir / Path(f'.jit/refs/heads/{branch}')
    os.makedirs(path.parent, exist_ok=True)
    print(f'refs/heads/{branch} path: {path}')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(commit_hash)
        f.write('\n')
    return 0

def get_head_thashkey2(jit_repo_dir: Path) -> Optional[str]:
    head_file_path = Path(jit_repo_dir) / Path('.jit/HEAD')
    print(head_file_path)

def get_head_thashkey(jit_repo_dir: Path) -> Optional[str]:
    head = jit_repo_dir / Path('.jit/HEAD')
    with open(head, 'r', encoding='utf-8') as f:
        ref = f.read().strip()
    if ref[:5] != 'ref: ' and is_hash_str(ref):
        head_commit_id = ref  # detached head state
    elif ('ref: ' in ref) and len(ref.split(':')) == 2:
        refpath = jit_repo_dir / Path('.jit') / Path(ref.split(' ')[1].strip())
        if not refpath.is_file():
            return None
        with open(refpath, 'r', encoding='utf-8') as f:
            head_commit_id = f.read().strip()
    else:
        raise Exception("HEAD in an unknown state")
    hcid = head_commit_id
    head_commit_path = jit_repo_dir / Path(f'.jit/objects/{hcid[:2]}/{hcid[2:]}')
    with open(head_commit_path, 'rb') as f:
        commit_contents_deflated = f.read()
    commit_contents = zlib.decompress(commit_contents_deflated)
    i = commit_contents.index(b'\00')
    assert commit_contents[i+1:i+6] == b'tree '
    return commit_contents[i+6:i+46].decode()


def is_hash_str(s: str) -> bool:
    SHA1LEN = 40
    try:
        int(s, 16)
        return len(s) == SHA1LEN
    except ValueError:
        return False


_template_commit_comments = (
"""
# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
"""
)


def open_editor(jit_repo_dir, initial_content=_template_commit_comments):
    # Get the user's preferred editor
    commit_file = jit_repo_dir / Path('.jit/COMMIT_EDITMSG')
    config = get_jit_config(jit_repo_dir)
    if config == {} or config is None:
        raise Exception("No jit config file found for commit user information")
    core = config.get('core')
    if core is not None:
        editor = core.get('editor')
    else:
        editor = None
    if not editor:
        editor = os.environ.get('EDITOR', 'vi')  # fallback to vi
    with open(commit_file, 'w', encoding='utf-8') as f:
        f.write(initial_content)
        f.flush()
        f.seek(0)
    subprocess.call([editor, commit_file])
    with open(commit_file, 'r') as f:
        content = f.read()
    return content


def remove_comments(s: str):
    buf = ''
    for line in s.split('\n'):
        if not len(line.lstrip()):
            continue
        if line.lstrip()[0] == '#':
            continue
        buf += line
    return buf


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)

