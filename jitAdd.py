#!/usr/bin/env -S uv run
"""
jitAdd.py - Add file contents to the staging area
"""
import os
import sys
from pathlib import Path
from typing import Optional

import dircache as dirc
import odb
from jitcoreutils import get_jit_repo_dir, git_file_mode

flags = ['-v']


def main(args):
    """
    add list of file names (args) to the staging area.
    """
    if not args:
        print('Usage:\n./jitAdd.py <files>')
        return 1

    jit_repo_dir: Optional[Path] = get_jit_repo_dir()
    if not jit_repo_dir:
        print(f'Not a jit repository -'
              f' .jit/ not found in {os.getcwd()} or parent folders.')
        return 2

    files_added = []
    cwd = Path.cwd()
    for file in [cwd/Path(x).resolve() for x in args if x not in flags]:
        if jit_repo_dir not in file.parents:
            raise Exception(f'Error: file: {file} is not in jit repo: {jit_repo_dir}')
        elif file.is_file():
            jit_add(file)
            files_added.append(file)
        else:
            print(f'{file.relative_to(cwd, walk_up=True)} not found')

    if files_added and '-v' in args:
        for file in files_added:
            print(f'Added {file}')

    return 0 if files_added else 3


def jit_add(filepath: Path):
    """
    load index into memory from file
    add filepath to index
    blob file and save to .jit/objects
    save updated index to file system
    """
    jit_repo_dir: Optional[Path] = get_jit_repo_dir()
    assert isinstance(jit_repo_dir, Path)
    index: dict[str, dict] = dirc.load_index()
    jitfilepath: Path = filepath.resolve().relative_to(jit_repo_dir)
    ientry: Optional[dict[str, str]] = index.get(str(jitfilepath))
    if ientry and is_unchanged_from_index(ientry, jitfilepath):
        return  # file is already staged, nothing to do here
    dirc.add_file_to_index(index, jitfilepath)
    odb.save_file_to_odb(filepath)


def is_unchanged_from_index(index_entry: dict, jitfilepath: Path) -> bool:
    """
    check size and stat data to optimize for speed when something like
    jit add .
    is executed in a large repo
    """
    jit_repo_dir = get_jit_repo_dir()
    if not jit_repo_dir:
        raise Exception('not a jit repo')
    fullpath = jit_repo_dir / jitfilepath
    st = os.stat(fullpath)
    ie_size = index_entry.get('size')
    if st.st_size != ie_size:
        return False
    ie_uid = index_entry.get('uid')
    ie_gid = index_entry.get('gid')
    ie_mode = index_entry.get('mode')
    mode = git_file_mode(st.st_mode)
    if (st.st_uid != ie_uid) or (st.st_gid != ie_gid) or (ie_mode != mode):
        return False
    ie_ctime = index_entry.get('ctime')
    ie_mtime = index_entry.get('mtime')
    if ie_ctime == st.st_ctime and ie_mtime == st.st_mtime:
        return True
    ie_hashkey = index_entry.get('hashkey')
    return odb.is_hash_eq(odb.get_file_hash_key(jitfilepath), ie_hashkey)


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    main(args)

