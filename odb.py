#!/usr/bin/env -S uv run
import hashlib
import os
import sys
import zlib
from pathlib import Path

# import dircache
from jitcoreutils import get_jit_repo_dir


OBD_JIT_PATH = Path('.jit/objects')

SHA1LEN = 40  # 20 bytes, 40 hex chars.
GIT_OBJ_PATH_LEN = 54


class HashKeyCollisionError(FileExistsError):
    def __init__(self):
        super().__init__()


def num_commits_in_odb():
    cnt = 0
    for file in OBD_JIT_PATH.rglob('*'):
        obj = inflate_obj(file)
        if is_commit(obj):
            cnt += 1
    return cnt


def is_commit(obj):
    return 'commit' == obj[:6] 


def save_file_to_odb(filepath: Path):
    jit_repo_dir = get_jit_repo_dir()
    blob = file_to_blob(filepath)
    hashkey = get_hash_key(blob)
    deflated_blob = compress(blob)
    target_path = jit_repo_dir / odb_path(hashkey)
    if target_path.exists():
        print(f'log - {hashkey} already in database')
        return
    os.makedirs(target_path.parent, exist_ok=True)
    with open(target_path,'wb') as f:
        f.write(deflated_blob)


def buf_to_odb(obj: bytes):
    jit_repo_dir = get_jit_repo_dir()
    hashkey = get_hash_key(obj)
    deflated_obj = compress(obj)
    target_path = jit_repo_dir / odb_path(hashkey)
    if target_path.exists():
        print(f'log - {hashkey} already in database')
        return
    os.makedirs(target_path.parent, exist_ok=True)
    with open(target_path,'wb') as f:
        f.write(deflated_obj)
    return hashkey


def is_hash_eq(hash1, hash2):
    return str(hash1) == str(hash2)


def file_to_blob(jitfilepath: Path):
    jit_repo_dir = get_jit_repo_dir()
    if not jit_repo_dir:
        print("not a jit repo")
        return
    filepath = jit_repo_dir / jitfilepath
    with open(filepath, 'rb') as f:
        file_buf = f.read()
    byte_count = len(file_buf)
    blob_header = b"blob " + bytes(f"{byte_count}", encoding='utf-8') + b"\x00"
    blob_buf = blob_header + file_buf
    return blob_buf


def compress(jit_obj):
    return zlib.compress(jit_obj, level=zlib.Z_BEST_SPEED)


def inflate_obj(filename: Path):
    with open(filename, 'rb') as f:
        compressed_contents = f.read()
    decompressed_contents = zlib.decompress(compressed_contents)
    return decompressed_contents


def get_hash_key(jitobject) -> str:
    h = hashlib.new('sha1')
    h.update(jitobject)
    return h.hexdigest()


def get_file_hash_key(filepath: Path):
    return get_hash_key(file_to_blob(filepath))


def to_path(filepath: str):
    if '.git/objects/' in filepath and len(filepath) == GIT_OBJ_PATH_LEN:
        return filepath
    if len(filepath) == SHA1LEN:
        return "".join(['.git/objects/', filepath[:2], '/', filepath[2:]])
    else:
        return None


def main():
    if (num_args := len(sys.argv) - 1) != 1:
        print("Usage:\nfile2jitblob <file>")
        print(f"ERROR: {num_args} args != 1 arg. Use one and only one file.")
        return

    filepath = Path(sys.argv[1])
    print(inflate_obj(filepath))


def odb_path(hash_key):
    # split hashkey at first two chars to bust inodes
    return OBD_JIT_PATH / Path(hash_key[:2] + '/' + hash_key[2:])


def write_index_to_odb(index):
    tree: dict = {'type': 'tree',
            'mode': '040000',
            'hashkey': None,
            'children': {},}
    for name, d in index.items():
        filepath = Path(name)
        fd = {'name': filepath.name,
              'type': 'blob',
              'hashkey': d['hashkey'],
              'mode': d['mode'],
              'children': {},}
        add_to_tree(tree, filepath, fd)

    hashkey = write_tree_to_odb(tree)
    return hashkey


def add_to_tree(tree, filepath, d):
    # update children 
    attach_point = tree
    for p in filepath.parents[::-1][1:]:
        if attach_point.get('children').get(p.name) is None:
            dt = {'name': p.name,
                  'type': 'tree',
                  'mode': '040000',
                  'hashkey': None,
                  'children': {},}
            attach_point['children'][p.name] = dt
            attach_point = dt
        else:
            attach_point = attach_point.get('children').get(p.name)

    # add end node
    attach_point['children'][filepath.name] = d


def write_tree_to_odb(tree) -> str:
    tree['hashkey'] = _write_tree_to_odb_helper(tree)
    return tree['hashkey']


def _write_tree_to_odb_helper(tree) -> str:
    lines = []
    for ck, cv in tree['children'].items():
        if cv['type'] == 'blob':
            lines.append([cv['mode'], cv['type'], cv['hashkey'], cv['name']])
        else:
            hashkey = _write_tree_to_odb_helper(cv)
            tree['children'][ck]['hashkey'] = hashkey
            lines.append([cv['mode'], cv['type'], hashkey, cv['name']+'/'])

    sorted_lines =sorted(lines, key=lambda x: x[3])
    obj = b''

    for line in sorted_lines:
        if line[1] == 'tree' and line[3][-1] == '/':
            name = line[3][:-1]
            permissions = '40000'
            hashkey = line[2]
            obj += f"40000 {name}\0".encode('utf-8')
            obj += bytes.fromhex(hashkey)
        else:
            permissions = line[0]
            name = line[3]
            hashkey = line[2]
            obj += f"{permissions} {name}\0".encode('utf-8')
            obj += bytes.fromhex(hashkey)

    obj_buf = f"tree {len(obj)}\0".encode('utf-8') + obj
    hash_key = get_hash_key(obj_buf)
    buf_to_odb(obj_buf)
    return hash_key
if __name__ == '__main__':
    print(inflate_obj(Path(sys.argv[1])))

