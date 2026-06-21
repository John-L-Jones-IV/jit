#!/usr/bin/env -S uv run
import sys
import time
from dataclasses import dataclass


@dataclass
class GitIndexEntry:
    changed_time_s: str
    changed_time_ns: bytes
    modified_time_s: str
    modified_time_ns: bytes
    stat_dev: bytes
    stat_ino: bytes
    mode: bytes
    obj_type: int
    unix_permissions: int
    uid: bytes
    gid: bytes
    file_size: bytes
    file_hash: bytes
    file_name: bytes
    flags: bytes
    extended_flags: bytes

    def __repr__(self):
        uid = int.from_bytes(self.uid) & 0xF
        gid = int.from_bytes(self.gid) & 0xF
        return (f"{self.file_hash.hex()} "
                f"{str(self.file_name)}\n"
                f"file_size: {int.from_bytes(self.file_size)}\n"
                f"mode: 0x{int.from_bytes(self.mode):X} "
                f"obj_type: {decode_obj_type(self.obj_type)} "
                f"unix_permissions: "
                f"{pretty_unix_permissions(self.unix_permissions)} \n"
                f"ctime: {self.changed_time_s} "
                f"{int.from_bytes(self.changed_time_ns)}\n"
                f"mtime: {self.modified_time_s} "
                f"{int.from_bytes(self.modified_time_ns)}\n"
                f"dev: {int.from_bytes(self.stat_dev)}, "
                f"ino: {int.from_bytes(self.stat_ino)}, "
                f"uid: {uid:b} gid: {gid:b} "
                f"flags: {int.from_bytes(self.flags):b}\n"
                )


def main():
    if len(sys.argv) < 2:
        print('usage:')
        print('readGitIndex.py <git-index-filepath>')
        return
    index = index_from_file(sys.argv[1])
    print_index(index)


def decode_obj_type(obj_type) -> str:
    match int(obj_type):
        case 0b1000:
            return 'Regular File'
        case 0b1010:
            return 'Symbolic Link'
        case 0b1110:
            return 'Git Link'
    return 'ERROR'


def pretty_unix_permissions(permissions: int) -> str:
    i = int(permissions)
    other = i & 0x7
    user = (i >> 3) & 0x7
    root = (i >> 6) & 0x7
    return f"{root:X}{user:X}{other:X}"


def index_from_file(filepath):
    index_entries = {}
    with open(filepath, 'rb') as f:
        # header 
        signature = f.read(4)
        version = f.read(4)
        num_entries = f.read(4)

        # entries
        for i in range(int.from_bytes(num_entries)):
            ctime_s: str = time.ctime(int.from_bytes(f.read(4)))
            ctime_ns = f.read(4)
            mtime_s: str = time.ctime(int.from_bytes(f.read(4)))
            mtime_ns = f.read(4)
            dev = f.read(4)
            ino = f.read(4)
            mode = f.read(4)
            obj_type = (int.from_bytes(mode) >> 12) & 0xF
            unix_permissions = int.from_bytes(mode) & 0x3FF
            uid = f.read(4)
            gid = f.read(4)
            file_size = f.read(4)
            file_hash = f.read(20)
            flags = f.read(2)
            # assume_valid = bool((int.from_bytes(flags) & 0x80) >> 7)
            extended_version = bool((int.from_bytes(flags) & 0x40) >> 6)
            file_name_len = int.from_bytes(flags) & 0xFFF
            extended_flags = bytes()
            pack = [extended_version, extended_flags]
            file_name = get_file_name(f, file_name_len, pack)
            index_entries[file_hash.hex()] = GitIndexEntry(
                    ctime_s,
                    ctime_ns,
                    mtime_s,
                    mtime_ns,
                    dev,
                    ino,
                    mode,
                    obj_type,
                    unix_permissions,
                    uid,
                    gid,
                    file_size,
                    file_hash,
                    file_name,
                    flags,
                    extended_flags
                    )
    return { 'signature' : signature,
             'git_version' : version,
             'num_entries' : num_entries,
             'entries' : index_entries }


def get_file_name(f, flen, pack):
    extended_version, _ = pack[0], pack[1]
    MAX_FILE_NAME_LEN = 255
    buf = bytes()
    while ((c := f.read(1)) != b'\00'):
        buf += c
        if len(buf) > MAX_FILE_NAME_LEN or len(buf) > flen:
            raise Exception("Filename buffer overflow error")

    if extended_version:
        pack[1] = f.read(2)  # extended_flags

    # re-align to next 8-byte increment, excluding header
    HEADER_OFFSET = 4
    padding = (8 - (f.tell() - HEADER_OFFSET)) % 8
    if padding:
        f.read(padding)
    return buf


def print_index(index):
    print("="*80)
    print("GIT INDEX HEADER", end='\t')
    print(f"signature: {index['signature']}", end='\t')
    print(f"version: {int.from_bytes(index['git_version'])}", end='\t')
    print(f"num_entries: {int.from_bytes(index['num_entries'])}")
    for key, val in index['entries'].items():
        print("="*80)
        print(f"{val}")


if __name__ == '__main__':
    main()

