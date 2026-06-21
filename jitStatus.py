#!/usr/bin/env -S uv run
import os
import json
import zlib
from pathlib import Path
from typing import Optional

import odb as odb
from jitcoreutils import get_jit_repo_dir


def main(args):
    cwd = Path(os.getcwd())
    ready_for_commit = []
    not_staged_for_commit = []
    untracked = []

    jit_repo_dir: Optional[Path] = get_jit_repo_dir()
    if jit_repo_dir is None:
        print("fatal: not a jit repository")
        return

    # HEAD
    head = str(jit_repo_dir / Path('.jit/HEAD'))
    with open(head, 'r', encoding='utf-8') as f:
        ref = f.read()
        ref = ref.strip()
    if ref[:5] != 'ref: ' and is_hash_str(ref):
        print("You are in 'detached HEAD' state at {ref}")
    elif 'ref: ' in ref and len(ref.split(':')) == 2:
        refpath = Path(ref.split(' ')[1].strip())
        branch = refpath.name.split('/')[-1]
        print(f"On branch {branch}")
        if not (jit_repo_dir/Path('.jit')/refpath).is_file():
            print("\nNo commits yet\n")
    else:
        raise Exception("in an unknown HEAD state")

    # index
    index_path = Path(jit_repo_dir / Path('.jit/index.json'))
    if not index_path.is_file():
        index: dict[str, dict[str, str]] = dict()
    else:
        try:
            with open(str(index_path), 'r') as f:
                index = json.load(f)
        except json.JSONDecodeError as e:
            print("Failed to decode index JSON:", e)
            raise e

    # compare index to working directory
    for file in jit_repo_dir.rglob('*'):
        jitpath = file.relative_to(jit_repo_dir)
        if '.git' in jitpath.parts or '.jit' in jitpath.parts:
            continue  # not tracking internals
        ie = index.get(str(jitpath))
        if ie is None:
            if file.is_dir():
                untracked.append(file.relative_to(cwd, walk_up=True))
            else:
                untracked.append(file.relative_to(cwd, walk_up=True))
            continue
        if ie['size'] != os.stat(file).st_size:  # modified
            not_staged_for_commit.append(file.relative_to(cwd, walk_up=True))
            continue
        if odb.get_file_hash_key(file) != ie['hashkey']:
            not_staged_for_commit.append(file.relative_to(cwd, walk_up=True))

    # compare index to HEAD
    for k, v in index.items():
        if not in_head(jit_repo_dir, head, v['hashkey']):
            filepath = jit_repo_dir / Path(k)
            ready_for_commit.append(filepath.relative_to(cwd, walk_up=True))

    print_status(ready_for_commit, not_staged_for_commit, untracked)


def in_head(jit_repo_dir: Path, head: str, filehashkey: str):
    with open(head, 'r', encoding='utf-8') as f:
        ref = f.read().strip()
    if ref[:5] != 'ref: ' and is_hash_str(ref):  # detached head
        head_commit = ref
    else:
        ref_path = jit_repo_dir / Path('.jit')/Path(ref.split(':')[1].strip())
        if not ref_path.is_file():  # no previous commits
            return False
        with open(ref_path, 'r', encoding='utf-8') as f:
            head_commit = f.read().strip()
    return file_found_in_trees(jit_repo_dir, head_commit, filehashkey)
    

def file_found_in_trees(jit_repo_dir: Path, treeish: str, filehashkey: str) -> bool:
    treeish_path = jit_repo_dir / Path(f'.jit/objects/{treeish[:2]}/{treeish[2:]}')
    with open(treeish_path, 'rb') as f:
        b = f.read()
    contents0 = zlib.decompress(b)
    header_end_i = contents0.index(b'\00')+1
    header = contents0[:header_end_i-1].split(b' ')[0]
    contents1 = contents0[header_end_i:]
    if header == b'commit':
        txtl = contents1.decode('utf-8').split('\n')
        for line in txtl:
            if line[:4] == 'tree':
                treehash = line[5:]
                if file_found_in_trees(jit_repo_dir, treehash, filehashkey):
                    return True
            if line[:6] == 'author':
                break
    elif header == b'tree':
        i = 0
        while i < len(contents1) - 20:
            entry_hash_i = contents1.index(b'\00', i)
            mode = contents1[i:entry_hash_i].split(b' ')[0]
            if mode == b'40000':  # tree
                tree_hash = contents1[entry_hash_i+1:entry_hash_i+21]
                if file_found_in_trees(jit_repo_dir, tree_hash.hex(), filehashkey):
                    return True
                i = entry_hash_i+21
            elif mode == b'100644' or mode == b'100755':  # file
                blob_hash = contents1[entry_hash_i+1:entry_hash_i+21]
                if blob_hash.hex() == filehashkey:
                    return True
                i = entry_hash_i + 21
            else:
                raise Exception(f"unexpected object in tree {treeish}")
    else:
        raise Exception(f"unexpected object {treeish}")
    return False


def print_status(ready_for_commit, not_staged_for_commit, untracked):
    CLEAR_CLR = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    
    if len(ready_for_commit):
        print("Changes to be committed:")
        print('  (use "jit rm --cached <file>..." to unstage)')
        for file in ready_for_commit:
            print(f"\t{GREEN}{file}{CLEAR_CLR}")
        print()
    
    if len(not_staged_for_commit):
        print("Changes not staged for commit:")
        for file in not_staged_for_commit:
            print(f"\t{RED}{file}{CLEAR_CLR}")
        print()
    
    if len(untracked):
        print("Untracked files:")
        print('  (use "jit add <file>..." to include what will be committed)')
        for file in untracked:
            print(f"\t{RED}{file}{CLEAR_CLR}")
        print()


def is_hash_str(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def pretty_unix_permissions(permissions: int) -> str:
    i = int(permissions)
    other = i & 0x7
    user = (i >> 3) & 0x7
    root = (i >> 6) & 0x7 
    return f"{root:X}{user:X}{other:X}"


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    main(args)

