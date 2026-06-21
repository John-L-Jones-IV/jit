#!/usr/bin/env -S uv run
import json
import os
from pathlib import Path

import odb as odb
from jitcoreutils import get_jit_repo_dir, git_file_mode


def add_file_to_index(index: dict[str, dict], jitfilepath: Path):
    jit_repo_dir = get_jit_repo_dir()
    if not jit_repo_dir:
        print("not a jit repo")
        return
    fullpath = jit_repo_dir / jitfilepath
    index[str(jitfilepath)] = make_index_entry_from_filepath(fullpath)
    save_index(index)


def rm_file_from_index(index: dict[str, dict], jitfilepath: Path):
    try:
        del index[str(jitfilepath)]
    except KeyError:
        print(f"{jitfilepath} was not in index and cannot be deleted.")
    save_index(index)


def make_index_entry_from_filepath(filepath: Path):
    stat = os.stat(filepath)
    return {'hashkey': odb.get_file_hash_key(filepath),
            'size': stat.st_size, 
            'ctime': stat.st_ctime, 
            'mtime': stat.st_mtime,
            'uid': stat.st_uid,
            'gid': stat.st_gid,
            'mode': git_file_mode(stat.st_mode),}


def load_index() -> dict[str, dict]:
    jit_repo_dir = get_jit_repo_dir()
    if not jit_repo_dir:
        raise Exception("not a jit repo")
    index_path = jit_repo_dir / Path('.jit/index.json')
    if not index_path.exists() or not index_path.is_file():
        print("No jit index found. " 
              "Returning new empty index dict. " 
              "Saving empty index file.")
        return dict()
    try:
        with open(index_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"'{index_path}' is not a valid JSON file. Error: {e}")
        print("returning new index")
        return dict()

def save_index(index: dict[str, dict]):
    jit_repo_dir = get_jit_repo_dir()
    if not jit_repo_dir:
        raise Exception("not a jit repo")
    index_path = jit_repo_dir / Path('.jit/index.json')
    sorted_index = {k: index[k] for k in sorted(index.keys())}
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(sorted_index))


def pprint_index(index: dict[str, dict]):
    import pprint
    print(pprint.pformat(index, indent=2))


def main():
    index = load_index()
    pprint_index(index)


if __name__ == '__main__':
    main()

